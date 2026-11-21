"""Turn SHAP values into plain-language reason codes.

SHAP says how much each input pushed one prediction up or down. Templates then state
that as a sentence using the real feature value, so a reason is always a fact about the
record. If a template does not fit the value (for example "no activity in 2 days" as a
risk), it returns None and the reason is skipped rather than shown misleadingly.
"""
from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
import shap
from lightgbm import LGBMClassifier
from sklearn.pipeline import Pipeline

STAGE_NAMES = ["prospecting", "qualification", "proposal", "negotiation"]


def _count(value: float, noun: str) -> str:
    """Write "1 ticket" or "2 tickets", never "1 tickets"."""
    return f"{value:.0f} {noun}{'' if round(value) == 1 else 's'}"


def shap_matrix(model: object, X: pd.DataFrame) -> np.ndarray:
    """SHAP values in log-odds, one row per record and one column per feature."""
    if isinstance(model, LGBMClassifier):
        values = shap.TreeExplainer(model).shap_values(X)
        if isinstance(values, list):
            values = values[1]
        values = np.asarray(values)
        return values[:, :, 1] if values.ndim == 3 else values
    if isinstance(model, Pipeline):
        transformed = model[:-1].transform(X)
        # Scaled features have mean 0, so a zero background means "the average record".
        background = np.zeros((1, transformed.shape[1]))
        return shap.LinearExplainer(model[-1], background).shap_values(transformed)
    raise TypeError(f"Unsupported model type: {type(model).__name__}")


Template = Callable[[float, bool], str | None]


def _deal_templates() -> dict[str, Template]:
    def silence(v: float, risk: bool) -> str | None:
        if risk:
            return f"No activity in {v:.0f} days" if v >= 10 else None
        return f"Recent activity ({v:.0f} days ago)" if v <= 10 else None

    def exec_contact(v: float, risk: bool) -> str | None:
        if risk and v == 0:
            return "No executive contact on this deal"
        return "Executive contact engaged" if not risk and v == 1 else None

    def exec_touch(v: float, risk: bool) -> str | None:
        if risk and v >= 30:
            return f"No executive contact in {v:.0f} days"
        return f"Executive touch {v:.0f} days ago" if not risk and v < 30 else None

    def stakeholders(v: float, risk: bool) -> str | None:
        if risk and v <= 2:
            return f"Only {v:.0f} stakeholder{'s' if v != 1 else ''} engaged"
        return f"{v:.0f} stakeholders engaged" if not risk and v >= 3 else None

    def recent(v: float, risk: bool) -> str | None:
        if risk and v <= 2:
            if v == 0:
                return "No activities in the last 30 days"
            return f"Only {v:.0f} {'activity' if v == 1 else 'activities'} in the last 30 days"
        return f"{v:.0f} activities in the last 30 days" if not risk and v >= 3 else None

    def stage(v: float, risk: bool) -> str | None:
        name = STAGE_NAMES[int(v)]
        if risk and v <= 1:
            return f"Still early, in {name}"
        return f"Advanced to {name}" if not risk and v >= 2 else None

    def velocity(v: float, risk: bool) -> str | None:
        if risk and v > 1.2:
            return f"{v:.1f}x slower than average in this stage"
        return "Moving at or above average pace" if not risk and v <= 1.0 else None

    def discount(v: float, risk: bool) -> str | None:
        return f"Heavy discount of {v:.0f}% (discounts do not lift win rate)" \
            if risk and v >= 25 else None

    def age(v: float, risk: bool) -> str | None:
        return f"Deal is {v:.0f} days old" if risk and v >= 90 else None

    def size(v: float, risk: bool) -> str | None:
        return f"Large vs. the account: {v:.0%} of current ARR" if risk and v >= 0.4 else None

    def tickets(v: float, risk: bool) -> str | None:
        text = f"{_count(v, 'severe support ticket')} open on the account"
        return text if risk and v > 0 else None

    def tickets_recent(v: float, risk: bool) -> str | None:
        return f"{_count(v, 'severe ticket')} in the last 45 days" if risk and v > 0 else None

    def overdue(v: float, risk: bool) -> str | None:
        return f"Close date passed {abs(v):.0f} days ago" if risk and v < 0 else None

    def pushed(v: float, risk: bool) -> str | None:
        return "Close date has already been pushed out" if risk and v == 1 else None

    def renewal(v: float, risk: bool) -> str | None:
        return "Renewal deals close at a higher rate" if not risk and v == 1 else None

    def expansion(v: float, risk: bool) -> str | None:
        return "Expansion of an existing customer" if not risk and v == 1 else None

    return {
        "days_since_last_activity": silence, "has_exec_contact": exec_contact,
        "days_since_exec_touch": exec_touch, "stakeholders_engaged": stakeholders,
        "activities_30d": recent, "stage_index": stage, "stage_velocity_ratio": velocity,
        "discount_pct": discount, "deal_age_days": age, "amount_to_arr": size,
        "open_severe_tickets": tickets, "severe_tickets_45d": tickets_recent,
        "days_to_close": overdue, "close_date_pushed": pushed, "is_renewal": renewal,
        "is_expansion": expansion,
    }


def _churn_templates() -> dict[str, Template]:
    # For churn, a positive SHAP value pushes towards leaving, so `risk` means "raises churn".
    def usage(v: float, risk: bool) -> str | None:
        if risk and v < 0.9:
            return f"Active users down {1 - v:.0%} vs. the prior 30 days"
        return "Usage stable or growing" if not risk and v >= 0.97 else None

    def events(v: float, risk: bool) -> str | None:
        return f"Key feature use down {1 - v:.0%} in 30 days" if risk and v < 0.9 else None

    def seats(v: float, risk: bool) -> str | None:
        if risk and v < 0.4:
            return f"Only {v:.0%} of purchased seats in use"
        return f"{v:.0%} of seats in use" if not risk and v >= 0.6 else None

    def tickets(v: float, risk: bool) -> str | None:
        return f"{_count(v, 'support ticket')} in the last 30 days" if risk and v >= 2 else None

    def trend(v: float, risk: bool) -> str | None:
        return f"Ticket volume up by {v:.1f} vs. the recent monthly average" \
            if risk and v >= 1 else None

    def severe(v: float, risk: bool) -> str | None:
        return f"{_count(v, 'severe ticket')} in the last 60 days" if risk and v > 0 else None

    def late(v: float, risk: bool) -> str | None:
        if risk and v >= 5:
            return f"Invoices paid {v:.0f} days late on average"
        return "Invoices paid on time" if not risk and v < 1 else None

    def overdue(v: float, risk: bool) -> str | None:
        return _count(v, "overdue invoice") if risk and v > 0 else None

    def champion(v: float, risk: bool) -> str | None:
        return "Champion has not been seen in over 45 days" if risk and v == 1 else None

    def renewal(v: float, risk: bool) -> str | None:
        return f"Renewal in {v:.0f} days" if risk and 0 <= v <= 120 else None

    return {
        "usage_trend_30d": usage, "events_trend_30d": events, "seat_utilization": seats,
        "tickets_30d": tickets, "ticket_trend": trend, "severe_tickets_60d": severe,
        "avg_days_late": late, "overdue_invoices": overdue, "champion_silent": champion,
        "days_to_renewal": renewal,
    }


DEAL_TEMPLATES = _deal_templates()
CHURN_TEMPLATES = _churn_templates()


def reasons_for_row(
    features: pd.Series,
    contributions: np.ndarray,
    columns: list[str],
    templates: dict[str, Template],
    risk_when_negative: bool,
    limit: int = 4,
) -> list[dict]:
    """Return the strongest explainable reasons for one record."""
    order = np.argsort(-np.abs(contributions))
    reasons: list[dict] = []
    for i in order:
        name = columns[i]
        template = templates.get(name)
        value = features[name]
        if template is None or pd.isna(value):
            continue
        impact = float(contributions[i])
        risk = impact < 0 if risk_when_negative else impact > 0
        text = template(float(value), risk)
        if text is None:
            continue
        reasons.append({
            "feature": name,
            "value": round(float(value), 3),
            "impact": round(impact, 4),
            "direction": "risk" if risk else "positive",
            "text": text,
        })
        if len(reasons) == limit:
            break
    return reasons


def explain_frame(
    model: object,
    frame: pd.DataFrame,
    columns: list[str],
    templates: dict[str, Template],
    risk_when_negative: bool,
) -> list[list[dict]]:
    values = shap_matrix(model, frame[columns])
    return [
        reasons_for_row(frame.iloc[i], values[i], columns, templates, risk_when_negative)
        for i in range(len(frame))
    ]
