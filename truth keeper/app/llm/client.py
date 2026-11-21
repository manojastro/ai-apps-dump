"""The ONLY place that talks to an LLM.

  LLM_MODE=mock (default) - deterministic MockLLM, no network, zero cost
  LLM_MODE=real           - Claude through the official Anthropic SDK

Every call records model, prompt version, token usage and latency. Real mode uses:
  - structured outputs (output_config.format = JSON schema) when LLM_STRUCTURED_OUTPUT=true;
    the response is still parsed and validated by our own Pydantic models afterwards
  - output_config.effort from LLM_EFFORT
  - the server-side refusal fallback (beta) when LLM_USE_FALLBACKS=true
Temperature is not sent: current Claude models reject sampling parameters.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass

from app.config import Settings, get_settings
from app.llm.mock import MockLLM
from app.tracing import get_tracer

FALLBACK_BETA = "server-side-fallback-2026-07-01"


class LLMCallError(RuntimeError):
    """The call itself failed (network, rate limit, refusal...). Counts as a failed attempt."""

    def __init__(self, category: str, message: str):
        super().__init__(message)
        self.category = category


@dataclass
class LLMResult:
    text: str
    model: str
    prompt_version: str
    mode: str
    input_tokens: int
    output_tokens: int
    tokens_estimated: bool
    latency_ms: float
    stop_reason: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class LLMClient:
    def __init__(self, settings: Settings | None = None, mock: MockLLM | None = None):
        self.settings = settings or get_settings()
        self.mode = "mock" if mock is not None else self.settings.llm_mode
        self._mock = mock
        self._anthropic = None
        if self.mode == "mock" and self._mock is None:
            self._mock = MockLLM(profile=self.settings.mock_profile)

    @property
    def model_name(self) -> str:
        return f"mock-{self._mock.profile}" if self.mode == "mock" else self.settings.model

    def _client(self):
        if self._anthropic is None:
            import anthropic  # imported lazily so MOCK mode never needs credentials

            self._anthropic = anthropic.Anthropic()
        return self._anthropic

    def complete(self, *, system: str, user: str, prompt_version: str,
                 json_schema: dict | None = None) -> LLMResult:
        tracer = get_tracer()
        with tracer.start_as_current_span("llm.call") as span:
            span.set_attribute("openinference.span.kind", "LLM")
            span.set_attribute("llm.model_name", self.model_name)
            span.set_attribute("tk.prompt_version", prompt_version)
            span.set_attribute("tk.llm_mode", self.mode)
            span.set_attribute("input.value", user)
            span.set_attribute("llm.input_messages.0.message.role", "system")
            span.set_attribute("llm.input_messages.0.message.content", system)
            span.set_attribute("llm.input_messages.1.message.role", "user")
            span.set_attribute("llm.input_messages.1.message.content", user)
            t0 = time.perf_counter()
            try:
                if self.mode == "mock":
                    text = self._mock.respond(system, user)
                    result = LLMResult(
                        text=text, model=self.model_name, prompt_version=prompt_version, mode="mock",
                        input_tokens=(len(system) + len(user)) // 4, output_tokens=len(text) // 4,
                        tokens_estimated=True, latency_ms=0.0, stop_reason="end_turn",
                    )
                else:
                    result = self._real(system, user, prompt_version, json_schema)
            except LLMCallError as e:
                span.set_attribute("tk.error_category", e.category)
                raise
            result.latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            span.set_attribute("output.value", result.text)
            span.set_attribute("llm.token_count.prompt", result.input_tokens)
            span.set_attribute("llm.token_count.completion", result.output_tokens)
            span.set_attribute("llm.token_count.total", result.input_tokens + result.output_tokens)
            span.set_attribute("tk.latency_ms", result.latency_ms)
            return result

    def _real(self, system: str, user: str, prompt_version: str, json_schema: dict | None) -> LLMResult:
        import anthropic

        s = self.settings
        output_config: dict = {"effort": s.effort}
        if s.structured_output and json_schema:
            output_config["format"] = {"type": "json_schema", "schema": json_schema}
        kwargs: dict = dict(
            model=s.model,
            max_tokens=s.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config=output_config,
        )
        try:
            if s.use_fallbacks:
                resp = self._client().beta.messages.create(betas=[FALLBACK_BETA], fallbacks="default", **kwargs)
            else:
                resp = self._client().messages.create(**kwargs)
        except anthropic.RateLimitError as e:
            raise LLMCallError("rate_limited", str(e)) from e
        except anthropic.BadRequestError as e:
            raise LLMCallError("bad_request", str(e)) from e
        except anthropic.APIStatusError as e:
            raise LLMCallError(f"api_status_{e.status_code}", str(e)) from e
        except anthropic.APIConnectionError as e:
            raise LLMCallError("connection", str(e)) from e
        if resp.stop_reason == "refusal":
            raise LLMCallError("refusal", f"model declined: {getattr(resp, 'stop_details', None)}")
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        return LLMResult(
            text=text, model=getattr(resp, "model", s.model), prompt_version=prompt_version, mode="real",
            input_tokens=resp.usage.input_tokens, output_tokens=resp.usage.output_tokens, tokens_estimated=False,
            latency_ms=0.0, stop_reason=resp.stop_reason,
        )


def estimate_cost_usd(input_tokens: int, output_tokens: int, settings: Settings | None = None) -> float:
    s = settings or get_settings()
    return round(input_tokens / 1e6 * s.price_input_per_mtok + output_tokens / 1e6 * s.price_output_per_mtok, 6)


def dumps(obj) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, default=str)
