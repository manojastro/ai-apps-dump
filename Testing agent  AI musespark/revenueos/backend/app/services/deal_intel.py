"""Deal list sorted by risk, and per-deal explanations."""
from __future__ import annotations

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Account, Deal, Prediction, User
from app.services.predictions import WIN_MODEL, active_version, deal_band
from app.services.scope import Scope

SORTS = {"risk", "value_at_risk", "amount", "close_date"}


def _summary(deal: Deal, prediction: Prediction | None) -> dict:
    p = prediction.score if prediction is not None and deal.outcome is None else None
    amount = float(deal.amount)
    return {
        "id": deal.id, "name": deal.name, "account_id": deal.account_id,
        "account_name": deal.account.name, "owner_name": deal.owner.full_name
        if deal.owner else None, "team_id": deal.owner.team_id if deal.owner else None,
        "amount": amount, "stage": deal.stage, "type": deal.type,
        "created_at": deal.created_at, "close_date": deal.close_date,
        "closed_at": deal.closed_at, "outcome": deal.outcome,
        "discount_pct": deal.discount_pct,
        "p_win": round(p, 4) if p is not None else None,
        "risk_band": deal_band(p),
        "value_at_risk": round(amount * (1 - p), 2) if p is not None else None,
        "reasons": (prediction.reasons_json if p is not None else [])[:3],
        "cite": f"deals#{deal.id}",
    }


def list_deals(
    session: Session,
    scope: Scope,
    page: int,
    page_size: int,
    sort: str = "risk",
    open_only: bool = True,
    q: str | None = None,
    stage: str | None = None,
    deal_type: str | None = None,
    team_id: int | None = None,
    band: str | None = None,
    account_id: int | None = None,
) -> tuple[list[dict], int]:
    version = active_version(session, WIN_MODEL)
    join_on = and_(
        Prediction.entity_id == Deal.id,
        Prediction.model_name == WIN_MODEL,
        Prediction.model_version == (version.version if version else ""),
    )
    filters = [scope.deals()]
    if open_only:
        filters.append(Deal.outcome.is_(None))
    if q:
        like = f"%{q.strip()}%"
        filters.append(or_(Deal.name.ilike(like), Account.name.ilike(like)))
    if stage:
        filters.append(Deal.stage == stage)
    if deal_type:
        filters.append(Deal.type == deal_type)
    if account_id:
        filters.append(Deal.account_id == account_id)
    team = scope.effective_team(team_id)
    if team is not None:
        filters.append(Deal.owner_id.in_(select(User.id).where(User.team_id == team)))
    if band == "at_risk":
        filters.append(Prediction.score < 0.35)
    elif band == "watch":
        filters.append(and_(Prediction.score >= 0.35, Prediction.score < 0.6))
    elif band == "healthy":
        filters.append(Prediction.score >= 0.6)

    base = (select(Deal, Prediction).join(Account, Deal.account_id == Account.id)
            .outerjoin(Prediction, join_on).where(*filters))
    total = session.scalar(select(func.count()).select_from(base.subquery()))

    risk = func.coalesce(1 - Prediction.score, 0)
    order = {
        "risk": risk.desc(),
        "value_at_risk": (Deal.amount * risk).desc(),
        "amount": Deal.amount.desc(),
        "close_date": Deal.close_date.asc(),
    }[sort if sort in SORTS else "risk"]
    rows = session.execute(
        base.options(joinedload(Deal.account), joinedload(Deal.owner))
        .order_by(order, Deal.id).limit(page_size).offset((page - 1) * page_size)
    ).all()
    return [_summary(deal, prediction) for deal, prediction in rows], total or 0


def explain_deal(session: Session, scope: Scope, deal_id: int) -> dict | None:
    version = active_version(session, WIN_MODEL)
    deal = session.scalars(
        select(Deal).options(joinedload(Deal.account), joinedload(Deal.owner))
        .where(Deal.id == deal_id, scope.deals())
    ).first()
    if deal is None:
        return None
    prediction = None
    if version is not None:
        prediction = session.scalars(
            select(Prediction).where(
                Prediction.entity_id == deal_id, Prediction.model_name == WIN_MODEL,
                Prediction.model_version == version.version,
            )
        ).first()
    result = _summary(deal, prediction)
    result["reasons"] = prediction.reasons_json if prediction and deal.outcome is None else []
    result["model_version"] = version.version if version else None
    result["model_algorithm"] = version.algorithm if version else None
    result["prediction_cite"] = f"predictions#{prediction.id}" if prediction else None
    return result
