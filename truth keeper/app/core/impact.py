"""Deterministic estimate of monthly money at risk per conflict.

Formulas (all per month, in the subscription currency, also converted to USD with a static
FX table for totals):
  CANCELLED_BUT_BILLING_ACTIVE  sum(monthly_amount) of still-charging subscriptions  (refund risk)
  PLAN_MISMATCH                 |list_price(crm_plan) - monthly_amount|              (leakage / overbilling)
  CHURNED_STILL_MARKETED        0, non-monetary (brand + consent risk)
  EMAIL_MISMATCH                monthly_amount of the billing record whose email differs
                                (invoices may not reach the payer); 0 if only marketing differs
  DUPLICATE_CUSTOMER            sum(monthly_amount) of every live record except the first (double charge)
  PAST_DUE_BUT_CRM_ACTIVE       monthly_amount * ceil(days_past_due / 30)            (overdue balance)
"""

from __future__ import annotations

import math

from app.core.catalog import PLAN_PRICES, to_usd
from app.core.models import Conflict, ConflictType, Impact


def _amt(x) -> float:
    return float(x or 0.0)


def estimate(conflict: Conflict) -> Impact:
    ev = conflict.evidence
    billing = ev.get("billing") or []
    currency = (billing[0].get("currency") if billing else None) or "USD"
    t = conflict.type
    if t == ConflictType.CANCELLED_BUT_BILLING_ACTIVE:
        amount = sum(_amt(b["monthly_amount"]) for b in billing)
        formula = "sum(monthly_amount of still-charging subscriptions)"
    elif t == ConflictType.PLAN_MISMATCH:
        list_price = PLAN_PRICES.get(ev.get("crm_plan") or "", 0.0)
        amount = sum(abs(list_price - _amt(b["monthly_amount"])) for b in billing)
        formula = "|list_price(crm_plan) - billing monthly_amount|"
    elif t == ConflictType.CHURNED_STILL_MARKETED:
        return Impact(amount=0.0, currency="USD", amount_usd=0.0, monetary=False,
                      formula="non-monetary: brand and consent risk")
    elif t == ConflictType.EMAIL_MISMATCH:
        bill = [m for m in ev.get("mismatches", []) if m["system"] == "billing"]
        amount = sum(_amt(m.get("monthly_amount")) for m in bill)
        currency = (bill[0].get("currency") if bill else None) or "USD"
        formula = "monthly_amount of billing record with a different email"
    elif t == ConflictType.DUPLICATE_CUSTOMER:
        amount = sum(_amt(b["monthly_amount"]) for b in billing[1:])
        formula = "sum(monthly_amount of duplicate billing records beyond the first)"
    elif t == ConflictType.PAST_DUE_BUT_CRM_ACTIVE:
        amount = sum(_amt(b["monthly_amount"]) * math.ceil(b["days_past_due"] / 30) for b in billing)
        formula = "monthly_amount * ceil(days_past_due / 30)"
    else:  # pragma: no cover
        raise ValueError(f"unknown conflict type {t}")
    amount = round(amount, 2)
    return Impact(amount=amount, currency=currency, amount_usd=to_usd(amount, currency), formula=formula)


def attach(conflicts: list[Conflict]) -> list[Conflict]:
    for c in conflicts:
        c.impact = estimate(c)
    return conflicts
