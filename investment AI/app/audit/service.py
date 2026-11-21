from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.logging import get_logger
from app.persistence import AuditEventRow

log = get_logger(component="audit")

ALLOWED = {
    "PLAN_CREATED",
    "IPS_VALIDATED",
    "PII_REDACTED",
    "REGULATORY_SNAPSHOT_CREATED",
    "SOURCE_FETCHED",
    "SOURCE_CACHE_USED",
    "AGENT_COMPLETED",
    "POLICY_RULE_TRIGGERED",
    "RISK_VETO",
    "PLAN_REBUILT",
    "PLAN_SELECTED",
    "PDF_GENERATED",
}


def audit(db: Session, event: str, *, plan_id: str = "", component: str = "", metadata: dict | None = None) -> None:
    if event not in ALLOWED:
        raise ValueError(f"unknown audit event {event}")
    payload = metadata or {}
    # Never persist chain-of-thought.
    payload.pop("chain_of_thought", None)
    payload.pop("hidden_reasoning", None)
    row = AuditEventRow(
        event=event,
        timestamp=datetime.now(timezone.utc),
        plan_id=plan_id,
        component=component,
        metadata_json=json.dumps(payload),
    )
    db.add(row)
    db.commit()
    log.info("audit", audit_event=event, plan_id=plan_id, component=component)
