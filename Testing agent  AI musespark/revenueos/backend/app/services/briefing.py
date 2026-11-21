"""Per-user daily brief, built from models and rules with no LLM.

Why no LLM here: the brief is a scheduled list of facts, so it stays free, repeatable
and cannot hallucinate. Nothing is emailed. It is only shown on the dashboard.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import DailyBrief, User
from app.services import deal_intel, forecast, retention
from app.services.scope import Scope


def scope_for(user: User) -> Scope:
    return Scope(user_id=user.id, role=user.role, team_id=user.team_id)


def build_content(session: Session, scope: Scope) -> dict:
    deals, _ = deal_intel.list_deals(session, scope, 1, 5, sort="value_at_risk")
    accounts, _ = retention.list_at_risk(session, scope, 1, 5)
    changes = forecast.get_changes(session, scope)
    current = forecast.get_forecast(session, scope)
    return {
        "forecast": {
            "quarter": current["quarter"], "low": current["low"],
            "expected": current["expected"], "high": current["high"],
            "cite": current["cite"],
        },
        "forecast_change": {
            "total_change": changes.get("total_change"),
            "categories": changes.get("categories", {}),
            "top_items": changes.get("items", [])[:3],
        },
        "top_risks": [{
            "deal_id": d["id"], "name": d["name"], "amount": d["amount"], "p_win": d["p_win"],
            "value_at_risk": d["value_at_risk"],
            "reason": d["reasons"][0]["text"] if d["reasons"] else None, "cite": d["cite"],
        } for d in deals],
        "accounts_needing_attention": [{
            "account_id": a["account_id"], "name": a["name"], "arr": a["arr"],
            "p_churn": a["p_churn"],
            "reason": a["reasons"][0]["text"] if a["reasons"] else None, "cite": a["cite"],
        } for a in accounts],
    }


def generate_all(session: Session, brief_date: date | None = None) -> int:
    """Create or refresh today's brief for every user. Re-running replaces, never stacks."""
    brief_date = brief_date or get_settings().data_as_of
    users = session.scalars(select(User)).all()
    for user in users:
        content = build_content(session, scope_for(user))
        session.query(DailyBrief).filter_by(user_id=user.id, brief_date=brief_date).delete()
        session.add(DailyBrief(
            user_id=user.id, brief_date=brief_date,
            content_json=_json_safe(content),
        ))
    session.commit()
    return len(users)


def _json_safe(value):
    import json

    return json.loads(json.dumps(value, default=str))


def latest_for(session: Session, user_id: int) -> DailyBrief | None:
    return session.scalars(
        select(DailyBrief).where(DailyBrief.user_id == user_id)
        .order_by(DailyBrief.brief_date.desc())
    ).first()
