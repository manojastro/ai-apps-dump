"""Data access helpers for monitoring windows and evaluation results."""
from __future__ import annotations

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.entities import (
    CanaryResult,
    CandidateEvaluation,
    DataQualityCheck,
    DeploymentRisk,
    DriftResult,
    FairnessResult,
    MonitoringWindow,
    PerformanceResult,
    PredictionStat,
    ShadowComparison,
)


def add_and_commit(session: Session, row: object) -> object:
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def add_many(session: Session, rows: list[object]) -> list[object]:
    session.add_all(rows)
    session.commit()
    return rows


class WindowRepository:
    """Persistence for monitoring windows."""

    @staticmethod
    def create(session: Session, **kwargs: object) -> MonitoringWindow:
        return add_and_commit(session, MonitoringWindow(**kwargs))  # type: ignore[arg-type]

    @staticmethod
    def get(session: Session, window_id: int) -> MonitoringWindow | None:
        return session.get(MonitoringWindow, window_id)

    @staticmethod
    def latest(session: Session, evaluated_only: bool = True) -> MonitoringWindow | None:
        stmt = select(MonitoringWindow).order_by(MonitoringWindow.id.desc())
        if evaluated_only:
            stmt = stmt.where(MonitoringWindow.evaluated.is_(True))
        return session.scalar(stmt.limit(1))

    @staticmethod
    def latest_with_alert(session: Session) -> MonitoringWindow | None:
        stmt = (
            select(MonitoringWindow)
            .where(MonitoringWindow.alert.is_(True))
            .order_by(MonitoringWindow.id.desc())
        )
        return session.scalar(stmt.limit(1))

    @staticmethod
    def list_all(session: Session) -> list[MonitoringWindow]:
        return list(session.scalars(select(MonitoringWindow).order_by(MonitoringWindow.id)))

    @staticmethod
    def load_frame(window: MonitoringWindow) -> pd.DataFrame:
        return pd.read_csv(window.data_path)

    @staticmethod
    def mark_evaluated(session: Session, window: MonitoringWindow, alert: bool) -> None:
        window.evaluated = True
        window.alert = alert
        session.commit()


class ResultsRepository:
    """Persistence for all per-window measurement rows."""

    @staticmethod
    def save_drift_results(
        session: Session, rows: list[DriftResult]
    ) -> list[DriftResult]:
        return list(add_many(session, rows))

    @staticmethod
    def drift_for_window(session: Session, window_id: int) -> list[DriftResult]:
        return list(
            session.scalars(
                select(DriftResult).where(DriftResult.window_id == window_id)
            )
        )

    @staticmethod
    def save_prediction_stat(session: Session, row: PredictionStat) -> PredictionStat:
        return add_and_commit(session, row)  # type: ignore[arg-type]

    @staticmethod
    def prediction_stat_for_window(
        session: Session, window_id: int
    ) -> PredictionStat | None:
        return session.scalar(
            select(PredictionStat)
            .where(PredictionStat.window_id == window_id)
            .order_by(PredictionStat.id.desc())
            .limit(1)
        )

    @staticmethod
    def save_performance(session: Session, row: PerformanceResult) -> PerformanceResult:
        return add_and_commit(session, row)  # type: ignore[arg-type]

    @staticmethod
    def performance_for_window(
        session: Session, window_id: int
    ) -> PerformanceResult | None:
        return session.scalar(
            select(PerformanceResult)
            .where(PerformanceResult.window_id == window_id)
            .order_by(PerformanceResult.id.desc())
            .limit(1)
        )

    @staticmethod
    def performance_history(session: Session) -> list[PerformanceResult]:
        return list(
            session.scalars(select(PerformanceResult).order_by(PerformanceResult.id))
        )

    @staticmethod
    def save_quality_checks(
        session: Session, rows: list[DataQualityCheck]
    ) -> list[DataQualityCheck]:
        return list(add_many(session, rows))

    @staticmethod
    def quality_for_window(session: Session, window_id: int) -> list[DataQualityCheck]:
        return list(
            session.scalars(
                select(DataQualityCheck).where(DataQualityCheck.window_id == window_id)
            )
        )

    @staticmethod
    def save_fairness(session: Session, row: FairnessResult) -> FairnessResult:
        return add_and_commit(session, row)  # type: ignore[arg-type]

    @staticmethod
    def fairness_for_window(session: Session, window_id: int) -> FairnessResult | None:
        return session.scalar(
            select(FairnessResult)
            .where(FairnessResult.window_id == window_id)
            .order_by(FairnessResult.id.desc())
            .limit(1)
        )


class CandidateRepository:
    """Persistence for candidate evaluations, risks, shadow and canary results."""

    @staticmethod
    def save_evaluation(
        session: Session, row: CandidateEvaluation
    ) -> CandidateEvaluation:
        return add_and_commit(session, row)  # type: ignore[arg-type]

    @staticmethod
    def latest_evaluation(
        session: Session, version: str
    ) -> CandidateEvaluation | None:
        return session.scalar(
            select(CandidateEvaluation)
            .where(CandidateEvaluation.version == version)
            .order_by(CandidateEvaluation.id.desc())
            .limit(1)
        )

    @staticmethod
    def list_evaluations(session: Session) -> list[CandidateEvaluation]:
        return list(
            session.scalars(
                select(CandidateEvaluation).order_by(CandidateEvaluation.id.desc())
            )
        )

    @staticmethod
    def save_risk(session: Session, row: DeploymentRisk) -> DeploymentRisk:
        return add_and_commit(session, row)  # type: ignore[arg-type]

    @staticmethod
    def latest_risk(session: Session, version: str) -> DeploymentRisk | None:
        return session.scalar(
            select(DeploymentRisk)
            .where(DeploymentRisk.version == version)
            .order_by(DeploymentRisk.id.desc())
            .limit(1)
        )

    @staticmethod
    def save_shadow(session: Session, row: ShadowComparison) -> ShadowComparison:
        return add_and_commit(session, row)  # type: ignore[arg-type]

    @staticmethod
    def latest_shadow(session: Session, version: str) -> ShadowComparison | None:
        return session.scalar(
            select(ShadowComparison)
            .where(ShadowComparison.version == version)
            .order_by(ShadowComparison.id.desc())
            .limit(1)
        )

    @staticmethod
    def list_shadow(session: Session) -> list[ShadowComparison]:
        return list(
            session.scalars(
                select(ShadowComparison).order_by(ShadowComparison.id.desc())
            )
        )

    @staticmethod
    def save_canary(session: Session, row: CanaryResult) -> CanaryResult:
        return add_and_commit(session, row)  # type: ignore[arg-type]

    @staticmethod
    def latest_canary(session: Session, version: str) -> CanaryResult | None:
        return session.scalar(
            select(CanaryResult)
            .where(CanaryResult.version == version)
            .order_by(CanaryResult.id.desc())
            .limit(1)
        )
