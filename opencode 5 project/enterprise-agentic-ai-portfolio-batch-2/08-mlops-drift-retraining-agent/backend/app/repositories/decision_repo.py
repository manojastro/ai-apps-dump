"""Data access helpers for decisions, investigations, promotions and audit."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.entities import (
    ApprovalRecord,
    EvidenceItem,
    Hypothesis,
    Investigation,
    KpiSnapshot,
    Promotion,
    RejectedHypothesis,
    RetrainingDecision,
    RollbackRecord,
    ToolCall,
    TrainingRun,
)


class DecisionRepository:
    """Persistence for retraining gate decisions."""

    @staticmethod
    def save(session: Session, row: RetrainingDecision) -> RetrainingDecision:
        session.add(row)
        session.commit()
        session.refresh(row)
        return row

    @staticmethod
    def for_window(session: Session, window_id: int) -> list[RetrainingDecision]:
        return list(
            session.scalars(
                select(RetrainingDecision)
                .where(RetrainingDecision.window_id == window_id)
                .order_by(RetrainingDecision.id.desc())
            )
        )

    @staticmethod
    def latest(session: Session, limit: int = 50) -> list[RetrainingDecision]:
        return list(
            session.scalars(
                select(RetrainingDecision).order_by(RetrainingDecision.id.desc()).limit(limit)
            )
        )


class TrainingRunRepository:
    """Persistence for training runs."""

    @staticmethod
    def save(session: Session, row: TrainingRun) -> TrainingRun:
        session.add(row)
        session.commit()
        session.refresh(row)
        return row

    @staticmethod
    def latest_for_version(session: Session, version: str) -> TrainingRun | None:
        return session.scalar(
            select(TrainingRun)
            .where(TrainingRun.version == version)
            .order_by(TrainingRun.id.desc())
            .limit(1)
        )

    @staticmethod
    def count_candidates(session: Session) -> int:
        rows = session.scalars(select(TrainingRun).where(TrainingRun.kind == "candidate"))
        return len(list(rows))


class InvestigationRepository:
    """Persistence for investigations with evidence and hypotheses."""

    @staticmethod
    def save_investigation(session: Session, row: Investigation) -> Investigation:
        session.add(row)
        session.commit()
        session.refresh(row)
        return row

    @staticmethod
    def add_evidence(session: Session, rows: list[EvidenceItem]) -> list[EvidenceItem]:
        session.add_all(rows)
        session.commit()
        return rows

    @staticmethod
    def add_hypotheses(session: Session, rows: list[Hypothesis]) -> list[Hypothesis]:
        session.add_all(rows)
        session.commit()
        return rows

    @staticmethod
    def add_rejected(session: Session, rows: list[RejectedHypothesis]) -> list[RejectedHypothesis]:
        session.add_all(rows)
        session.commit()
        return rows

    @staticmethod
    def for_window(session: Session, window_id: int) -> Investigation | None:
        return session.scalar(
            select(Investigation)
            .where(Investigation.window_id == window_id)
            .order_by(Investigation.id.desc())
            .limit(1)
        )

    @staticmethod
    def latest(session: Session) -> Investigation | None:
        return session.scalar(
            select(Investigation).order_by(Investigation.id.desc()).limit(1)
        )


class PromotionRepository:
    """Persistence for the approval state machine."""

    @staticmethod
    def create(session: Session, row: Promotion) -> Promotion:
        session.add(row)
        session.commit()
        session.refresh(row)
        return row

    @staticmethod
    def get(session: Session, promotion_id: int) -> Promotion | None:
        return session.get(Promotion, promotion_id)

    @staticmethod
    def update(session: Session, promotion: Promotion) -> Promotion:
        promotion.updated_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(promotion)
        return promotion

    @staticmethod
    def list_all(session: Session) -> list[Promotion]:
        return list(session.scalars(select(Promotion).order_by(Promotion.id.desc())))

    @staticmethod
    def add_approval(session: Session, row: ApprovalRecord) -> ApprovalRecord:
        session.add(row)
        session.commit()
        session.refresh(row)
        return row


class RollbackRepository:
    """Persistence for rollback history."""

    @staticmethod
    def save(session: Session, row: RollbackRecord) -> RollbackRecord:
        session.add(row)
        session.commit()
        session.refresh(row)
        return row

    @staticmethod
    def list_all(session: Session) -> list[RollbackRecord]:
        return list(session.scalars(select(RollbackRecord).order_by(RollbackRecord.id.desc())))


class AuditRepository:
    """Persistence for tool call audit entries."""

    @staticmethod
    def record(session: Session, row: ToolCall) -> ToolCall:
        session.add(row)
        session.commit()
        session.refresh(row)
        return row

    @staticmethod
    def list_recent(session: Session, limit: int = 100) -> list[ToolCall]:
        return list(
            session.scalars(select(ToolCall).order_by(ToolCall.id.desc()).limit(limit))
        )


class KpiRepository:
    """Persistence for KPI snapshots."""

    @staticmethod
    def save(session: Session, payload: dict) -> KpiSnapshot:
        row = KpiSnapshot(payload=payload)
        session.add(row)
        session.commit()
        session.refresh(row)
        return row

    @staticmethod
    def latest(session: Session) -> KpiSnapshot | None:
        return session.scalar(select(KpiSnapshot).order_by(KpiSnapshot.id.desc()).limit(1))
