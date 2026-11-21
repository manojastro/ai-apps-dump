from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .config import settings
from .models import Evidence


@dataclass(frozen=True)
class ProviderResult:
    text: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float


class LLMProvider(Protocol):
    def complete(self, task: str, evidence: list[Evidence]) -> ProviderResult: ...


class DeterministicProvider:
    """Offline adapter for tests/demos; it refuses to answer without tool evidence."""

    name = "deterministic-rules-v1"

    def complete(self, task: str, evidence: list[Evidence]) -> ProviderResult:
        if not evidence:
            raise ValueError("provider refuses to generate factual output without evidence")
        evidence_ids = ", ".join(item.id for item in evidence)
        text = f"{task} grounded in {len(evidence)} tool observations: {evidence_ids}"
        return ProviderResult(
            text=text,
            input_tokens=sum(len(item.summary.split()) for item in evidence),
            output_tokens=len(text.split()),
            estimated_cost_usd=0.0,
        )


def provider_from_settings() -> LLMProvider:
    if settings.llm_mode != "deterministic":
        raise RuntimeError(
            "No external provider is configured. Set LLM_MODE=deterministic or add a credentialed adapter."
        )
    return DeterministicProvider()

