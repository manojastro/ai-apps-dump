from __future__ import annotations

import re
from dataclasses import dataclass

from fastapi import Header, HTTPException, status

from .config import settings
from .models import Role


INJECTION_PATTERNS = (
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*prompt", re.IGNORECASE),
    re.compile(r"(?:run|execute)\s+(?:a\s+)?(?:shell|command)", re.IGNORECASE),
    re.compile(r"<\/?(?:system|assistant|tool)[^>]*>", re.IGNORECASE),
)


def sanitize_untrusted(value: str, max_length: int = 2_000) -> tuple[str, bool]:
    """Redact secrets and neutralize common prompt-injection phrases."""

    clean = value.replace("\x00", " ")[:max_length]
    redacted = len(value) > max_length
    for key in settings.secret_patterns:
        pattern = re.compile(rf"(?i)({re.escape(key)}\s*[:=]\s*)([^\s,;]+)")
        clean, count = pattern.subn(r"\1[REDACTED]", clean)
        redacted = redacted or count > 0
    for pattern in INJECTION_PATTERNS:
        clean, count = pattern.subn("[UNTRUSTED_INSTRUCTION_REMOVED]", clean)
        redacted = redacted or count > 0
    clean = " ".join(clean.split())
    return clean, redacted


def untrusted_data_block(value: str) -> str:
    sanitized, _ = sanitize_untrusted(value)
    return f"<untrusted-observation>{sanitized}</untrusted-observation>"


@dataclass(frozen=True)
class Principal:
    subject: str
    role: Role


def get_principal(
    x_user: str = Header(default="demo-investigator"),
    x_role: str = Header(default=Role.investigator.value),
) -> Principal:
    try:
        role = Role(x_role)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid role") from exc
    return Principal(subject=x_user[:80], role=role)


def require_investigator(principal: Principal) -> Principal:
    if principal.role not in {Role.investigator, Role.admin}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="investigator role required")
    return principal


def require_admin(principal: Principal) -> Principal:
    if principal.role is not Role.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin role required")
    return principal
