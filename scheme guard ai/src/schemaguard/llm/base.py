"""Provider-agnostic LLM interface.

Each call names a `task` (explain_change | plan_fix | generate_patch | write_summary), a system and
user prompt for real models, and a structured `context` dict. Real providers only see the prompts;
the deterministic FakeLLM reads `context` so tests and CI are reproducible and offline.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

# USD per 1M tokens (input, output). Used for budget enforcement and reporting; always an estimate.
PRICES: dict[str, tuple[float, float]] = {
    "fake": (0.0, 0.0),
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
}
UNKNOWN_MODEL_PRICE = (5.00, 25.00)  # conservative when an Azure deployment name hides the model


def estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    p_in, p_out = PRICES.get(model, UNKNOWN_MODEL_PRICE)
    return round(tokens_in * p_in / 1e6 + tokens_out * p_out / 1e6, 6)


def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


@dataclass
class LLMResponse:
    text: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    model: str

    def json(self) -> dict[str, Any]:
        return parse_json_object(self.text)


class LLMError(RuntimeError):
    pass


class LLMClient(Protocol):
    name: str
    model: str

    def complete(
        self, task: str, system: str, user: str, context: dict[str, Any], json_mode: bool = True
    ) -> LLMResponse: ...


def parse_json_object(text: str) -> dict[str, Any]:
    """Parse the first JSON object in a model reply (tolerates ```json fences and prose)."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise LLMError("model reply contained no JSON object") from None
        obj = json.loads(text[start : end + 1])
    if not isinstance(obj, dict):
        raise LLMError("model reply JSON is not an object")
    return obj
