"""Append-only audit log.

This module deliberately exposes only `append` and read functions. There is no update or
delete function, and SQLite triggers (app/approval/db.py) reject UPDATE/DELETE on the table
even if someone writes raw SQL.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.approval.db import AuditRow


def append(session: Session, *, actor: str, event: str, entity_type: str, entity_id: str,
           before: dict[str, Any] | None = None, after: dict[str, Any] | None = None,
           details: dict[str, Any] | None = None) -> AuditRow:
    row = AuditRow(actor=actor, event=event, entity_type=entity_type, entity_id=str(entity_id),
                   before=before, after=after, details=details)
    session.add(row)
    session.flush()
    return row


def entries(session: Session, entity_id: str | None = None, limit: int = 200) -> list[AuditRow]:
    q = select(AuditRow).order_by(AuditRow.id.desc()).limit(limit)
    if entity_id is not None:
        q = q.where(AuditRow.entity_id == str(entity_id))
    return list(session.scalars(q))


def to_dict(row: AuditRow) -> dict:
    return {"id": row.id, "ts": row.ts.isoformat(), "actor": row.actor, "event": row.event,
            "entity_type": row.entity_type, "entity_id": row.entity_id, "before": row.before,
            "after": row.after, "details": row.details}
