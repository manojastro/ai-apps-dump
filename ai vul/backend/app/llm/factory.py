from __future__ import annotations

from typing import Any

from app.core.config import Settings, get_settings
from app.llm.base import LLMProvider
from app.llm.providers import AnthropicProvider, GeminiProvider, MockProvider, OpenAICompatibleProvider


class ProviderConfigError(ValueError):
    pass


def build_provider(settings: Settings | None = None, provider: str | None = None, model: str | None = None) -> LLMProvider:
    s = settings or get_settings()
    name = provider or s.ai_provider
    model = model if model is not None else s.ai_model
    common = {"max_retries": s.ai_max_retries, "cost_in": s.ai_cost_input_per_1k, "cost_out": s.ai_cost_output_per_1k}
    if name == "mock":
        return MockProvider(model or "deterministic-template-v1", max_retries=0)
    key = s.ai_api_key.get_secret_value()
    if not key:
        raise ProviderConfigError(f"AI_PROVIDER={name} requires AI_API_KEY")
    if not model:
        raise ProviderConfigError(f"AI_PROVIDER={name} requires AI_MODEL (no model name is assumed)")
    if name == "openai":
        return OpenAICompatibleProvider(model, key, s.ai_base_url, s.ai_timeout_seconds, **common)
    if name == "anthropic":
        return AnthropicProvider(model, key, s.ai_timeout_seconds, s.ai_base_url, **common)
    if name == "gemini":
        return GeminiProvider(model, key, s.ai_timeout_seconds, s.ai_base_url, **common)
    raise ProviderConfigError(f"Unknown AI_PROVIDER '{name}'")


def provider_status(settings: Settings | None = None) -> dict[str, Any]:
    s = settings or get_settings()
    try:
        p = build_provider(s)
        return {"provider": p.name, "model": p.model, "status": "Mock" if p.name == "mock" else "Configured", "detail": ""}
    except ProviderConfigError as exc:
        return {"provider": s.ai_provider, "model": s.ai_model or None, "status": "Error", "detail": str(exc)}
