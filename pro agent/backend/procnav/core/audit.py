"""Structured, redacted audit trail and persisted run events (the source for live streaming)."""

from __future__ import annotations

import logging
import uuid
from typing import Any

import structlog
from sqlalchemy.orm import Session

from .models import AuditEvent, RunEvent
from .redact import redact

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)
log = structlog.get_logger("procnav")


def audit(
    session: Session,
    tenant_id: uuid.UUID,
    *,
    actor_type: str,
    actor_id: str | uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: str | uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
    data: dict[str, Any] | None = None,
) -> None:
    clean = redact(data or {})
    session.add(
        AuditEvent(
            tenant_id=tenant_id,
            actor_type=actor_type,
            actor_id=str(actor_id) if actor_id else None,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            run_id=run_id,
            data=clean,
        )
    )
    log.info(
        "audit",
        action=action,
        entity=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        tenant=str(tenant_id),
        actor=actor_type,
        run=str(run_id) if run_id else None,
    )


def run_event(session: Session, tenant_id: uuid.UUID, run_id: uuid.UUID, type_: str, data: dict[str, Any]) -> None:
    session.add(RunEvent(tenant_id=tenant_id, run_id=run_id, type=type_, data=redact(data)))
