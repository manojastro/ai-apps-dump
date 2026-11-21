"""Churn risk views and rule-based expansion triggers."""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.db.models import Account, Subscription, UsageDaily
from app.services.predictions import CHURN_MODEL, churn_band, scores
from app.services.scope import Scope

SEAT_LIMIT_TRIGGER = 0.85
GROWTH_TRIGGER = 0.15


def _risk_rows(session: Session, scope: Scope) -> list[dict]:
    predictions = scores(session, CHURN_MODEL)
    accounts = session.scalars(
        select(Account).options(joinedload(Account.owner)).where(
            scope.accounts(), Account.id.in_(list(predictions)), Account.status == "active"
        )
    ).all()
    renewals = dict(session.execute(
        select(Subscription.account_id, func.max(Subscription.renewal_date))
        .where(Subscription.status == "active").group_by(Subscription.account_id)
    ).all())
    rows = []
    for a in accounts:
        prediction = predictions[a.id]
        rows.append({
            "account_id": a.id, "name": a.name, "segment": a.segment, "region": a.region,
            "owner_name": a.owner.full_name if a.owner else None, "arr": float(a.arr),
            "p_churn": round(prediction.score, 4), "band": churn_band(prediction.score),
            "expected_arr_loss": round(float(a.arr) * prediction.score, 2),
            "renewal_date": renewals.get(a.id),
            "reasons": prediction.reasons_json[:3],
            "cite": f"accounts#{a.id}", "prediction_cite": f"predictions#{prediction.id}",
        })
    rows.sort(key=lambda r: r["expected_arr_loss"], reverse=True)
    return rows


def list_at_risk(
    session: Session, scope: Scope, page: int, page_size: int, band: str | None = None
) -> tuple[list[dict], int]:
    rows = _risk_rows(session, scope)
    if band:
        rows = [r for r in rows if r["band"] == band]
    start = (page - 1) * page_size
    return rows[start:start + page_size], len(rows)


def summary(session: Session, scope: Scope) -> dict:
    """Totals, with the account list behind them, so every figure is traceable."""
    rows = _risk_rows(session, scope)
    high = [r for r in rows if r["band"] == "high"]
    medium = [r for r in rows if r["band"] == "medium"]
    return {
        "as_of": get_settings().data_as_of,
        "scored_accounts": len(rows),
        "total_arr": round(sum(r["arr"] for r in rows), 2),
        "at_risk_arr": round(sum(r["arr"] for r in high), 2),
        "at_risk_accounts": len(high),
        "watch_arr": round(sum(r["arr"] for r in medium), 2),
        "watch_accounts": len(medium),
        "expected_arr_loss": round(sum(r["expected_arr_loss"] for r in rows), 2),
        "at_risk_account_ids": [r["account_id"] for r in high],
    }


def explain_churn(session: Session, scope: Scope, account_id: int) -> dict | None:
    account = session.scalars(
        select(Account).where(Account.id == account_id, scope.accounts())
    ).first()
    if account is None:
        return None
    prediction = scores(session, CHURN_MODEL, [account_id]).get(account_id)
    return {
        "account_id": account.id, "name": account.name, "arr": float(account.arr),
        "status": account.status,
        "p_churn": round(prediction.score, 4) if prediction else None,
        "band": churn_band(prediction.score) if prediction else None,
        "reasons": prediction.reasons_json if prediction else [],
        "cite": f"accounts#{account.id}",
    }


def expansion_candidates(session: Session, scope: Scope) -> list[dict]:
    """Rule-based triggers: usage near the seat limit, or fast team growth."""
    today = get_settings().data_as_of
    recent_from = today - timedelta(days=30)
    prior_from = today - timedelta(days=90)
    prior_to = today - timedelta(days=60)
    weekday = func.extract("isodow", UsageDaily.date) < 6
    recent = func.avg(case((UsageDaily.date > recent_from, UsageDaily.active_users)))
    prior = func.avg(case(
        ((UsageDaily.date > prior_from) & (UsageDaily.date <= prior_to), UsageDaily.active_users)
    ))
    seats = func.max(case((UsageDaily.date > recent_from, UsageDaily.seats_purchased)))
    rows = session.execute(
        select(Account, recent, prior, seats)
        .join(UsageDaily, UsageDaily.account_id == Account.id)
        .where(scope.accounts(), Account.status == "active", weekday,
               UsageDaily.date > prior_from)
        .group_by(Account.id)
    ).all()
    results = []
    for account, recent_users, prior_users, seat_count in rows:
        if not recent_users or not seat_count:
            continue
        utilization = float(recent_users) / float(seat_count)
        growth = float(recent_users) / float(prior_users) - 1 if prior_users else 0.0
        triggers = []
        if utilization >= SEAT_LIMIT_TRIGGER:
            triggers.append(f"Usage near seat limit: {utilization:.0%} of {seat_count} seats")
        if growth >= GROWTH_TRIGGER:
            triggers.append(f"Team growth: active users up {growth:.0%} in 60 days")
        if triggers:
            results.append({
                "account_id": account.id, "name": account.name, "arr": float(account.arr),
                "seat_utilization": round(utilization, 3), "user_growth": round(growth, 3),
                "seats": int(seat_count), "triggers": triggers, "cite": f"accounts#{account.id}",
            })
    results.sort(key=lambda r: r["arr"], reverse=True)
    return results
