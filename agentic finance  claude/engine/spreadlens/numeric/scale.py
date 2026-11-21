"""Scale and currency detection plus exact scale conversion."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

# Exact decimal factors to base units.
SCALE_FACTORS: dict[str, Decimal] = {
    "units": Decimal("1"),
    "thousands": Decimal("1000"),
    "lakhs": Decimal("100000"),
    "millions": Decimal("1000000"),
    "crores": Decimal("10000000"),
    "billions": Decimal("1000000000"),
}

SCALE_LABELS = {
    "units": "", "thousands": "thousand", "lakhs": "lakh", "millions": "million",
    "crores": "crore", "billions": "billion",
}

_SCALE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("crores", re.compile(r"\b(crores?|cr\.?)(?=[\s,)\]]|$)", re.I)),
    ("lakhs", re.compile(r"\b(lakhs?|lacs?)\b", re.I)),
    ("millions", re.compile(r"\b(millions?|mn)\b", re.I)),
    ("billions", re.compile(r"\b(billions?|bn)\b", re.I)),
    ("thousands", re.compile(r"(\bthousands?\b|'000|’000|\b000s\b)", re.I)),
]
_UNITS_HINT = re.compile(r"\b(in\s+(rupees|inr|₹)\b(?!\s*(crore|lakh|lac|million|thousand|'000)))", re.I)

_CURRENCY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("INR", re.compile(r"(₹|\bINR\b|\bRs\.?(?=\s|\d|$)|\bRupees?\b)", re.I)),
    ("USD", re.compile(r"(US\$|\bUSD\b|\$(?=\s?\d|\s?in\b|\s?million|\s?thousand)|\bUS dollars?\b)", re.I)),
    ("EUR", re.compile(r"(€|\bEUR\b|\beuros?\b)", re.I)),
    ("GBP", re.compile(r"(£|\bGBP\b|\bpounds? sterling\b)", re.I)),
]


@dataclass
class Detection:
    value: str | None
    evidence: list[str]
    conflicts: list[str]


def _unit_context(text: str) -> list[str]:
    """Lines likely to be unit declarations, e.g. '(All amounts in ₹ crores)'."""
    out = []
    for line in text.splitlines():
        low = line.lower()
        if any(k in low for k in ("amount", "in ₹", "in rs", "in inr", "in usd", "rupees", "crore", "lakh",
                                  "million", "thousand", "'000", "(in ", "currency")):
            if len(line) < 160:
                out.append(line.strip())
    return out


def detect_scale(text: str) -> Detection:
    lines = _unit_context(text)
    found: dict[str, list[str]] = {}
    for line in lines:
        for name, pat in _SCALE_PATTERNS:
            if pat.search(line):
                found.setdefault(name, []).append(line)
                break
        else:
            if _UNITS_HINT.search(line):
                found.setdefault("units", []).append(line)
    if not found:
        return Detection(None, [], [])
    if len(found) == 1:
        name, ev = next(iter(found.items()))
        return Detection(name, ev[:3], [])
    return Detection(None, [e for v in found.values() for e in v][:5], sorted(found))


def detect_currency(text: str) -> Detection:
    found: dict[str, list[str]] = {}
    for line in text.splitlines():
        for code, pat in _CURRENCY_PATTERNS:
            if pat.search(line):
                found.setdefault(code, []).append(line.strip()[:160])
    if not found:
        return Detection(None, [], [])
    # Rank by frequency; conflicting explicit currencies are surfaced, never merged.
    ranked = sorted(found.items(), key=lambda kv: -len(kv[1]))
    if len(ranked) == 1:
        return Detection(ranked[0][0], ranked[0][1][:3], [])
    top, second = ranked[0], ranked[1]
    if len(top[1]) >= 3 * len(second[1]):
        return Detection(top[0], top[1][:3], [])
    return Detection(None, top[1][:2] + second[1][:2], [c for c, _ in ranked])


def to_base_units(value: Decimal, scale: str) -> Decimal:
    return value * SCALE_FACTORS[scale]


def from_base_units(value: Decimal, scale: str) -> Decimal:
    return value / SCALE_FACTORS[scale]


def half_unit(decimals: int | None, scale: str | None) -> Decimal:
    """Maximum rounding error of a reported figure, in base units."""
    d = 0 if decimals is None else decimals
    factor = SCALE_FACTORS.get(scale or "units", Decimal("1"))
    return (Decimal("0.5") * (Decimal(10) ** -d)) * factor
