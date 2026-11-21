"""Rounding tolerance derived from source precision.

Every reported figure is rounded to its last printed digit, so its true value lies within
± half a unit of that digit. A check that adds n rounded figures and compares them with
another rounded figure can therefore be off by at most the sum of those half-units. That
sum is the rounding tolerance. It is NOT materiality: materiality is an analyst setting
reported alongside, and never used to turn a fail into a pass.
"""

from __future__ import annotations

from decimal import Decimal

from spreadlens.numeric.scale import half_unit
from spreadlens.rules.types import Fact


def rounding_tolerance(facts: list[Fact]) -> tuple[Decimal, str]:
    total = Decimal("0")
    parts = []
    for f in facts:
        hu = half_unit(f.decimals, f.scale)
        total += hu
        parts.append(f"±{hu.normalize():f} ({f.decimals or 0}dp, {f.scale or 'units'})")
    basis = (
        f"Sum of half-unit rounding bounds of {len(facts)} rounded figures: "
        + " + ".join(parts[:8])
        + (" ..." if len(parts) > 8 else "")
    )
    return total, basis
