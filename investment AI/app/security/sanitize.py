from __future__ import annotations

import html
import re

from app.constants import INJECTION_PHRASES

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def sanitize_text(text: str, *, max_len: int = 50_000) -> str:
    cleaned = _CONTROL.sub("", text or "")
    cleaned = html.escape(cleaned)
    return cleaned[:max_len]


def detect_prompt_injection(text: str) -> bool:
    lowered = (text or "").lower()
    return any(phrase in lowered for phrase in INJECTION_PHRASES)
