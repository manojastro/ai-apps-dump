"""Mask bank account numbers in anything that leaves the process (logs, traces, audit
payloads, evidence packs). Even synthetic numbers are masked, by rule."""

import re
from typing import Any

_ACCOUNT = re.compile(r"(?<!\d)(\d{5,14})(\d{4})(?!\d)")  # 9-18 digit runs
SENSITIVE_KEYS = {"account_number", "bank_account_number"}


def mask_text(text: str) -> str:
    return _ACCOUNT.sub(lambda m: "X" * len(m.group(1)) + m.group(2), text)


def mask(value: Any) -> Any:
    """Recursively mask strings and sensitive keys in JSON-like data."""
    if isinstance(value, str):
        return mask_text(value)
    if isinstance(value, dict):
        return {
            k: (mask_text(str(v)) if k in SENSITIVE_KEYS and v is not None else mask(v))
            for k, v in value.items()
        }
    if isinstance(value, list | tuple):
        return [mask(v) for v in value]
    return value
