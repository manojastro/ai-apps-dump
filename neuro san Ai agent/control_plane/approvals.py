"""Approval engine (M15): human gates for L2 actions and promotions.

State machine: PENDING → APPROVED | DENIED | EXPIRED. Terminal states are
immutable (double-decide raises). Stale PENDING rows expire by age so
execution can never hang forever (approval-timeout failure condition).
Convention: approvals.script_id holds the gated entity id (script or
workflow) — shared with the autonomy engine's approval counting.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

TERMINAL = ("APPROVED", "DENIED", "EXPIRED")
DEFAULT_TIMEOUT_HOURS = 24


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def request_approval(conn: sqlite3.Connection, case_id: str, script_id: str,
                     requested_by: str, reason: str = "") -> dict[str, Any]:
    """Open a gate. An existing PENDING gate for (case, entity) is reused."""
    existing = pending_for(conn, case_id, script_id)
    if existing is not None:
        return existing
    approval_id = f"APR-{case_id}-{script_id}" if case_id else f"APR-{script_id}"
    conn.execute(
        "INSERT INTO approvals(approval_id, case_id, script_id, requested_by) "
        "VALUES (?,?,?,?)", (approval_id, case_id, script_id, requested_by or reason))
    conn.commit()
    return get_approval(conn, approval_id)


def get_approval(conn: sqlite3.Connection, approval_id: str) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM approvals WHERE approval_id=?",
                       (approval_id,)).fetchone()
    if row is None:
        raise LookupError(f"approval {approval_id} not found")
    return dict(row)


def pending_for(conn: sqlite3.Connection, case_id: str,
                script_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM approvals WHERE case_id=? AND script_id=? AND state='PENDING' "
        "ORDER BY requested_at DESC LIMIT 1", (case_id, script_id)).fetchone()
    return dict(row) if row else None


def latest_for(conn: sqlite3.Connection, case_id: str,
               script_id: str) -> dict[str, Any] | None:
    """Newest gate for (case, entity) in any state (execution checks APPROVED)."""
    row = conn.execute(
        "SELECT * FROM approvals WHERE case_id=? AND script_id=? "
        "ORDER BY requested_at DESC LIMIT 1", (case_id, script_id)).fetchone()
    return dict(row) if row else None


def approve(conn: sqlite3.Connection, approval_id: str, approver: str) -> dict[str, Any]:
    return _decide(conn, approval_id, approver, "APPROVED")


def deny(conn: sqlite3.Connection, approval_id: str, approver: str) -> dict[str, Any]:
    return _decide(conn, approval_id, approver, "DENIED")


def _decide(conn: sqlite3.Connection, approval_id: str, approver: str,
            state: str) -> dict[str, Any]:
    if not approver.strip():
        raise ValueError("approver identity is required (no self-approval blanks)")
    current = get_approval(conn, approval_id)
    if current["state"] in TERMINAL:
        raise ValueError(f"approval {approval_id} already {current['state']}")
    conn.execute("UPDATE approvals SET state=?, approver=?, decided_at=? "
                 "WHERE approval_id=?", (state, approver, _utcnow(), approval_id))
    conn.commit()
    return get_approval(conn, approval_id)


def expire_stale(conn: sqlite3.Connection, older_than_hours: int = DEFAULT_TIMEOUT_HOURS,
                 now: datetime | None = None) -> int:
    """Expire PENDING gates older than the timeout. Returns count expired."""
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(hours=older_than_hours)
    rows = conn.execute("SELECT approval_id, requested_at FROM approvals "
                        "WHERE state='PENDING'").fetchall()
    expired = 0
    for row in rows:
        try:
            requested = datetime.fromisoformat(str(row["requested_at"]).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            continue
        if requested.tzinfo is None:
            requested = requested.replace(tzinfo=timezone.utc)
        if requested < cutoff:
            conn.execute("UPDATE approvals SET state='EXPIRED', decided_at=? "
                         "WHERE approval_id=?", (_utcnow(), row["approval_id"]))
            expired += 1
    conn.commit()
    return expired
