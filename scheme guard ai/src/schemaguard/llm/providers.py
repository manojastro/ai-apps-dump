"""Real LLM providers. Not exercised in CI (no keys); enabled with SCHEMAGUARD_LLM_PROVIDER.

Keys come from the providers' standard env vars (AZURE_OPENAI_API_KEY, OPENAI_API_KEY,
ANTHROPIC_API_KEY). For Azure without a key, DefaultAzureCredential (managed identity) is used if
`azure-identity` is installed.
"""

from __future__ import annotations

import os
from typing import Any

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from schemaguard.llm.base import LLMError, LLMResponse, estimate_cost

MAX_OUTPUT_TOKENS = 16000


class _Transient(Exception):
    pass


_retry = retry(
    retry=retry_if_exception_type(_Transient),
    wait=wait_exponential(multiplier=1, max=20),
    stop=stop_after_attempt(4),
    reraise=True,
)


class OpenAIChatLLM:
    """OpenAI or Azure OpenAI chat completions."""

    def __init__(
        self, *, azure: bool, model: str, timeout_s: float, endpoint: str = "", api_version: str = ""
    ):
        import openai

        self._openai = openai
        self.name = "azure" if azure else "openai"
        self.model = model
        if azure:
            key = os.environ.get("AZURE_OPENAI_API_KEY")
            kwargs: dict[str, Any] = {
                "azure_endpoint": endpoint,
                "api_version": api_version,
                "timeout": timeout_s,
            }
            if key:
                kwargs["api_key"] = key
            else:
                from azure.identity import DefaultAzureCredential, get_bearer_token_provider

                kwargs["azure_ad_token_provider"] = get_bearer_token_provider(
                    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
                )
            self.client: Any = openai.AzureOpenAI(**kwargs)
        else:
            self.client = openai.OpenAI(timeout=timeout_s)

    @_retry
    def complete(
        self, task: str, system: str, user: str, context: dict[str, Any], json_mode: bool = True
    ) -> LLMResponse:
        o = self._openai
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                response_format={"type": "json_object"} if json_mode else {"type": "text"},
                max_tokens=MAX_OUTPUT_TOKENS,
            )
        except (o.RateLimitError, o.APIConnectionError, o.APITimeoutError, o.InternalServerError) as exc:
            raise _Transient(str(exc)) from exc
        except o.APIStatusError as exc:
            raise LLMError(f"{self.name} API error {exc.status_code}: {exc.message}") from exc
        text = resp.choices[0].message.content or ""
        tin, tout = resp.usage.prompt_tokens, resp.usage.completion_tokens
        return LLMResponse(text, tin, tout, estimate_cost(self.model, tin, tout), self.model)


class AnthropicLLM:
    """Claude via the official Anthropic SDK (Messages API).

    Server-side refusal fallbacks are enabled (`fallbacks="default"`), so a policy decline is retried
    on a fallback model inside the same call; a final `refusal` stop reason is surfaced as an error.
    """

    def __init__(self, *, model: str, timeout_s: float):
        import anthropic

        self._anthropic = anthropic
        self.name = "anthropic"
        self.model = model or "claude-opus-5-5"
        self.client = anthropic.Anthropic(timeout=timeout_s, max_retries=3)

    def complete(
        self, task: str, system: str, user: str, context: dict[str, Any], json_mode: bool = True
    ) -> LLMResponse:
        a = self._anthropic
        if json_mode:
            system = system + "\n\nRespond with a single JSON object and nothing else."
        try:
            resp = self.client.beta.messages.create(
                model=self.model,
                max_tokens=MAX_OUTPUT_TOKENS,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_config={"effort": "medium"},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except a.APIStatusError as exc:  # SDK already retried 408/409/429/5xx and connection errors
            raise LLMError(f"anthropic API error {exc.status_code}: {exc.message}") from exc
        except a.APIConnectionError as exc:
            raise LLMError(f"anthropic connection error: {exc}") from exc
        if resp.stop_reason == "refusal":
            raise LLMError("model declined the request (stop_reason=refusal)")
        text = "".join(b.text for b in resp.content if b.type == "text")
        tin, tout = resp.usage.input_tokens, resp.usage.output_tokens
        return LLMResponse(text, tin, tout, estimate_cost(self.model, tin, tout), resp.model)
