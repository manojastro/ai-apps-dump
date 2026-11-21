from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS incidents (
    incident_id TEXT PRIMARY KEY,
    scenario TEXT NOT NULL,
    status TEXT NOT NULL,
    before_source TEXT NOT NULL,
    after_source TEXT,
    investigation_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT NOT NULL,
    approved INTEGER NOT NULL,
    approved_by TEXT NOT NULL,
    approver_role TEXT NOT NULL,
    reason TEXT NOT NULL,
    action_id TEXT NOT NULL,
    patch_sha256 TEXT NOT NULL,
    fixed_source_sha256 TEXT NOT NULL,
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
    incident_id TEXT PRIMARY KEY,
    finding_valid INTEGER NOT NULL,
    expected_finding INTEGER NOT NULL,
    detected_finding INTEGER NOT NULL,
    true_exploitability TEXT NOT NULL,
    predicted_exploitability TEXT NOT NULL,
    remediation_attempted INTEGER NOT NULL DEFAULT 0,
    remediation_success INTEGER NOT NULL DEFAULT 0,
    security_regression INTEGER NOT NULL DEFAULT 0,
    test_regression INTEGER NOT NULL DEFAULT 0,
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
CREATE TRIGGER IF NOT EXISTS audit_log_no_update BEFORE UPDATE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit log is immutable'); END;
CREATE TRIGGER IF NOT EXISTS audit_log_no_delete BEFORE DELETE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit log is immutable'); END;
CREATE TRIGGER IF NOT EXISTS approvals_no_update BEFORE UPDATE ON approvals
BEGIN SELECT RAISE(ABORT, 'approval attestation is immutable'); END;
CREATE TRIGGER IF NOT EXISTS approvals_no_delete BEFORE DELETE ON approvals
BEGIN SELECT RAISE(ABORT, 'approval attestation is immutable'); END;
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Repository:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
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
            applied_migrations = {
                row[0] for row in connection.execute("SELECT version FROM schema_migrations").fetchall()
            }
            approval_columns = {row[1] for row in connection.execute("PRAGMA table_info(approvals)")}
            for column, definition in {
                "approver_role": "TEXT",
                "action_id": "TEXT",
                "patch_sha256": "TEXT",
                "fixed_source_sha256": "TEXT",
            }.items():
                if column not in approval_columns:
                    connection.execute(f"ALTER TABLE approvals ADD COLUMN {column} {definition}")
            evaluation_columns = {row[1] for row in connection.execute("PRAGMA table_info(evaluations)")}
            for column in ("expected_finding", "detected_finding"):
                if column not in evaluation_columns:
                    connection.execute(f"ALTER TABLE evaluations ADD COLUMN {column} INTEGER NOT NULL DEFAULT 1")
            if "001_initial" not in applied_migrations:
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES ('001_initial', ?)",
                    (now_iso(),),
                )
            if "002_bound_approval" not in applied_migrations:
                # Legacy approvals cannot prove which action, preview, and fixed bytes
                # were reviewed. Keep their immutable rows as history but require a
                # new attestation instead of inferring any binding.
                connection.execute(
                    """UPDATE incidents SET status='REAPPROVAL_REQUIRED', updated_at=?
                    WHERE status='APPROVED' AND incident_id IN (
                        SELECT incident_id FROM approvals WHERE approved=1 AND (
                            approver_role IS NULL OR action_id IS NULL OR
                            patch_sha256 IS NULL OR fixed_source_sha256 IS NULL
                        )
                    )""",
                    (now_iso(),),
                )
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES ('002_bound_approval', ?)",
                    (now_iso(),),
                )
            if "003_require_fresh_bound_reapproval" not in applied_migrations:
                # Early version-002 approvals did not verify the persisted preview
                # bytes. Invalidate every still-executable historical decision once.
                connection.execute(
                    """UPDATE incidents SET status='REAPPROVAL_REQUIRED', updated_at=?
                    WHERE status='APPROVED' AND incident_id IN (
                        SELECT incident_id FROM approvals WHERE approved=1
                    )""",
                    (now_iso(),),
                )
                connection.execute(
                    """INSERT INTO schema_migrations(version, applied_at)
                    VALUES ('003_require_fresh_bound_reapproval', ?)""",
                    (now_iso(),),
                )

    def create_incident(self, record: dict[str, Any]) -> None:
        timestamp = now_iso()
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO incidents
                (incident_id, scenario, status, before_source, investigation_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (record["incident_id"], record["scenario"], record["status"], record["before_source"],
                 json.dumps(record["investigation"]), timestamp, timestamp),
            )
            connection.execute(
                """INSERT INTO evaluations
                (incident_id, finding_valid, expected_finding, detected_finding,
                 true_exploitability, predicted_exploitability)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (record["incident_id"], int(record["finding_valid"]), int(record["expected_finding"]),
                 int(record["detected_finding"]), record["true_exploitability"],
                 record["predicted_exploitability"]),
            )

    def update_status(self, incident_id: str, status: str) -> None:
        with self.connect() as connection:
            cursor = connection.execute(
                "UPDATE incidents SET status = ?, updated_at = ? WHERE incident_id = ?",
                (status, now_iso(), incident_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(incident_id)

    def set_after_source(self, incident_id: str, after_source: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE incidents SET after_source = ?, updated_at = ? WHERE incident_id = ?",
                (after_source, now_iso(), incident_id),
            )

    def incident(self, incident_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM incidents WHERE incident_id = ?", (incident_id,)).fetchone()
            if not row:
                return None
            result = dict(row)
            result["investigation"] = json.loads(result.pop("investigation_json"))
            approval = connection.execute(
                "SELECT * FROM approvals WHERE incident_id = ? ORDER BY id DESC LIMIT 1", (incident_id,)
            ).fetchone()
            validation = connection.execute(
                "SELECT * FROM validations WHERE incident_id = ? ORDER BY id DESC LIMIT 1", (incident_id,)
            ).fetchone()
            result["approval"] = dict(approval) if approval else None
            result["validation"] = None
            if validation:
                result["validation"] = dict(validation)
                result["validation"]["result"] = json.loads(result["validation"].pop("result_json"))
            return result

    def list_incidents(self, limit: int) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT incident_id, scenario, status,
                json_extract(investigation_json, '$.finding.title') AS title,
                json_extract(investigation_json, '$.finding.cwe') AS cwe,
                json_extract(investigation_json, '$.exploitability.classification') AS exploitability,
                json_extract(investigation_json, '$.release_risk_before.score') AS risk_score,
                created_at FROM incidents ORDER BY created_at DESC LIMIT ?""", (limit,)
            ).fetchall()
            return [dict(row) for row in rows]

    def record_approval(
        self,
        incident_id: str,
        approved: bool,
        approved_by: str,
        approver_role: str,
        reason: str,
        action_id: str,
        patch_sha256: str,
        fixed_source_sha256: str,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO approvals
                (incident_id, approved, approved_by, approver_role, reason, action_id,
                 patch_sha256, fixed_source_sha256, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (incident_id, int(approved), approved_by, approver_role, reason, action_id,
                 patch_sha256, fixed_source_sha256, now_iso()),
            )

    def record_validation(self, incident_id: str, result: dict[str, Any]) -> None:
        checks = result["checks"]
        passed = bool(result["passed"])
        security_regression, test_regression = self._regression_flags(checks)
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO validations (incident_id, passed, result_json, created_at) VALUES (?, ?, ?, ?)",
                (incident_id, int(passed), json.dumps(result), now_iso()),
            )
            connection.execute(
                """UPDATE evaluations SET remediation_attempted = 1, remediation_success = ?,
                security_regression = ?, test_regression = ? WHERE incident_id = ?""",
                (int(passed), security_regression, test_regression, incident_id),
            )

    @staticmethod
    def _regression_flags(checks: dict[str, bool]) -> tuple[int, int]:
        security_names = (
            "original_finding_removed", "safe_construct_present", "exact_scenario_structure",
            "allow_list_policy", "no_top_level_side_effects", "no_obvious_new_high_risk_pattern",
        )
        test_names = ("syntax_valid", "public_contract_preserved")
        security_regression = int(any(checks.get(name) is False for name in security_names if name in checks))
        test_regression = int(any(checks.get(name) is False for name in test_names if name in checks))
        return security_regression, test_regression

    def record_validation_outcome(
        self,
        incident_id: str,
        result: dict[str, Any],
        *,
        status: str,
        after_source: str | None,
        actor: str,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
        decision: str,
    ) -> None:
        """Persist source state, validation, evaluation, and audit in one transaction."""
        checks = result["checks"]
        passed = bool(result["passed"])
        security_regression, test_regression = self._regression_flags(checks)
        timestamp = now_iso()
        with self.connect() as connection:
            cursor = connection.execute(
                """UPDATE incidents SET after_source=?, status=?, updated_at=?
                WHERE incident_id=?""",
                (after_source, status, timestamp, incident_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(incident_id)
            connection.execute(
                "INSERT INTO validations (incident_id, passed, result_json, created_at) VALUES (?, ?, ?, ?)",
                (incident_id, int(passed), json.dumps(result), timestamp),
            )
            connection.execute(
                """UPDATE evaluations SET remediation_attempted=1, remediation_success=?,
                security_regression=?, test_regression=? WHERE incident_id=?""",
                (int(passed), security_regression, test_regression, incident_id),
            )
            connection.execute(
                """INSERT INTO audit_log
                (timestamp, incident_id, actor, tool, action, input_json, output_json, decision)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    timestamp,
                    incident_id,
                    actor,
                    "ValidationAgent.validate",
                    "rescan_test_and_finalize_or_rollback",
                    json.dumps(input_data),
                    json.dumps(output_data),
                    decision,
                ),
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

    def activity(self, limit: int) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM audit_log ORDER BY sequence DESC LIMIT ?", (limit,)).fetchall()
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
                """SELECT COUNT(*) AS investigations,
                COALESCE(SUM(CASE WHEN expected_finding = 1 AND detected_finding = 1 THEN 1 ELSE 0 END), 0) AS true_findings,
                COALESCE(SUM(finding_valid), 0) AS finding_correct,
                COALESCE(SUM(CASE WHEN true_exploitability = predicted_exploitability THEN 1 ELSE 0 END), 0) AS exploit_correct,
                COALESCE(SUM(remediation_attempted), 0) AS attempted,
                COALESCE(SUM(remediation_success), 0) AS successful,
                COALESCE(SUM(security_regression), 0) AS security_regressions,
                COALESCE(SUM(test_regression), 0) AS test_regressions FROM evaluations"""
            ).fetchone()
            investigations = int(row["investigations"])
            attempts = int(row["attempted"])
            return {
                "investigations": investigations,
                "true_findings": int(row["true_findings"]),
                "finding_validity": round(int(row["finding_correct"]) / investigations, 4) if investigations else 0.0,
                "exploitability_accuracy": round(int(row["exploit_correct"]) / investigations, 4) if investigations else 0.0,
                "attempted_remediations": attempts,
                "successful_remediations": int(row["successful"]),
                "remediation_success_rate": round(int(row["successful"]) / attempts, 4) if attempts else 0.0,
                "security_regressions": int(row["security_regressions"]),
                "test_regressions": int(row["test_regressions"]),
            }

    def counts(self) -> dict[str, int]:
        summary = self.evaluation_summary()
        return {"incidents": summary["investigations"], "validated": summary["successful_remediations"]}
