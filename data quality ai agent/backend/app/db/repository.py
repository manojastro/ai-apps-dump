from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import (
    ApprovalRow,
    AttemptRow,
    AuditRow,
    Base,
    EvaluationRow,
    EventRow,
    EvidenceRow,
    HypothesisRow,
    IncidentRow,
    ValidationRow,
    VerificationRow,
)
from app.graph.state import RecoveryState
from app.models.domain import Incident, Status, now
from app.observability.metrics import state_metrics

RELATED: dict[
    str,
    type[EvidenceRow]
    | type[HypothesisRow]
    | type[AttemptRow]
    | type[ValidationRow]
    | type[VerificationRow]
    | type[ApprovalRow]
    | type[AuditRow],
] = {
    "evidence": EvidenceRow,
    "hypotheses": HypothesisRow,
    "attempts": AttemptRow,
    "validations": ValidationRow,
    "verifications": VerificationRow,
    "approvals": ApprovalRow,
    "audit": AuditRow,
}


def record(row: Base) -> dict[str, Any]:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


class Repository:
    def __init__(self, settings: Settings):
        self.settings = settings
        settings.prepare_paths()
        options = (
            {"connect_args": {"check_same_thread": False, "timeout": 30}}
            if (settings.database_url.startswith("sqlite"))
            else {}
        )
        self.engine = create_engine(settings.database_url, **options)
        if self.engine.dialect.name == "sqlite":

            @event.listens_for(self.engine, "connect")
            def sqlite_pragmas(connection, _):
                connection.execute("PRAGMA foreign_keys=ON")
                connection.execute("PRAGMA journal_mode=WAL")

    def migrate(self) -> None:
        root = Path(__file__).resolve().parents[3]
        config = Config(str(root / "alembic.ini"))
        config.set_main_option("script_location", str(root / "backend" / "migrations"))
        config.attributes["database_url"] = self.settings.database_url
        command.upgrade(config, "head")

    def close(self) -> None:
        self.engine.dispose()

    def create(self, incident: Incident) -> dict[str, Any]:
        with Session(self.engine) as session, session.begin():
            row = IncidentRow(
                id=incident.id,
                title=incident.title,
                pipeline_id=incident.pipeline_id,
                environment=incident.environment,
                scenario=incident.scenario,
                status=Status.CREATED,
                created_at=incident.created_at,
                updated_at=now(),
                input=incident.model_dump(mode="json"),
            )
            session.add(row)
        self.event(
            incident.id, "incident_created", "intake", {"triggered_by": incident.triggered_by}
        )
        return self.get(incident.id)

    def get(self, incident_id: str) -> dict[str, Any]:
        with Session(self.engine) as session:
            row = session.get(IncidentRow, incident_id)
            if row is None:
                raise KeyError(incident_id)
            return record(row)

    def list_incidents(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        with Session(self.engine) as session:
            return [
                record(r)
                for r in session.scalars(
                    select(IncidentRow)
                    .order_by(IncidentRow.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
            ]

    def status(self, incident_id: str, status: Status, reason: str = "") -> None:
        with Session(self.engine) as session, session.begin():
            row = session.get(IncidentRow, incident_id)
            if row is None:
                raise KeyError(incident_id)
            row.status, row.updated_at, row.failure_reason = status, now(), reason

    def event(self, incident_id: str, kind: str, node: str, payload: dict[str, Any]) -> None:
        timestamp = now()
        with Session(self.engine) as session, session.begin():
            session.add(
                EventRow(
                    incident_id=incident_id,
                    kind=kind,
                    node=node,
                    timestamp=timestamp,
                    payload=payload,
                )
            )
            session.add(
                AuditRow(
                    incident_id=incident_id,
                    kind=kind,
                    tool=node,
                    timestamp=timestamp,
                    payload=payload,
                )
            )
            if kind == "node_started":
                row = session.get(IncidentRow, incident_id)
                if row:
                    row.current_stage, row.updated_at = node, timestamp

    def project(self, state: RecoveryState) -> None:
        """Idempotent relational projection; checkpoints separately retain execution state."""
        incident_id = state["incident_id"]
        with Session(self.engine) as session, session.begin():
            row = session.get(IncidentRow, incident_id)
            if row is None:
                raise KeyError(incident_id)
            row.status = state.get("final_status", Status.RUNNING)
            row.attempt_count = state.get("attempt_number", 0)
            row.artifact = state.get("final_remediation")
            row.updated_at = now()
            row.failure_reason = state.get("failure_reason", "")
            row.metrics = state_metrics(state)
            for item in state.get("aggregated_evidence", []):
                session.merge(EvidenceRow(incident_id=incident_id, **item.model_dump(mode="json")))
            for hypothesis in state.get("root_cause_hypotheses", []):
                session.merge(
                    HypothesisRow(incident_id=incident_id, **hypothesis.model_dump(mode="json"))
                )
            for attempt in state.get("attempt_history", []):
                session.merge(
                    AttemptRow(
                        incident_id=incident_id,
                        number=attempt.number,
                        candidate=attempt.candidate.model_dump(mode="json"),
                        status=attempt.status,
                        feedback=attempt.feedback,
                    )
                )
                for check in attempt.validations:
                    session.merge(
                        ValidationRow(
                            incident_id=incident_id,
                            attempt=attempt.number,
                            **check.model_dump(mode="json"),
                        )
                    )
            if state.get("verification_result"):
                session.merge(
                    VerificationRow(
                        incident_id=incident_id,
                        **state["verification_result"].model_dump(mode="json"),
                    )
                )
            if state.get("human_decision"):
                existing = session.get(ApprovalRow, incident_id)
                if existing is None:
                    session.add(
                        ApprovalRow(
                            incident_id=incident_id, decided_at=now(), **state["human_decision"]
                        )
                    )

    def related(self, incident_id: str, kind: str) -> list[dict[str, Any]]:
        model = RELATED[kind]
        with Session(self.engine) as session:
            return [
                record(r)
                for r in session.scalars(
                    select(model).where(model.incident_id == incident_id).limit(1000)
                )
            ]

    def events(self, incident_id: str, after: int = 0) -> list[dict[str, Any]]:
        with Session(self.engine) as session:
            return [
                record(r)
                for r in session.scalars(
                    select(EventRow)
                    .where(EventRow.incident_id == incident_id, EventRow.id > after)
                    .order_by(EventRow.id)
                    .limit(500)
                )
            ]

    def summary(self) -> dict[str, Any]:
        with Session(self.engine) as session:
            statuses = {
                status: count
                for status, count in (
                    session.execute(
                        select(IncidentRow.status, func.count()).group_by(IncidentRow.status)
                    ).all()
                )
            }
            attempts = {
                status: count
                for status, count in (
                    session.execute(
                        select(AttemptRow.status, func.count()).group_by(AttemptRow.status)
                    ).all()
                )
            }
            evaluation = session.scalar(
                select(EvaluationRow).order_by(EvaluationRow.created_at.desc())
            )
            total = sum(statuses.values())
            terminal = sum(statuses.get(s, 0) for s in ("COMPLETED", "FAILED", "REJECTED"))
            return {
                "total_incidents": total,
                "statuses": statuses,
                "attempts": attempts,
                "terminal_incidents": terminal,
                "active_incidents": total - terminal,
                "recovery_success_rate": statuses.get("COMPLETED", 0) / terminal if terminal else 0,
                "validator_rejection_rate": attempts.get("REJECTED", 0) / sum(attempts.values())
                if attempts
                else 0,
                "evaluation": record(evaluation) if evaluation else None,
            }
