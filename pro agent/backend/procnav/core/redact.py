"""Redaction for model inputs, logs, audit data, traces and stored page text."""

from __future__ import annotations

import re
from typing import Any

SENSITIVE_KEYS = re.compile(
    r"(^|_|-)(password|passwd|pass|secret|token|cookie|cookies|authorization|api_?key|otp|session_?id|credential"
    r"|credentials|storage_state)s?($|_|-)",
    re.IGNORECASE,
)
_PATTERNS: list[tuple[re.Pattern[str], Any]] = [
    # Postal addresses: Indian PIN codes with preceding address text on the same line.
    # Keep the destination reference, drop any address text that follows it.
    (
        re.compile(r"(?i)\b(ship to|consignee|deliver(?:y)? to)\b([^\n]{0,40}?ADDR-[A-Z0-9-]++\)?+)[^\n]+"),
        r"\1\2 [ADDRESS REDACTED]",
    ),
    (
        re.compile(r"[^\n,]{3,80},[^\n]{3,80}\b\d{6}\b"),
        lambda m: " ".join([*re.findall(r"ADDR-[A-Z0-9-]+", m.group(0)), "[ADDRESS REDACTED]"]),
    ),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[EMAIL]"),
    (re.compile(r"(?i)\b(sid_[a-z]+|procnav_session)=[^;\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)(bearer\s+)[a-z0-9._-]+"), r"\1[REDACTED]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{10,}\b"), "[API KEY]"),
    (re.compile(r"\b(?:\d[ -]?){13,19}\b"), "[NUMBER REDACTED]"),
]


def redact_text(value: str, extra_secrets: list[str] | None = None) -> str:
    out = value
    for secret in extra_secrets or []:
        if secret and len(secret) >= 4:
            out = out.replace(secret, "[SECRET]")
    for pattern, repl in _PATTERNS:
        out = pattern.sub(repl, out)
    return out


def redact(value: Any, extra_secrets: list[str] | None = None) -> Any:
    if isinstance(value, str):
        return redact_text(value, extra_secrets)
    if isinstance(value, dict):
        return {
            k: ("[REDACTED]" if SENSITIVE_KEYS.search(str(k)) else redact(v, extra_secrets)) for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact(v, extra_secrets) for v in value]
    return value
