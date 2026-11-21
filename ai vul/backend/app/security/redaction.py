"""Secret redaction for logs, traces, tool-call records and API responses."""

from __future__ import annotations

import re
from typing import Any

SENSITIVE_KEYS = re.compile(
    r"(pass(word)?|secret|token|api[_-]?key|authorization|cookie|client[_-]?secret|bearer|credential)",
    re.IGNORECASE,
)
SENSITIVE_VALUES = [
    re.compile(r"(?i)bearer\s+[a-z0-9._\-]+"),
    re.compile(r"(?<![A-Za-z0-9])sk-(?:proj-|ant-)?[A-Za-z0-9_\-]{20,}"),
    re.compile(r"eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}"),  # JWT
]
REDACTED = "[REDACTED]"


def redact_text(value: str) -> str:
    for pattern in SENSITIVE_VALUES:
        value = pattern.sub(REDACTED, value)
    return value


def redact(value: Any, _depth: int = 0) -> Any:
    """Recursively redact secrets in dict/list structures (bounded depth)."""
    if _depth > 8:
        return "[TRUNCATED]"
    if isinstance(value, dict):
        return {
            k: (REDACTED if isinstance(k, str) and SENSITIVE_KEYS.search(k) else redact(v, _depth + 1)) for k, v in value.items()
        }
    if isinstance(value, list | tuple):
        return [redact(v, _depth + 1) for v in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def truncate(value: Any, max_chars: int = 4000) -> Any:
    """Keep stored traces bounded."""
    if isinstance(value, str) and len(value) > max_chars:
        return value[:max_chars] + f"... [truncated {len(value) - max_chars} chars]"
    if isinstance(value, dict):
        return {k: truncate(v, max_chars) for k, v in value.items()}
    if isinstance(value, list):
        return [truncate(v, max_chars) for v in value[:200]]
    return value
