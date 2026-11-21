from __future__ import annotations

import json
import hashlib
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4

from .schemas import ProposedAction, RCAResult, ValidationResult, utc_now


REDACT_KEYS = {"api_key", "authorization", "password", "secret", "token"}


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if key.lower() in REDACT_KEYS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def canonical_payload(action: ProposedAction | dict[str, Any] | str) -> tuple[str, str]:
    if isinstance(action, ProposedAction):
        value = action.model_dump(mode="json")
    elif isinstance(action, str):
        value = json.loads(action)
    else:
        value = action
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return encoded, hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def migrate(self) -> None:
        migration_dir = Path(__file__).with_name("migrations")
        with self.connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
            )
            applied = {
                row["version"]
                for row in connection.execute("SELECT version FROM schema_migrations")
            }
            for path in sorted(migration_dir.glob("*.sql")):
                version = int(path.stem.split("_", 1)[0])
                if version not in applied:
                    connection.executescript(path.read_text(encoding="utf-8"))
                    connection.execute(
                        "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                        (version, utc_now()),
                    )
            self._repair_legacy_approval_bindings(connection)

    @staticmethod
    def _repair_legacy_approval_bindings(connection: sqlite3.Connection) -> None:
        """Prepare invalidated v1 actions for a new, exact payload-bound approval."""
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(actions)").fetchall()
        }
        if "payload_hash" not in columns:
            return
        rows = connection.execute(
            "SELECT action_id,payload_json FROM actions WHERE payload_hash=''"
        ).fetchall()
        for row in rows:
            try:
                payload = ProposedAction.model_validate_json(row["payload_json"])
                encoded, digest = canonical_payload(payload)
            except Exception:
                continue
            connection.execute(
                "UPDATE actions SET payload_json=?,payload_version=?,payload_hash=?,updated_at=? WHERE action_id=?",
                (encoded, payload.payload_version, digest, utc_now(), row["action_id"]),
            )

    def ping(self) -> bool:
        try:
            with self.connect() as connection:
                return connection.execute("SELECT 1").fetchone()[0] == 1
        except sqlite3.Error:
            return False

    def insert_run(
        self, trace: dict[str, Any], status: str,
        observed_started_at: str, verification_deadline: str,
    ) -> None:
        latency = sum(step["latency_ms"] for step in trace["steps"])
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO agent_runs
                (run_id, agent_id, agent_version, scenario, status, started_at,
                 completed_at, total_cost_usd, latency_ms, trace_json, created_at,
                 observed_started_at, verification_deadline)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    trace["run_id"], trace["agent_id"], trace["agent_version"],
                    trace["scenario"], status, trace["started_at"], trace["completed_at"],
                    trace["total_cost_usd"], latency,
                    json.dumps(redact(trace), separators=(",", ":")), utc_now(),
                    observed_started_at, verification_deadline,
                ),
            )

    def insert_incident(
        self, incident_id: str, run_id: str, severity: str,
        title: str, detections: list[dict[str, Any]], rca: RCAResult,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO incidents
                (incident_id, run_id, severity, status, title, root_cause,
                 confidence, detections_json, rca_json, created_at)
                VALUES (?, ?, ?, 'OPEN', ?, ?, ?, ?, ?, ?)""",
                (incident_id, run_id, severity, title, rca.probable_root_cause,
                 rca.confidence, json.dumps(detections), rca.model_dump_json(), utc_now()),
            )
            connection.executemany(
                """INSERT INTO evidence
                (evidence_id, incident_id, source, fact, value_json, observed_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                [
                    (e.evidence_id, incident_id, e.source, e.fact,
                     json.dumps(e.value), e.observed_at)
                    for e in rca.evidence
                ],
            )

    def insert_action(self, action: ProposedAction) -> None:
        now = utc_now()
        payload, payload_hash = canonical_payload(action)
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO actions
                (action_id, incident_id, action_type, risk, required_approval,
                 status, payload_json, payload_version, payload_hash, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (action.action_id, action.incident_id, action.action_type,
                  action.risk.value, int(action.required_approval), action.status,
                  payload, action.payload_version, payload_hash, now, now),
            )

    def insert_validation(self, result: ValidationResult, action_id: str | None = None) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO validations
                (validation_id, incident_id, action_id, stage, passed, result_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (result.validation_id, result.incident_id, action_id, result.stage,
                 int(result.passed), result.model_dump_json(), result.created_at),
            )

    def audit(
        self, *, incident_id: str | None, agent: str, tool: str, action: str,
        input_data: Any, output_data: Any, evidence: Any = None,
        decision: str = "", approval: str = "", execution_result: str = "",
        validation_result: str = "",
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO audit_events
                (event_id, timestamp, project, incident_id, agent, tool, action,
                 input_json, output_json, evidence_json, decision, approval,
                 execution_result, validation_result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f"evt_{uuid4().hex[:16]}", utc_now(), "agent-reliability-platform",
                 incident_id, agent, tool, action,
                 json.dumps(redact(input_data), default=str),
                 json.dumps(redact(output_data), default=str),
                 json.dumps(redact(evidence or []), default=str),
                 decision, approval, execution_result, validation_result),
            )

    def query_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self.connect() as connection:
            return [dict(row) for row in connection.execute(sql, params).fetchall()]

    def query_one(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(sql, params).fetchone()
            return dict(row) if row else None

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        with self.connect() as connection:
            connection.execute(sql, params)
