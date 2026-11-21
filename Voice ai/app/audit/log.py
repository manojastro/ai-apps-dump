from __future__ import annotations

import hashlib
import json
from datetime import datetime

from sqlalchemy import select

from app import clock
from app.data.db import session
from app.data.models import AuditEntry


def args_hash(args: dict) -> str:
    return hashlib.sha256(json.dumps(args, sort_keys=True, default=str).encode()).hexdigest()[:16]


def write(*, actor: str, tool: str, args: dict, status: str, patient_id: str | None = None,
          workflow_id: str | None = None, detail: str = "") -> None:
    with session() as s:
        s.add(AuditEntry(ts=clock.now(), actor=actor, tool=tool, args_hash=args_hash(args), patient_id=patient_id,
                         workflow_id=workflow_id, status=status, detail=detail[:500]))


def search(*, actor: str | None = None, tool: str | None = None, patient_id: str | None = None,
           date_from: datetime | None = None, date_to: datetime | None = None,
           workflow_id: str | None = None, limit: int = 200) -> list[AuditEntry]:
    q = select(AuditEntry).order_by(AuditEntry.id.desc()).limit(limit)
    if actor:
        q = q.where(AuditEntry.actor == actor)
    if tool:
        q = q.where(AuditEntry.tool == tool)
    if patient_id:
        q = q.where(AuditEntry.patient_id == patient_id)
    if workflow_id:
        q = q.where(AuditEntry.workflow_id == workflow_id)
    if date_from:
        q = q.where(AuditEntry.ts >= date_from)
    if date_to:
        q = q.where(AuditEntry.ts <= date_to)
    with session() as s:
        return list(s.scalars(q))
