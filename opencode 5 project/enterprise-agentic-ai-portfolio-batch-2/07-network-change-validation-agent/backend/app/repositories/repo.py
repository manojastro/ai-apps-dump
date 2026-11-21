"""Repositories: thin data-access layer over SQLAlchemy sessions."""
from __future__ import annotations

from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.entities import (
    ApprovalRec,
    AuditEvent,
    ChangeModel,
    DiffRecord,
    EvidenceRec,
    HypothesisRec,
    IntentResult,
    IntentTest,
    Investigation,
    KpiSnapshot,
    RcaRecord,
    Regression,
    SnapshotModel,
    ToolCallRec,
    ValidationRun,
)


class SnapshotRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def current(self) -> SnapshotModel | None:
        stmt = (
            select(SnapshotModel)
            .where(SnapshotModel.is_current.is_(True))
            .order_by(desc(SnapshotModel.id))
            .limit(1)
        )
        return self.session.scalar(stmt)

    def get(self, snapshot_id: int) -> SnapshotModel | None:
        return self.session.get(SnapshotModel, snapshot_id)

    def create(self, version: str, payload: dict[str, Any], is_current: bool = False,
               change_id: int | None = None, demote_current: bool = True) -> SnapshotModel:
        if is_current and demote_current:
            for row in self.session.scalars(
                select(SnapshotModel).where(SnapshotModel.is_current.is_(True))
            ):
                row.is_current = False
        snap = SnapshotModel(version=version, payload=payload, is_current=is_current,
                             change_id=change_id)
        self.session.add(snap)
        self.session.flush()
        return snap

    def previous_current(self, before_id: int) -> SnapshotModel | None:
        stmt = (
            select(SnapshotModel)
            .where(SnapshotModel.is_current.is_(False), SnapshotModel.id < before_id)
            .order_by(desc(SnapshotModel.id))
            .limit(1)
        )
        return self.session.scalar(stmt)


class ChangeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, change_id: int) -> ChangeModel | None:
        return self.session.get(ChangeModel, change_id)

    def list(self, limit: int = 50) -> list[ChangeModel]:
        stmt = select(ChangeModel).order_by(desc(ChangeModel.id)).limit(limit)
        return list(self.session.scalars(stmt))

    def create(self, title: str, config_diff: str, requested_by: str = "netops",
               fault_name: str | None = None) -> ChangeModel:
        change = ChangeModel(title=title, config_diff=config_diff,
                             requested_by=requested_by, fault_name=fault_name)
        self.session.add(change)
        self.session.flush()
        return change


class RunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def latest_for_change(self, change_id: int) -> ValidationRun | None:
        stmt = (
            select(ValidationRun)
            .where(ValidationRun.change_id == change_id)
            .order_by(desc(ValidationRun.id))
            .limit(1)
        )
        return self.session.scalar(stmt)

    def regressions_for_run(self, run_id: int) -> list[Regression]:
        stmt = select(Regression).where(Regression.run_id == run_id)
        return list(self.session.scalars(stmt))

    def intents_for_run(self, run_id: int) -> list[IntentResult]:
        stmt = select(IntentResult).where(IntentResult.run_id == run_id)
        return list(self.session.scalars(stmt))

    def investigations_for_run(self, run_id: int) -> list[Investigation]:
        stmt = select(Investigation).where(Investigation.run_id == run_id)
        return list(self.session.scalars(stmt))

    def count(self) -> int:
        return int(self.session.scalar(select(func.count(ValidationRun.id))) or 0)


class IntentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def all_enabled(self) -> list[IntentTest]:
        stmt = select(IntentTest).where(IntentTest.enabled.is_(True))
        return list(self.session.scalars(stmt))

    def upsert(self, name: str, itype: str, params: dict[str, Any],
               severity: str = "HIGH") -> IntentTest:
        existing = self.session.scalar(select(IntentTest).where(IntentTest.name == name))
        if existing:
            existing.itype = itype
            existing.params = params
            existing.severity = severity
            return existing
        row = IntentTest(name=name, itype=itype, params=params, severity=severity)
        self.session.add(row)
        self.session.flush()
        return row


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def event(self, entity: str, entity_id: int, action: str, actor: str = "system",
              detail: dict[str, Any] | None = None) -> AuditEvent:
        row = AuditEvent(entity=entity, entity_id=entity_id, action=action, actor=actor,
                         detail=detail or {})
        self.session.add(row)
        self.session.flush()
        return row

    def approval(self, change_id: int, actor: str, decision: str, comment: str,
                 from_status: str, to_status: str) -> ApprovalRec:
        row = ApprovalRec(change_id=change_id, actor=actor, decision=decision,
                          comment=comment, from_status=from_status, to_status=to_status)
        self.session.add(row)
        self.session.flush()
        return row

    def tool_call(self, tool: str, permission: str, input_json: dict[str, Any],
                  output_json: dict[str, Any], ok: bool, duration_ms: int,
                  error: str | None = None, change_id: int | None = None) -> ToolCallRec:
        row = ToolCallRec(tool=tool, permission=permission, input_json=input_json,
                          output_json=output_json, ok=ok, duration_ms=duration_ms,
                          error=error, change_id=change_id)
        self.session.add(row)
        self.session.flush()
        return row


class InvestigationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, run_id: int, agent: str, duration_ms: int,
               summary: dict[str, Any]) -> Investigation:
        row = Investigation(run_id=run_id, agent=agent, duration_ms=duration_ms,
                            summary=summary, status="completed")
        self.session.add(row)
        self.session.flush()
        return row

    def evidence(self, investigation_id: int, kind: str, source_agent: str,
                 content: dict[str, Any]) -> EvidenceRec:
        row = EvidenceRec(investigation_id=investigation_id, kind=kind,
                          source_agent=source_agent, content=content)
        self.session.add(row)
        return row

    def hypothesis(self, investigation_id: int, statement: str, status: str = "proposed",
                   score: float = 0.0, refuted_by: str | None = None) -> HypothesisRec:
        row = HypothesisRec(investigation_id=investigation_id, statement=statement,
                            status=status, score=score, refuted_by=refuted_by)
        self.session.add(row)
        return row

    def rca(self, run_id: int, incident_id: str, payload: dict[str, Any]) -> RcaRecord:
        row = RcaRecord(run_id=run_id, incident_id=incident_id, payload=payload)
        self.session.add(row)
        self.session.flush()
        return row


class DiffRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, change_id: int, raw_text: str, ops_json: list[dict[str, Any]]) -> DiffRecord:
        row = DiffRecord(change_id=change_id, raw_text=raw_text, ops_json=ops_json)
        self.session.add(row)
        self.session.flush()
        return row


class KpiRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, metrics: dict[str, Any], tag: str = "validation") -> KpiSnapshot:
        row = KpiSnapshot(tag=tag, metrics=metrics)
        self.session.add(row)
        self.session.flush()
        return row
