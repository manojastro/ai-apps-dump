from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS incidents (
    incident_id TEXT PRIMARY KEY,
    scenario TEXT NOT NULL,
    status TEXT NOT NULL,
    ground_truth TEXT NOT NULL,
    predicted_root_cause TEXT NOT NULL,
    confidence REAL NOT NULL,
    diagnosis_ms REAL NOT NULL,
    snapshot_json TEXT NOT NULL,
    rca_json TEXT NOT NULL,
    failure_started_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT NOT NULL,
    approved INTEGER NOT NULL,
    approved_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(incident_id) REFERENCES incidents(incident_id)
);
CREATE TABLE IF NOT EXISTS executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT NOT NULL,
    action_id TEXT NOT NULL,
    adapter TEXT NOT NULL,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(incident_id) REFERENCES incidents(incident_id)
);
CREATE TABLE IF NOT EXISTS validations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT NOT NULL,
    passed INTEGER NOT NULL,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(incident_id) REFERENCES incidents(incident_id)
);
CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT NOT NULL,
    true_root_cause TEXT NOT NULL,
    predicted_root_cause TEXT NOT NULL,
    correct INTEGER NOT NULL,
    confidence REAL NOT NULL,
    diagnosis_ms REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(incident_id) REFERENCES incidents(incident_id)
);
CREATE TABLE IF NOT EXISTS audit_log (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    incident_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    tool TEXT NOT NULL,
    action TEXT NOT NULL,
    input_json TEXT NOT NULL,
    output_json TEXT NOT NULL,
    decision TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_approval_per_incident ON approvals(incident_id);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Repository:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path, timeout=10)
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

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            connection.execute(
                "INSERT OR IGNORE INTO schema_migrations (version, description, applied_at) VALUES (?, ?, ?)",
                (1, "initial incident, approval, execution, validation, evaluation, and audit schema", now_iso()),
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(incidents)").fetchall()}
            if "failure_started_at" not in columns:
                connection.execute("ALTER TABLE incidents ADD COLUMN failure_started_at TEXT")
                connection.execute("UPDATE incidents SET failure_started_at = created_at WHERE failure_started_at IS NULL")
            connection.execute(
                "INSERT OR IGNORE INTO schema_migrations (version, description, applied_at) VALUES (?, ?, ?)",
                (2, "add simulated failure start time for MTTD and MTTR evaluation", now_iso()),
            )

    def create_incident(self, record: dict[str, Any]) -> None:
        timestamp = now_iso()
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO incidents
                (incident_id, scenario, status, ground_truth, predicted_root_cause, confidence,
                 diagnosis_ms, snapshot_json, rca_json, failure_started_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (record["incident_id"], record["scenario"], record["status"], record["ground_truth"],
                 record["predicted_root_cause"], record["confidence"], record["diagnosis_ms"],
                 json.dumps(record["snapshot"]), json.dumps(record["rca"]), record["failure_started_at"],
                 timestamp, timestamp),
            )
            connection.execute(
                """INSERT INTO evaluations
                (incident_id, true_root_cause, predicted_root_cause, correct, confidence, diagnosis_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (record["incident_id"], record["ground_truth"], record["predicted_root_cause"],
                 int(record["ground_truth"] == record["predicted_root_cause"]), record["confidence"],
                 record["diagnosis_ms"], timestamp),
            )

    def update_status(self, incident_id: str, status: str) -> None:
        with self.connect() as connection:
            cursor = connection.execute(
                "UPDATE incidents SET status = ?, updated_at = ? WHERE incident_id = ?",
                (status, now_iso(), incident_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(incident_id)

    def transition_status(self, incident_id: str, expected: tuple[str, ...], status: str) -> None:
        placeholders = ",".join("?" for _ in expected)
        with self.connect() as connection:
            cursor = connection.execute(
                f"UPDATE incidents SET status = ?, updated_at = ? WHERE incident_id = ? AND status IN ({placeholders})",
                (status, now_iso(), incident_id, *expected),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("incident state changed concurrently or transition is invalid")

    def incident(self, incident_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM incidents WHERE incident_id = ?", (incident_id,)).fetchone()
            if not row:
                return None
            result = dict(row)
            result["snapshot"] = json.loads(result.pop("snapshot_json"))
            result["rca"] = json.loads(result.pop("rca_json"))
            result["approval"] = self._last_jsonless(
                connection, "SELECT * FROM approvals WHERE incident_id = ? ORDER BY id DESC LIMIT 1", incident_id
            )
            result["execution"] = self._last_json(
                connection, "SELECT * FROM executions WHERE incident_id = ? ORDER BY id DESC LIMIT 1",
                incident_id, "result_json",
            )
            result["validation"] = self._last_json(
                connection, "SELECT * FROM validations WHERE incident_id = ? ORDER BY id DESC LIMIT 1",
                incident_id, "result_json",
            )
            return result

    @staticmethod
    def _last_jsonless(connection: sqlite3.Connection, query: str, incident_id: str) -> dict[str, Any] | None:
        row = connection.execute(query, (incident_id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def _last_json(connection: sqlite3.Connection, query: str, incident_id: str,
                   json_column: str) -> dict[str, Any] | None:
        row = connection.execute(query, (incident_id,)).fetchone()
        if not row:
            return None
        result = dict(row)
        result["result"] = json.loads(result.pop(json_column))
        return result

    def list_incidents(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT incident_id, scenario, status, predicted_root_cause AS root_cause,
                confidence, created_at FROM incidents ORDER BY created_at DESC LIMIT ?""", (limit,)
            ).fetchall()
            return [dict(row) for row in rows]

    def record_approval(self, incident_id: str, approved: bool, approved_by: str, reason: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO approvals (incident_id, approved, approved_by, reason, created_at) VALUES (?, ?, ?, ?, ?)",
                (incident_id, int(approved), approved_by, reason, now_iso()),
            )

    def record_approval_and_transition(self, incident_id: str, approved: bool, approved_by: str,
                                       reason: str, expected_status: str, new_status: str) -> None:
        with self.connect() as connection:
            cursor = connection.execute(
                "UPDATE incidents SET status = ?, updated_at = ? WHERE incident_id = ? AND status = ?",
                (new_status, now_iso(), incident_id, expected_status),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("incident state changed concurrently or approval is duplicated")
            connection.execute(
                "INSERT INTO approvals (incident_id, approved, approved_by, reason, created_at) VALUES (?, ?, ?, ?, ?)",
                (incident_id, int(approved), approved_by, reason, now_iso()),
            )

    def record_execution(self, incident_id: str, action_id: str, result: dict[str, Any]) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO executions (incident_id, action_id, adapter, result_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (incident_id, action_id, "SyntheticKafkaAdapter", json.dumps(result), now_iso()),
            )

    def record_execution_and_transition(self, incident_id: str, action_id: str, result: dict[str, Any],
                                        expected_status: str, new_status: str) -> None:
        with self.connect() as connection:
            cursor = connection.execute(
                "UPDATE incidents SET status = ?, updated_at = ? WHERE incident_id = ? AND status = ?",
                (new_status, now_iso(), incident_id, expected_status),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("incident state changed concurrently during execution")
            connection.execute(
                "INSERT INTO executions (incident_id, action_id, adapter, result_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (incident_id, action_id, "SyntheticKafkaAdapter", json.dumps(result), now_iso()),
            )

    def record_validation(self, incident_id: str, passed: bool, result: dict[str, Any]) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO validations (incident_id, passed, result_json, created_at) VALUES (?, ?, ?, ?)",
                (incident_id, int(passed), json.dumps(result), now_iso()),
            )

    def record_validation_and_transition(self, incident_id: str, passed: bool, result: dict[str, Any],
                                         expected_status: str, new_status: str) -> None:
        with self.connect() as connection:
            cursor = connection.execute(
                "UPDATE incidents SET status = ?, updated_at = ? WHERE incident_id = ? AND status = ?",
                (new_status, now_iso(), incident_id, expected_status),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("incident state changed concurrently during validation")
            connection.execute(
                "INSERT INTO validations (incident_id, passed, result_json, created_at) VALUES (?, ?, ?, ?)",
                (incident_id, int(passed), json.dumps(result), now_iso()),
            )

    def audit(self, incident_id: str, actor: str, tool: str, action: str,
              input_data: dict[str, Any], output_data: dict[str, Any], decision: str) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO audit_log
                (timestamp, incident_id, actor, tool, action, input_json, output_json, decision)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (now_iso(), incident_id, actor, tool, action, json.dumps(input_data),
                 json.dumps(output_data), decision),
            )

    def activity(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM audit_log ORDER BY sequence DESC LIMIT ?", (limit,)
            ).fetchall()
            results = []
            for row in rows:
                item = dict(row)
                item["input"] = json.loads(item.pop("input_json"))
                item["output"] = json.loads(item.pop("output_json"))
                results.append(item)
            return results

    def evaluation_summary(self) -> dict[str, Any]:
        with self.connect() as connection:
            row = connection.execute(
                """SELECT COUNT(*) AS total, COALESCE(SUM(correct), 0) AS correct,
                COALESCE(AVG(confidence), 0) AS mean_confidence,
                COALESCE(AVG(diagnosis_ms), 0) AS mean_diagnosis_ms FROM evaluations"""
            ).fetchone()
            total = int(row["total"])
            correct = int(row["correct"])
            incident_rows = connection.execute(
                """SELECT i.snapshot_json, i.predicted_root_cause, i.failure_started_at, i.created_at,
                (SELECT v.created_at FROM validations v
                 WHERE v.incident_id = i.incident_id AND v.passed = 1 ORDER BY v.id DESC LIMIT 1) AS validated_at
                FROM incidents i"""
            ).fetchall()
            lag_expected = 0
            lag_detected = 0
            mttd_values: list[float] = []
            mttr_values: list[float] = []
            for incident in incident_rows:
                snapshot = json.loads(incident["snapshot_json"])
                if "consumer_lag" in snapshot and float(snapshot["consumer_lag"]) > 500:
                    lag_expected += 1
                    lag_detected += int(incident["predicted_root_cause"] != "unknown_streaming_failure")
                failure_started = datetime.fromisoformat(incident["failure_started_at"])
                detected = datetime.fromisoformat(incident["created_at"])
                mttd_values.append(max(0.0, (detected - failure_started).total_seconds() * 1000))
                if incident["validated_at"]:
                    validated = datetime.fromisoformat(incident["validated_at"])
                    mttr_values.append(max(0.0, (validated - failure_started).total_seconds() * 1000))
            return {
                "total": total,
                "correct": correct,
                "rca_accuracy": round(correct / total, 4) if total else 0.0,
                "mean_confidence": round(float(row["mean_confidence"]), 4),
                "mean_diagnosis_ms": round(float(row["mean_diagnosis_ms"]), 3),
                "consumer_lag_detection_rate": round(lag_detected / lag_expected, 4) if lag_expected else 0.0,
                "mean_mttd_ms": round(sum(mttd_values) / len(mttd_values), 3) if mttd_values else 0.0,
                "mean_mttr_ms": round(sum(mttr_values) / len(mttr_values), 3) if mttr_values else 0.0,
            }

    def counts(self) -> dict[str, int]:
        with self.connect() as connection:
            incidents = connection.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
            validated = connection.execute("SELECT COUNT(*) FROM validations WHERE passed = 1").fetchone()[0]
            return {"incidents": incidents, "validated": validated}
