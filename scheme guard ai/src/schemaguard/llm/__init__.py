from __future__ import annotations

from schemaguard.config import Settings
from schemaguard.llm.base import LLMClient, LLMError, LLMResponse, estimate_cost
from schemaguard.llm.fake import FakeLLM

__all__ = ["LLMClient", "LLMError", "LLMResponse", "estimate_cost", "FakeLLM", "make_llm"]


def make_llm(settings: Settings) -> LLMClient:
    p = settings.llm_provider
    if p == "fake":
        return FakeLLM()
    from schemaguard.llm.providers import AnthropicLLM, OpenAIChatLLM

    if p == "azure":
        return OpenAIChatLLM(
            azure=True,
            model=settings.azure_openai_deployment or settings.llm_model,
            timeout_s=settings.llm_timeout_s,
            endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
        )
    if p == "openai":
        return OpenAIChatLLM(
            azure=False, model=settings.llm_model or "gpt-4.1", timeout_s=settings.llm_timeout_s
        )
    if p == "anthropic":
        return AnthropicLLM(model=settings.llm_model or "claude-opus-5-5", timeout_s=settings.llm_timeout_s)
    raise ValueError(f"unknown llm provider {p!r}")
