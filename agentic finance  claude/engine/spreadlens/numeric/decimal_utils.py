"""Decimal helpers. Monetary values cross the API as strings, never floats."""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal, getcontext

getcontext().prec = 40

EXCEL_SAFE_DIGITS = 15  # IEEE-754 doubles keep ~15 significant decimal digits


def dstr(value: Decimal | None) -> str | None:
    """Canonical string for a Decimal (no exponent, trailing zeros trimmed)."""
    if value is None:
        return None
    if value == 0:
        return "0"
    s = format(value.normalize(), "f")
    return s


def quantize(value: Decimal, places: int) -> Decimal:
    return value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)


def significant_digits(value: Decimal) -> int:
    t = value.normalize().as_tuple()
    digits = len(t.digits)
    return max(digits, 1)


def excel_safe(value: Decimal) -> bool:
    return significant_digits(value) <= EXCEL_SAFE_DIGITS


def group_indian(value: Decimal, places: int = 2) -> str:
    q = quantize(value, places)
    neg = q < 0
    s = format(abs(q), "f")
    int_part, _, frac = s.partition(".")
    if len(int_part) > 3:
        head, tail = int_part[:-3], int_part[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        int_part = ",".join(parts + [tail])
    out = int_part + (f".{frac}" if frac else "")
    return f"({out})" if neg else out


def group_intl(value: Decimal, places: int = 2) -> str:
    q = quantize(value, places)
    s = f"{abs(q):,.{places}f}"
    return f"({s})" if q < 0 else s
