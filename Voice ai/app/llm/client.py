"""The ONLY module that talks to an LLM. MOCK mode (default) is offline and free.

Messages use Anthropic content-block dicts:
  assistant: {"role": "assistant", "content": [{"type": "text"|"tool_use", ...}]}
  user:      {"role": "user", "content": "text" | [{"type": "tool_result", "tool_use_id", "content"}]}
"""
from __future__ import annotations

import logging
import os
import time
from typing import Protocol

from pydantic import BaseModel

from app.config import get_settings

log = logging.getLogger("eir.llm")


class ToolUse(BaseModel):
    id: str
    name: str
    input: dict


class LLMResponse(BaseModel):
    text: str = ""
    tool_uses: list[ToolUse] = []
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: float = 0.0


class LLMClient(Protocol):
    mode: str

    def complete(self, *, agent: str, prompt_version: str, system: str, messages: list[dict],
                 tools: list[dict]) -> LLMResponse: ...


def estimate_tokens(obj) -> int:
    """Rough char/4 estimate. Used in MOCK mode only; real runs use the API's usage numbers."""
    return max(1, len(str(obj)) // 4)


class ScriptedClient:
    """Returns pre-written responses in order. For unit tests."""

    mode = "MOCK"

    def __init__(self, script: list[LLMResponse | str | dict]):
        self.script = list(script)
        self.calls: list[dict] = []

    def complete(self, *, agent, prompt_version, system, messages, tools) -> LLMResponse:
        self.calls.append({"agent": agent, "messages": list(messages), "tools": [t["name"] for t in tools]})
        if not self.script:
            raise AssertionError("ScriptedClient script exhausted")
        item = self.script.pop(0)
        if isinstance(item, str):
            item = LLMResponse(text=item)
        elif isinstance(item, dict):
            item = LLMResponse(**item)
        item.tokens_in = item.tokens_in or estimate_tokens(messages)
        item.tokens_out = item.tokens_out or estimate_tokens(item.text or item.tool_uses)
        return item


class MockClient:
    """Deterministic rule-based stand-in for the model (see app/llm/mock_brain.py).

    mock_mode: "normal" behaves; "gullible" obeys instructions hidden in untrusted text (worst case for the
    security tests); "stubborn" is gullible and repeats a bad answer even after correction.
    """

    mode = "MOCK"

    def __init__(self, mock_mode: str = "normal"):
        self.mock_mode = mock_mode

    def complete(self, *, agent, prompt_version, system, messages, tools) -> LLMResponse:
        from app.llm.mock_brain import think

        t0 = time.perf_counter()
        resp = think(agent, messages, self.mock_mode)
        resp.latency_ms = (time.perf_counter() - t0) * 1000
        resp.tokens_in = estimate_tokens(system) + estimate_tokens(messages)
        resp.tokens_out = estimate_tokens(resp.text or resp.tool_uses)
        return resp


class AnthropicClient:
    """Real model via the Anthropic SDK. Only used when EIR_LLM_MODE=REAL (costs money)."""

    mode = "REAL"

    def __init__(self, model: str | None = None):
        import anthropic

        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self.client = anthropic.Anthropic()
        self.model = model or get_settings().model

    def complete(self, *, agent, prompt_version, system, messages, tools) -> LLMResponse:
        t0 = time.perf_counter()
        kwargs = dict(model=self.model, max_tokens=1024, system=system, messages=messages)
        if tools:
            kwargs["tools"] = tools
        r = self.client.messages.create(**kwargs)
        text = "".join(b.text for b in r.content if b.type == "text")
        uses = [ToolUse(id=b.id, name=b.name, input=dict(b.input)) for b in r.content if b.type == "tool_use"]
        out = LLMResponse(text=text, tool_uses=uses, tokens_in=r.usage.input_tokens, tokens_out=r.usage.output_tokens,
                          latency_ms=(time.perf_counter() - t0) * 1000)
        log.info("llm agent=%s prompt=%s in=%s out=%s ms=%.0f", agent, prompt_version, out.tokens_in,
                 out.tokens_out, out.latency_ms)
        return out


def get_llm(mock_mode: str = "normal") -> LLMClient:
    if get_settings().llm_mode == "REAL":
        return AnthropicClient()
    return MockClient(mock_mode)
