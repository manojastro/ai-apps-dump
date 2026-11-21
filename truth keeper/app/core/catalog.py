"""Static business reference data shared by the generator, detector and impact estimator.

These are modelling assumptions for the synthetic world, not measured values.
"""

from __future__ import annotations

# List price per month, in the subscription's own currency.
PLAN_PRICES: dict[str, float] = {
    "starter": 49.0,
    "growth": 149.0,
    "pro": 399.0,
    "enterprise": 1200.0,
}
PLANS: tuple[str, ...] = tuple(PLAN_PRICES)

# Static FX table used only to sum money at risk across currencies (assumption).
FX_TO_USD: dict[str, float] = {"USD": 1.0, "EUR": 1.08, "GBP": 1.27}

CRM_STATUSES = ("active", "cancelled", "trial")
BILLING_STATUSES = ("active", "past_due", "cancelled")
LIFECYCLE_STAGES = ("lead", "onboarding", "customer", "churned")

# Billing past_due longer than this many days counts as a conflict when CRM says active.
PAST_DUE_THRESHOLD_DAYS = 30


def to_usd(amount: float, currency: str) -> float:
    return round(amount * FX_TO_USD.get(currency.upper(), 1.0), 2)
