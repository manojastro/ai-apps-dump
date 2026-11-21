"""Persistent ServiceNow simulator.

Behaves like a remote instance: records live in ``sn_sim_records`` (separate from the
application's own tables), get ``sys_id``/``number`` values, keep an activity stream, and
support encoded queries. Every operation runs in its own transaction, exactly like a remote
system - a write that succeeded "remotely" stays committed even if the caller's transaction
rolls back.

Failures can be injected (auth failure, timeout, HTTP 500, or a "lost response" where the
record IS created but the caller sees a timeout) to exercise retry/idempotency end to end.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import session_scope
from app.core.types import utcnow
from app.integrations.servicenow.base import (
    ServiceNowAuthError,
    ServiceNowClient,
    ServiceNowServerError,
    ServiceNowTimeout,
)
from app.models.servicenow import SnSimActivity, SnSimRecord
from app.services.policy_store import SN_SIM_FAILURE_KEY, get_setting, put_setting

log = logging.getLogger("aegis.servicenow.mock")

NUMBER_PREFIX = {
    "change_request": ("CHG", 30000),
    "change_task": ("CTASK", 10000),
    "incident": ("INC", 10000),
}
SIM_TABLES = {
    "change_request": "Change Request",
    "change_task": "Change Task",
    "cmdb_ci_server": "Server (CMDB CI)",
    "cmdb_ci_service": "Business Service",
    "cmdb_rel_ci": "CI Relationship",
}
TABLE_FIELDS: dict[str, set[str]] = {
    "change_request": {
        "sys_id",
        "number",
        "short_description",
        "description",
        "justification",
        "implementation_plan",
        "backout_plan",
        "test_plan",
        "risk",
        "impact",
        "urgency",
        "priority",
        "type",
        "category",
        "state",
        "approval",
        "cmdb_ci",
        "business_service",
        "assignment_group",
        "correlation_id",
        "correlation_display",
        "start_date",
        "end_date",
        "close_code",
        "close_notes",
        "work_notes",
        "sys_created_by",
        "sys_created_on",
        "sys_updated_on",
    },
    "change_task": {
        "sys_id",
        "number",
        "short_description",
        "description",
        "change_request",
        "state",
        "cmdb_ci",
        "assignment_group",
        "correlation_id",
        "correlation_display",
        "close_code",
        "close_notes",
        "work_notes",
        "sys_created_by",
        "sys_created_on",
        "sys_updated_on",
    },
}
DEFAULT_STATES = {"change_request": {"state": "-5", "approval": "requested"}, "change_task": {"state": "1"}}
FAILURE_MODES = ("none", "auth_failure", "timeout", "server_error", "lost_response")


def _sys_id() -> str:
    return uuid.uuid4().hex


def _to_dict(rec: SnSimRecord) -> dict[str, Any]:
    return {
        **rec.fields,
        "sys_id": rec.sys_id,
        "number": rec.number,
        "sys_created_by": rec.sys_created_by,
        "sys_created_on": rec.sys_created_on.isoformat(),
        "sys_updated_on": rec.sys_updated_on.isoformat(),
    }


def _next_number(db: Session, table: str) -> str | None:
    if table not in NUMBER_PREFIX:
        return None
    prefix, base = NUMBER_PREFIX[table]
    count = db.scalar(select(func.count()).select_from(SnSimRecord).where(SnSimRecord.table_name == table)) or 0
    return f"{prefix}{base + count + 1:07d}"


def matches_query(fields: dict[str, Any], query: str) -> bool:
    """Subset of ServiceNow encoded-query syntax: =, !=, LIKE, IN joined by ^."""
    for clause in [c for c in query.split("^") if c and not c.startswith("ORDERBY")]:
        if "!=" in clause:
            k, v = clause.split("!=", 1)
            if str(fields.get(k, "")) == v:
                return False
        elif "LIKE" in clause:
            k, v = clause.split("LIKE", 1)
            if v.lower() not in str(fields.get(k, "")).lower():
                return False
        elif "IN" in clause and "=" not in clause:
            k, v = clause.split("IN", 1)
            if str(fields.get(k, "")) not in v.split(","):
                return False
        elif "=" in clause:
            k, v = clause.split("=", 1)
            if str(fields.get(k, "")) != v:
                return False
    return True


class MockServiceNowClient(ServiceNowClient):
    mode = "mock"
    instance_label = "northstar-sim.service-now.local (simulated)"

    def __init__(self, actor: str = "aegis.integration") -> None:
        self.actor = actor

    # ---------------------------------------------------------- failure injection
    def _maybe_fail(self, operation: str) -> str | None:
        with session_scope() as db:
            cfg = get_setting(db, SN_SIM_FAILURE_KEY, {"mode": "none", "remaining": 0})
            mode, remaining = cfg.get("mode", "none"), int(cfg.get("remaining", 0))
            if mode == "none" or remaining == 0:
                return None
            if mode == "lost_response" and operation != "create":
                return None
            if remaining > 0:
                cfg["remaining"] = remaining - 1
                if cfg["remaining"] == 0:
                    cfg["mode"] = "none"
                put_setting(db, SN_SIM_FAILURE_KEY, cfg, "simulator")
        log.warning("simulated ServiceNow failure", extra={"mode": mode, "operation": operation})
        if mode == "auth_failure":
            raise ServiceNowAuthError("401 Unauthorized: OAuth token rejected (simulated credential expiry)", 401)
        if mode == "timeout":
            raise ServiceNowTimeout("Request timed out after 20s (simulated)")
        if mode == "server_error":
            raise ServiceNowServerError("500 Internal Server Error (simulated)", 500)
        return mode  # lost_response: perform the write, then fail

    # ---------------------------------------------------------- contract
    def query(self, table: str, query: str = "", fields: list[str] | None = None, limit: int = 100) -> list[dict[str, Any]]:
        self._maybe_fail("query")
        out: list[dict[str, Any]] = []
        with session_scope() as db:
            rows = db.scalars(select(SnSimRecord).where(SnSimRecord.table_name == table).order_by(SnSimRecord.sys_created_on))
            for rec in rows:
                d = _to_dict(rec)
                if matches_query(d, query):
                    out.append({k: d.get(k) for k in fields} if fields else d)
                    if len(out) >= limit:
                        break
        return out

    def get(self, table: str, sys_id: str) -> dict[str, Any] | None:
        self._maybe_fail("get")
        with session_scope() as db:
            rec = db.scalar(select(SnSimRecord).where(SnSimRecord.table_name == table, SnSimRecord.sys_id == sys_id))
            return _to_dict(rec) if rec else None

    def create(self, table: str, fields: dict[str, Any]) -> dict[str, Any]:
        failure = self._maybe_fail("create")
        allowed = TABLE_FIELDS.get(table)
        if allowed is not None and (unknown := set(fields) - allowed):
            raise ServiceNowServerError(f"400 Bad Request: unknown fields {sorted(unknown)}", 400)
        with session_scope() as db:
            rec = SnSimRecord(
                table_name=table,
                sys_id=_sys_id(),
                number=_next_number(db, table),
                fields={**DEFAULT_STATES.get(table, {}), **fields},
                sys_created_by=self.actor,
            )
            db.add(rec)
            db.add(SnSimActivity(table_name=table, sys_id=rec.sys_id, action="insert", changes=fields, actor=self.actor))
            db.flush()
            result = _to_dict(rec)
        if failure == "lost_response":
            # The record now exists remotely, but the caller never receives the response.
            raise ServiceNowTimeout("Connection reset after request was sent (simulated lost response)")
        return result

    def update(self, table: str, sys_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        self._maybe_fail("update")
        with session_scope() as db:
            rec = db.scalar(select(SnSimRecord).where(SnSimRecord.table_name == table, SnSimRecord.sys_id == sys_id))
            if rec is None:
                raise ServiceNowServerError(f"404 Not Found: {table}/{sys_id}", 404)
            before = {k: rec.fields.get(k) for k in fields}
            rec.fields = {**rec.fields, **fields}
            rec.sys_updated_on = utcnow()
            db.add(
                SnSimActivity(
                    table_name=table,
                    sys_id=sys_id,
                    action="update",
                    changes={"before": before, "after": fields},
                    actor=self.actor,
                )
            )
            db.flush()
            return _to_dict(rec)

    def table_fields(self, table: str) -> set[str] | None:
        if table in TABLE_FIELDS:
            return TABLE_FIELDS[table]
        return None if table in SIM_TABLES else set()

    def test_connection(self) -> dict[str, Any]:
        self._maybe_fail("query")
        with session_scope() as db:
            count = db.scalar(select(func.count()).select_from(SnSimRecord)) or 0
        return {"ok": True, "instance": self.instance_label, "detail": f"Simulator reachable; {count} records", "mode": self.mode}
