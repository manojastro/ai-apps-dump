"""Audit trail (M2): redacted JSONL-style events in SQLite audit_events.

Every write passes through redact_text — no API keys, passwords,
hostnames-in-secrets, or PII seed values reach the store.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from common.redaction import redact_text
from database.models import AuditEvent


def log_event(conn: sqlite3.Connection, event: AuditEvent) -> int:
    """Insert one redacted audit event. Returns event_id."""
    cur = conn.execute(
        """INSERT INTO audit_events
        (timestamp, case_id, agent, event_type, tool, sanitized_input,
         sanitized_output, evidence_ids, decision, policy_result, risk,
         approval, action, duration_ms, success)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            event.timestamp,
            event.case_id,
            event.agent,
            event.event_type,
            event.tool,
            redact_text(event.sanitized_input),
            redact_text(event.sanitized_output),
            event.evidence_ids,
            event.decision,
            event.policy_result,
            event.risk,
            event.approval,
            event.action,
            event.duration_ms,
            event.success,
        ),
    )
    conn.commit()
    return int(cur.lastrowid or 0)


def list_events(conn: sqlite3.Connection, case_id: str) -> list[dict[str, Any]]:
    """Timeline for one case, oldest first."""
    cur = conn.execute(
        "SELECT * FROM audit_events WHERE case_id=? ORDER BY timestamp, event_id",
        (case_id,),
    )
    return [dict(row) for row in cur.fetchall()]
