"""Append-only audit trail. Every externally meaningful action is recorded here."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.workflow import AuditEvent
from app.observability.logging import correlation_id_var
from app.security.auth import Principal
from app.security.redaction import redact

log = logging.getLogger("aegis.audit")


def record_audit(
    db: Session,
    *,
    actor: Principal | None,
    action: str,
    target_type: str,
    target_id: str | None = None,
    previous_state: dict[str, Any] | None = None,
    new_state: dict[str, Any] | None = None,
    details: dict[str, Any] | None = None,
    outcome: str = "success",
    correlation_id: str | None = None,
    ip_address: str | None = None,
) -> AuditEvent:
    """Add an audit event to the current transaction (committed with the business change)."""
    event = AuditEvent(
        actor_id=actor.id if actor and actor.id != "system" else None,
        actor_label=actor.label if actor else "system",
        action=action,
        target_type=target_type,
        target_id=target_id,
        previous_state=redact(previous_state) if previous_state is not None else None,
        new_state=redact(new_state) if new_state is not None else None,
        details=redact(details or {}),
        outcome=outcome,
        correlation_id=correlation_id or correlation_id_var.get(),
        ip_address=ip_address,
    )
    db.add(event)
    log.info("audit %s %s/%s outcome=%s", action, target_type, target_id, outcome)
    return event
