"""Auditable access, review and processing events (never contains document content)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from spreadlens.models import AuditEvent, MetricEvent
from spreadlens.observability import correlation_id


def audit(db: Session, workspace_id: str | None, user_id: str | None, action: str, target_type: str | None = None,
          target_id: str | None = None, outcome: str = "ok", details: dict[str, Any] | None = None,
          message: str | None = None) -> None:
    db.add(AuditEvent(workspace_id=workspace_id, user_id=user_id, action=action, target_type=target_type,
                      target_id=target_id, outcome=outcome, details=details or {}, message=message,
                      correlation_id=correlation_id.get()))


def metric(db: Session, workspace_id: str | None, name: str, value: float, **labels: Any) -> None:
    db.add(MetricEvent(workspace_id=workspace_id, name=name, value=float(value), labels=labels))
