"""Normalisation helpers. Adapters call these so every downstream step compares clean values."""

from __future__ import annotations

import re
import unicodedata

_WS = re.compile(r"\s+")
_NON_NAME = re.compile(r"[^a-z0-9 ]")

PLAN_ALIASES = {
    "professional": "pro",
    "pro plan": "pro",
    "starter plan": "starter",
    "growth plan": "growth",
    "ent": "enterprise",
}


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def normalize_email(email: str | None) -> str | None:
    """Lower-case, trim and drop '+tag' sub-addressing. Returns None for empty input."""
    if email is None:
        return None
    e = email.strip().lower()
    if not e or "@" not in e:
        return e or None
    local, _, domain = e.partition("@")
    local = local.split("+", 1)[0]
    return f"{local}@{domain.strip()}"


def email_domain(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    return email.rsplit("@", 1)[1]


def normalize_name(name: str | None) -> str | None:
    """'  GARCÍA,  José ' -> 'jose garcia'."""
    if name is None:
        return None
    n = strip_accents(name).strip()
    if "," in n:
        last, _, first = n.partition(",")
        n = f"{first} {last}"
    n = _NON_NAME.sub(" ", n.lower())
    n = _WS.sub(" ", n).strip()
    return n or None


def normalize_plan(plan: str | None) -> str | None:
    if plan is None:
        return None
    p = _WS.sub(" ", plan.strip().lower())
    return PLAN_ALIASES.get(p, p) or None


def normalize_status(status: str | None) -> str | None:
    if status is None:
        return None
    return status.strip().lower() or None
