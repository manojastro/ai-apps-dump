"""Zero-secret helpers (M25): sanitize outbound, resolve inbound server-side.

Outbound (anything an LLM, log, or UI could see) passes sanitize_for_llm.
Inbound (coded-tool layer only) resolves aliases through SecureContext,
which lives server-side and is never serialized, logged, or prompted.
"""

from __future__ import annotations

from typing import Any

from common.redaction import redact_text


def sanitize_for_llm(obj: Any) -> Any:
    """Deep-copy obj with every string redacted. Dicts/lists recurse."""
    if isinstance(obj, str):
        return redact_text(obj)
    if isinstance(obj, dict):
        return {k: sanitize_for_llm(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize_for_llm(v) for v in obj]
    return obj


class SecureContext:
    """Alias <-> real mapping. Server-side only; never leaves coded tools."""

    def __init__(self, mapping: dict[str, str] | None = None) -> None:
        self._mapping = dict(mapping or {})

    def bind(self, alias: str, real: str) -> None:
        if not alias or not real:
            raise ValueError("alias and real value are both required")
        self._mapping[alias] = real

    def resolve(self, text: str) -> str:
        """Alias → real (coded-tool layer preparing a privileged call)."""
        for alias, real in self._mapping.items():
            if alias in text:
                text = text.replace(alias, real)
        return text

    def cloak(self, text: str) -> str:
        """Real → alias for anything prompt-bound (plus shape redaction)."""
        for alias, real in self._mapping.items():
            if real and real in text:
                text = text.replace(real, alias)
        return redact_text(text)

    def aliases(self) -> list[str]:
        return sorted(self._mapping)
