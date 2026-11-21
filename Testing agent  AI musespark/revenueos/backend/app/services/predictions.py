"""Read model scores from the active model version."""
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ModelVersion, Prediction

WIN_MODEL = "win_probability"
CHURN_MODEL = "churn_90d"


def active_version(session: Session, model_name: str) -> ModelVersion | None:
    return session.scalars(
        select(ModelVersion).where(
            ModelVersion.model_name == model_name, ModelVersion.is_active.is_(True)
        )
    ).first()


def scores(
    session: Session, model_name: str, entity_ids: Iterable[int] | None = None
) -> dict[int, Prediction]:
    version = active_version(session, model_name)
    if version is None:
        return {}
    query = select(Prediction).where(
        Prediction.model_name == model_name, Prediction.model_version == version.version
    )
    if entity_ids is not None:
        query = query.where(Prediction.entity_id.in_(list(entity_ids)))
    return {p.entity_id: p for p in session.scalars(query)}


def deal_band(p_win: float | None) -> str | None:
    if p_win is None:
        return None
    return "at_risk" if p_win < 0.35 else "watch" if p_win < 0.6 else "healthy"


def churn_band(p_churn: float | None) -> str | None:
    if p_churn is None:
        return None
    return "high" if p_churn >= 0.35 else "medium" if p_churn >= 0.15 else "low"
