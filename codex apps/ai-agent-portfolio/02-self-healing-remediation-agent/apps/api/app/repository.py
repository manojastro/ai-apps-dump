from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from .catalog import RUNBOOKS


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


JSON_COLUMNS = {
    "snapshot_json", "parameters_json", "rollback_json", "reasons_json",
    "original_state_json", "result_json", "checks_json", "details_json", "evidence_refs",
}


class Repository:
    def __init__(self, database_url: str, migration_path: Path):
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        pool_options = {"poolclass": StaticPool} if database_url in {"sqlite://", "sqlite:///:memory:"} else {}
        self.engine: Engine = create_engine(database_url, future=True, connect_args=connect_args, **pool_options)
        self.migration_path = migration_path

    def initialize(self) -> None:
        statements = [s.strip() for s in self.migration_path.read_text(encoding="utf-8").split(";") if s.strip()]
        with self.engine.begin() as conn:
            for statement in statements:
                conn.execute(text(statement))
            for runbook in RUNBOOKS.values():
                conn.execute(
                    text("""INSERT INTO runbooks (id,title,incident_type,approved,content,action,version)
                    VALUES (:id,:title,:incident_type,1,:content,:action,:version)
                    ON CONFLICT(id) DO UPDATE SET title=excluded.title, content=excluded.content,
                    action=excluded.action, version=excluded.version, approved=1"""), runbook,
                )

    def close(self) -> None:
        self.engine.dispose()

    def clear(self) -> None:
        tables = [
            "model_usage", "audit_events", "rollback_records", "verification_results",
            "executions", "approvals", "policy_decisions", "remediation_plans", "hypotheses",
            "evidence", "signals", "incidents",
        ]
        with self.engine.begin() as conn:
            for table in tables:
                conn.execute(text(f"DELETE FROM {table}"))

    def execute(self, sql: str, params: dict[str, Any] | None = None) -> None:
        with self.engine.begin() as conn:
            conn.execute(text(sql), params or {})

    def one(self, sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        with self.engine.connect() as conn:
            row = conn.execute(text(sql), params or {}).mappings().first()
        return self._decode(dict(row)) if row else None

    def all(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self.engine.connect() as conn:
            rows = conn.execute(text(sql), params or {}).mappings().all()
        return [self._decode(dict(row)) for row in rows]

    @staticmethod
    def _decode(row: dict[str, Any]) -> dict[str, Any]:
        for key in JSON_COLUMNS.intersection(row):
            value = row[key]
            if isinstance(value, str):
                try:
                    row[key.removesuffix("_json")] = json.loads(value)
                except json.JSONDecodeError:
                    row[key.removesuffix("_json")] = value
        return row

    def create_incident(self, scenario: dict[str, Any], force_failure: bool) -> dict[str, Any]:
        incident_id, now = new_id("inc"), utcnow()
        self.execute("""INSERT INTO incidents
            (id,scenario,title,status,risk_tier,namespace,resource,force_verification_failure,created_at,updated_at,detected_at,snapshot_json)
            VALUES (:id,:scenario,:title,'DETECTED',NULL,'selfheal-demo',:resource,:force,:now,:now,:now,'{}')""",
            {"id": incident_id, "scenario": scenario["id"], "title": scenario["title"],
             "resource": scenario["resource"], "force": int(force_failure), "now": now})
        self.add_signal(incident_id, scenario["signal"])
        self.audit(incident_id, "incident.detected", "detector", {"scenario": scenario["id"]})
        return self.get_incident(incident_id)

    def add_signal(self, incident_id: str, signal: dict[str, str]) -> None:
        self.execute("INSERT INTO signals (id,incident_id,kind,value,observed_at) VALUES (:id,:inc,:kind,:value,:now)",
                     {"id": new_id("sig"), "inc": incident_id, **signal, "now": utcnow()})

    def update_incident(self, incident_id: str, *, status: str, risk_tier: str | None, snapshot: dict[str, Any]) -> None:
        resolved = utcnow() if status in {"RESOLVED", "ROLLED_BACK", "ESCALATED", "BLOCKED", "REJECTED"} else None
        self.execute("""UPDATE incidents SET status=:status,risk_tier=:risk,updated_at=:now,
            resolved_at=COALESCE(:resolved,resolved_at),snapshot_json=:snapshot WHERE id=:id""",
            {"status": status, "risk": risk_tier, "now": utcnow(), "resolved": resolved,
             "snapshot": json.dumps(snapshot), "id": incident_id})

    def get_incident(self, incident_id: str) -> dict[str, Any]:
        incident = self.one("SELECT * FROM incidents WHERE id=:id", {"id": incident_id})
        if not incident:
            raise KeyError(incident_id)
        return incident

    def list_incidents(self) -> list[dict[str, Any]]:
        return self.all("SELECT * FROM incidents ORDER BY created_at DESC")

    def incident_detail(self, incident_id: str) -> dict[str, Any]:
        result = self.get_incident(incident_id)
        tables = ["signals", "evidence", "hypotheses", "remediation_plans", "policy_decisions",
                  "approvals", "executions", "verification_results", "rollback_records", "audit_events", "model_usage"]
        for table in tables:
            order = {"signals": "observed_at", "evidence": "collected_at", "hypotheses": "id"}.get(table, "created_at")
            result[table] = self.all(f"SELECT * FROM {table} WHERE incident_id=:id ORDER BY {order} ASC", {"id": incident_id})
        snapshot = result.get("snapshot", {})
        if snapshot.get("runbook"):
            result["runbook"] = snapshot["runbook"]
        return result

    def approval(self, incident_id: str) -> dict[str, Any] | None:
        return self.one("SELECT * FROM approvals WHERE incident_id=:id ORDER BY created_at DESC", {"id": incident_id})

    def record_approval(self, incident_id: str, decision: str, actor: str, comment: str) -> dict[str, Any]:
        approval = {"id": new_id("apr"), "incident_id": incident_id, "decision": decision,
                    "actor": actor, "comment": comment, "created_at": utcnow()}
        self.execute("""INSERT INTO approvals (id,incident_id,decision,actor,comment,created_at)
            VALUES (:id,:incident_id,:decision,:actor,:comment,:created_at)""", approval)
        self.audit(incident_id, f"approval.{decision.lower()}", actor, {"comment": comment})
        return approval

    def latest_execution(self, idempotency_key: str) -> dict[str, Any] | None:
        return self.one("SELECT * FROM executions WHERE idempotency_key=:key", {"key": idempotency_key})

    def recent_matching_execution(self, action: str, resource: str, cooldown_seconds: int) -> dict[str, Any] | None:
        row = self.one("SELECT * FROM executions WHERE action=:action AND resource=:resource AND status='SUCCEEDED' ORDER BY created_at DESC", {"action": action, "resource": resource})
        if not row:
            return None
        created = datetime.fromisoformat(row["created_at"])
        return row if (datetime.now(UTC) - created).total_seconds() < cooldown_seconds else None

    def audit(self, incident_id: str | None, event_type: str, actor: str, details: dict[str, Any]) -> None:
        self.execute("""INSERT INTO audit_events (id,incident_id,event_type,actor,details_json,created_at)
            VALUES (:id,:incident,:event,:actor,:details,:now)""",
            {"id": new_id("aud"), "incident": incident_id, "event": event_type, "actor": actor,
             "details": json.dumps(details), "now": utcnow()})

    def dashboard(self) -> dict[str, Any]:
        incidents = self.list_incidents()
        total = len(incidents)
        resolved = sum(i["status"] == "RESOLVED" for i in incidents)
        rollbacks = sum(i["status"] == "ROLLED_BACK" for i in incidents)
        blocked = sum(i["status"] == "BLOCKED" for i in incidents)
        failed = sum(i["status"] in {"ROLLED_BACK", "ESCALATED"} for i in incidents)
        approvals = self.all("""SELECT a.decision,
            (SELECT pd.risk_tier FROM policy_decisions pd WHERE pd.incident_id=a.incident_id ORDER BY pd.created_at DESC LIMIT 1) AS risk_tier
            FROM approvals a""")
        by_tier: dict[str, dict[str, int]] = {}
        for item in approvals:
            tier = item["risk_tier"]
            by_tier.setdefault(tier, {"approved": 0, "rejected": 0, "total": 0})
            by_tier[tier][item["decision"].lower()] += 1
            by_tier[tier]["total"] += 1
        for values in by_tier.values():
            values["approval_rate"] = round(values["approved"] / values["total"], 3) if values["total"] else 0
        mttrs = []
        for item in incidents:
            if item.get("resolved_at"):
                mttrs.append((datetime.fromisoformat(item["resolved_at"]) - datetime.fromisoformat(item["detected_at"])).total_seconds())
        type_counts: dict[str, int] = {}
        for item in incidents:
            type_counts[item["scenario"]] = type_counts.get(item["scenario"], 0) + 1
        return {
            "total_incidents": total, "active_incidents": sum(i["status"] in {"DETECTED", "PENDING_APPROVAL", "EXECUTING"} for i in incidents),
            "detected": total, "resolved": resolved, "auto_resolution_rate": round(resolved / total, 3) if total else 0,
            "verified_recovery_rate": round(resolved / total, 3) if total else 0,
            "mttr_seconds": round(sum(mttrs) / len(mttrs), 3) if mttrs else 0,
            "approval_rate_by_tier": by_tier, "actions_blocked": blocked, "rollback_rate": round(rollbacks / total, 3) if total else 0,
            "failed_recovery_rate": round(failed / total, 3) if total else 0,
            "top_incident_types": sorted(type_counts.items(), key=lambda x: (-x[1], x[0])),
            "timeline": incidents[:20],
        }

    def count(self, table: str) -> int:
        allowed = {"incidents", "executions", "rollback_records", "audit_events", "approvals"}
        if table not in allowed:
            raise ValueError(table)
        row = self.one(f"SELECT COUNT(*) AS count FROM {table}")
        return int(row["count"])
