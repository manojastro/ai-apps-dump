"""Concrete LLM providers. All network calls go through the egress allowlist with timeouts.

* ``mock``      - deterministic; returns the agent's evidence-derived template output.
* ``openai``    - any OpenAI-compatible Chat Completions endpoint (AI_BASE_URL), JSON mode.
* ``anthropic`` - Anthropic Messages API; structured output via a forced tool call.
* ``gemini``    - Google Gemini generateContent with ``responseMimeType=application/json``.
"""

from __future__ import annotations

import json
from typing import Any

from app.integrations.http import request_with_retry
from app.llm.base import UNTRUSTED_PREAMBLE, LLMError, LLMProvider, StructuredTask


def _schema(task: StructuredTask[Any]) -> dict[str, Any]:
    return task.output_model.model_json_schema()


def _system(task: StructuredTask[Any]) -> str:
    return (
        f"{task.system}\n\n{UNTRUSTED_PREAMBLE}\n\nRespond ONLY with a JSON object that validates against this "
        f"JSON Schema:\n{json.dumps(_schema(task))}"
    )


class MockProvider(LLMProvider):
    name = "mock"

    def __init__(self, model: str = "deterministic-template-v1", **kw: Any) -> None:
        super().__init__(model or "deterministic-template-v1", **kw)

    def _complete_json(self, task: StructuredTask[Any]) -> tuple[str, int | None, int | None]:
        return json.dumps(task.mock_response()), 0, 0

    def _cost(self, p: int | None, c: int | None) -> float | None:
        return 0.0


class OpenAICompatibleProvider(LLMProvider):
    name = "openai"

    def __init__(self, model: str, api_key: str, base_url: str, timeout: float, **kw: Any) -> None:
        super().__init__(model, **kw)
        self.api_key = api_key
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self.timeout = timeout

    def _complete_json(self, task: StructuredTask[Any]) -> tuple[str, int | None, int | None]:
        resp = request_with_retry(
            "POST",
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "temperature": task.temperature,
                "max_tokens": task.max_output_tokens,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": _system(task)}, {"role": "user", "content": task.user}],
            },
            timeout=self.timeout,
            attempts=2,
        )
        if resp.status_code != 200:
            raise LLMError(f"OpenAI-compatible endpoint returned HTTP {resp.status_code}")
        body = resp.json()
        usage = body.get("usage") or {}
        return body["choices"][0]["message"]["content"] or "", usage.get("prompt_tokens"), usage.get("completion_tokens")


class AnthropicProvider(LLMProvider):
    name = "anthropic"
    API_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, model: str, api_key: str, timeout: float, base_url: str = "", **kw: Any) -> None:
        super().__init__(model, **kw)
        self.api_key = api_key
        self.timeout = timeout
        self.url = f"{base_url.rstrip('/')}/v1/messages" if base_url else self.API_URL

    def _complete_json(self, task: StructuredTask[Any]) -> tuple[str, int | None, int | None]:
        tool = {"name": "submit_result", "description": f"Submit the {task.name} result.", "input_schema": _schema(task)}
        resp = request_with_retry(
            "POST",
            self.url,
            headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={
                "model": self.model,
                "max_tokens": task.max_output_tokens,
                "temperature": task.temperature,
                "system": f"{task.system}\n\n{UNTRUSTED_PREAMBLE}",
                "messages": [{"role": "user", "content": task.user}],
                "tools": [tool],
                "tool_choice": {"type": "tool", "name": "submit_result"},
            },
            timeout=self.timeout,
            attempts=2,
        )
        if resp.status_code != 200:
            raise LLMError(f"Anthropic API returned HTTP {resp.status_code}")
        body = resp.json()
        usage = body.get("usage") or {}
        block = next((b for b in body.get("content", []) if b.get("type") == "tool_use"), None)
        if block is None:
            return "", usage.get("input_tokens"), usage.get("output_tokens")
        return json.dumps(block.get("input", {})), usage.get("input_tokens"), usage.get("output_tokens")


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, model: str, api_key: str, timeout: float, base_url: str = "", **kw: Any) -> None:
        super().__init__(model, **kw)
        self.api_key = api_key
        self.timeout = timeout
        self.base = (base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")

    def _complete_json(self, task: StructuredTask[Any]) -> tuple[str, int | None, int | None]:
        resp = request_with_retry(
            "POST",
            f"{self.base}/models/{self.model}:generateContent",
            headers={"x-goog-api-key": self.api_key},
            json={
                "systemInstruction": {"parts": [{"text": _system(task)}]},
                "contents": [{"role": "user", "parts": [{"text": task.user}]}],
                "generationConfig": {
                    "temperature": task.temperature,
                    "maxOutputTokens": task.max_output_tokens,
                    "responseMimeType": "application/json",
                },
            },
            timeout=self.timeout,
            attempts=2,
        )
        if resp.status_code != 200:
            raise LLMError(f"Gemini API returned HTTP {resp.status_code}")
        body = resp.json()
        usage = body.get("usageMetadata") or {}
        parts = (body.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts)
        return text, usage.get("promptTokenCount"), usage.get("candidatesTokenCount")
