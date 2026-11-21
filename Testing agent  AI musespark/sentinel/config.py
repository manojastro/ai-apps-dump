"""Central settings, budget caps, and allowlists.

Why this file exists before any agent logic: the budget kill switch,
domain allowlist, and production block must be enforced *in code*,
not suggested in a prompt. Every agent imports from here.
"""

from __future__ import annotations

import logging
import os
from urllib.parse import urlparse

from pydantic import BaseModel, Field

logger = logging.getLogger("sentinel.config")

DEFAULT_LLM_TIMEOUT_SECS = 60

# Approximate USD per 1K tokens (input, output). Update when Anthropic reprices.
# Used only for the running-total display + kill switch; billing truth is the API.
MODEL_PRICING_PER_1K: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-5-20250929": (0.003, 0.015),
    "claude-sonnet-4-20250514": (0.003, 0.015),
    "claude-3-5-sonnet-20241022": (0.003, 0.015),
    "claude-3-5-haiku-20241022": (0.0008, 0.004),
}
DEFAULT_PRICING = (0.003, 0.015)

# Irreversible operations the agent must refuse even if a test case asks for them.
BLOCKED_ACTION_PHRASES = [
    "mass delete",
    "mass-delete",
    "delete account",
    "delete all records",
    "modify org-wide settings",
    "org-wide defaults",
    "sharing settings",
    "send email",
    "send mass email",
    "install package",
]


class BudgetExceeded(RuntimeError):
    pass


class Settings(BaseModel):
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5-20250929"
    salesforce_instance_url: str = ""
    allowed_domains: list[str] = Field(default_factory=list)
    max_tokens_per_run: int = 100_000
    max_cost_usd_per_run: float = 5.00
    llm_timeout_secs: int = DEFAULT_LLM_TIMEOUT_SECS

    @classmethod
    def from_env(cls) -> "Settings":
        raw_domains = os.getenv("SENTINEL_ALLOWED_DOMAINS", "")
        domains = [d.strip().lower() for d in raw_domains.split(",") if d.strip()]
        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
            salesforce_instance_url=os.getenv("SALESFORCE_INSTANCE_URL", ""),
            allowed_domains=domains,
            max_tokens_per_run=int(os.getenv("SENTINEL_MAX_TOKENS_PER_RUN", "100000")),
            max_cost_usd_per_run=float(os.getenv("SENTINEL_MAX_COST_USD_PER_RUN", "5.00")),
        )


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    inp, out = MODEL_PRICING_PER_1K.get(model, DEFAULT_PRICING)
    return (input_tokens / 1000.0) * inp + (output_tokens / 1000.0) * out


def hostname_of(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def is_domain_allowed(url: str, allowed_domains: list[str]) -> bool:
    """Exact or parent-domain match. Empty allowlist allows nothing."""
    host = hostname_of(url)
    if not host or not allowed_domains:
        return False
    allowed = {d.lower().lstrip(".") for d in allowed_domains}
    return any(host == d or host.endswith("." + d) for d in allowed)


def assert_sandbox_or_dev(instance_url: str) -> None:
    """Production block. Refuse to start unless target is sandbox / Dev Edition / scratch.

    Fails loudly with ValueError — never warn-and-continue.
    """
    host = hostname_of(instance_url)
    if not host:
        raise ValueError(f"Refusing to start: cannot parse SALESFORCE_INSTANCE_URL={instance_url!r}")
    lowered = host.lower()
    if lowered in {"login.salesforce.com", "www.salesforce.com", "salesforce.com"}:
        raise ValueError(f"Refusing to start: {host} is production/login, not a sandbox.")
    safe_markers = ("develop.", ".sandbox.", "sandbox.", "scratch.", ".scratch.")
    if any(m in lowered for m in safe_markers):
        return
    # Bare *.my.salesforce.com with no sandbox/develop/scratch qualifier = production.
    if lowered.endswith(".my.salesforce.com"):
        raise ValueError(
            f"Refusing to start: {host} looks like production "
            "(no develop/sandbox/scratch qualifier). Use a Dev Edition or sandbox org."
        )
    # Localhost is allowed for tests/red-team pages only.
    if lowered in {"localhost", "127.0.0.1"}:
        return
    raise ValueError(
        f"Refusing to start: {host} is not a recognised sandbox/Developer org. "
        "Set SALESFORCE_INSTANCE_URL to your Dev Edition or sandbox."
    )


def is_action_blocked(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in BLOCKED_ACTION_PHRASES)


class CostTracker:
    """Running total enforced in code. Abort cleanly when the cap is hit."""

    def __init__(self, max_tokens: int, max_cost_usd: float) -> None:
        self.max_tokens = max_tokens
        self.max_cost_usd = max_cost_usd
        self.tokens_used = 0
        self.cost_usd = 0.0

    def add(self, tokens: int, cost: float) -> None:
        self.tokens_used += tokens
        self.cost_usd += cost
        logger.info(
            "LLM cost: +%d tokens (+$%.4f) — total %d tokens / $%.4f (cap %d / $%.2f)",
            tokens, cost, self.tokens_used, self.cost_usd, self.max_tokens, self.max_cost_usd,
        )
        if self.tokens_used > self.max_tokens or self.cost_usd > self.max_cost_usd:
            raise BudgetExceeded(
                f"Budget kill switch: {self.tokens_used} tokens / ${self.cost_usd:.4f} "
                f"exceeds cap {self.max_tokens} / ${self.max_cost_usd:.2f}"
            )
