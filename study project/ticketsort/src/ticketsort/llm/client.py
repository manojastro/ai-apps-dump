"""One adapter for all LLM providers. Mock works now, real providers plug in later."""

from __future__ import annotations

import os
import time

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from ticketsort.config import Settings
from ticketsort.domain.models import Category, Extraction, LLMMeta, Service, TicketIn
from ticketsort.llm.pricing import estimate_cost

PROMPT_V1 = (__import__("pathlib").Path(__file__).parent / "prompts" / "triage_v1.md").read_text()


def _mock_category_service(text: str) -> tuple[Category, Service, str]:
    t = text.lower()
    if "phishing" in t or "clicked" in t or "usb" in t:
        return Category.SECURITY, Service.EMAIL if "mail" in t else Service.UNKNOWN, "phishing"
    if "vpn" in t:
        return Category.NETWORK, Service.VPN, "vpn-down"
    if "wifi" in t or "dns" in t or "switch" in t:
        return Category.NETWORK, Service.NETWORK_CORE, "net-issue"
    if "pos app" in t or "crashes" in t and "pos" in t:
        return Category.SOFTWARE, Service.POS_API, "pos-crash"
    if "payroll" in t:
        return Category.SOFTWARE, Service.PAYROLL_APP, "payroll-error"
    if "pos" in t:
        return Category.HARDWARE, Service.POS_API, "pos-fail"
    if "outlook" in t or "mfa" in t or "password" in t or "sso" in t or "unlock" in t:
        return Category.ACCESS, Service.SSO, "sso-mfa"
    if "mailbox" in t or "emails delayed" in t or "invoices" in t:
        return Category.EMAIL, Service.EMAIL, "email-issue"
    if "orders db" in t or "orders-db" in t or "checkout" in t or "report" in t:
        return Category.DATABASE, Service.ORDERS_DB, "db-slow"
    if "printer" in t or "laptop" in t:
        return Category.HARDWARE, Service.UNKNOWN, "hw-issue"
    if "excel" in t:
        return Category.SOFTWARE, Service.UNKNOWN, "excel-crash"
    return Category.SOFTWARE, Service.UNKNOWN, "general"


def _mock_impact_urgency(text: str) -> tuple[int, int]:
    t = text.lower()
    urgent_now = ("work stopped", "store closed", "all 8", "all 15", "sales impacted", "clicked")
    if any(k in t for k in urgent_now):
        return 1, 1
    if any(k in t for k in ("urgent", "now", "queue", "stuck", "timing out", "40 sec")):
        return 1, 2
    if any(k in t for k in ("slow", "delayed", "disconnect", "mismatch", "failed")):
        return 2, 2
    return 3, 3


class MockLLMClient:
    """Deterministic, free, offline. Used until you pick a real provider."""

    def __init__(self, model: str = "mock-1") -> None:
        self.model = model

    async def extract(self, ticket: TicketIn) -> tuple[Extraction, LLMMeta]:
        start = time.perf_counter()
        text = f"{ticket.short_description} {ticket.description}"
        cat, svc, sub = _mock_category_service(text)
        imp, urg = _mock_impact_urgency(text)
        vague = "nothing works" in text.lower()
        words = text.split()
        summary = " ".join(words[:30])
        conf = 0.4 if vague or svc == Service.UNKNOWN else 0.85
        ext = Extraction(
            category=cat,
            subcategory=sub,
            impact=imp,
            urgency=urg,
            affected_service=svc,
            summary=summary,
            confidence=conf,
            reasoning=f"Keywords point to {cat.value}/{svc.value}; impact {imp} urgency {urg}.",
        )
        ms = int((time.perf_counter() - start) * 1000)
        meta = LLMMeta(
            model=self.model,
            tokens_in=len(words),
            tokens_out=40,
            latency_ms=ms,
            cost_usd=0.0,
        )
        return ext, meta


async def extract_with_mock(ticket: TicketIn) -> tuple[Extraction, LLMMeta]:
    return await MockLLMClient().extract(ticket)


class OpenAILLMClient:
    """Real OpenAI path — needs LLM_API_KEY env. Wired fully in M5, skeleton here."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model = settings.llm_model or "gpt-4o-mini"
        self.api_key = os.getenv("LLM_API_KEY", "")

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=8),
    )
    async def extract(self, ticket: TicketIn) -> tuple[Extraction, LLMMeta]:
        if not self.api_key:
            raise RuntimeError("LLM_API_KEY missing in .env")
        start = time.perf_counter()
        schema = Extraction.model_json_schema()
        wanted = sorted(schema.get("properties", {}).keys())
        user_text = (
            f"Ticket {ticket.ticket_id}: {ticket.short_description}\n"
            f"{ticket.description}\nJSON with keys {wanted}"
        )
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": PROMPT_V1},
                        {"role": "user", "content": user_text},
                    ],
                },
            )
            r.raise_for_status()
            data = r.json()
        content = data["choices"][0]["message"]["content"]
        ext = Extraction.model_validate_json(content)
        usage = data.get("usage", {})
        tin, tout = int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0))
        ms = int((time.perf_counter() - start) * 1000)
        meta = LLMMeta(
            model=self.model,
            tokens_in=tin,
            tokens_out=tout,
            latency_ms=ms,
            cost_usd=estimate_cost(self.model, tin, tout),
        )
        return ext, meta


def get_client(settings: Settings) -> MockLLMClient | OpenAILLMClient:
    if settings.llm_provider == "mock":
        return MockLLMClient()
    if settings.llm_provider == "openai":
        return OpenAILLMClient(settings)
    raise NotImplementedError(f"provider {settings.llm_provider} not wired yet (mock works now)")
