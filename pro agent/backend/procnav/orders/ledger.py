"""Order ledger: the single source of truth for purchasing side effects.

The database trigger enforces valid transitions; this module adds row locks so that two
workers can never both move the same intent into 'submitting'. Graph checkpoints are not
consulted for side effects: a resumed run always reads the ledger first.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.audit import audit
from ..core.models import ApprovalRequest, OrderAttempt, OrderIntent

IN_FLIGHT = ("submitting", "unknown", "cancellation_requested")


class LedgerError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def new_intent_key(run_id: uuid.UUID) -> str:
    # Sent to the supplier as the purchase-order reference / idempotency token.
    return f"PN-{str(run_id)[:8].upper()}-{secrets.token_hex(4).upper()}"


def intent_for_run(session: Session, run_id: uuid.UUID) -> OrderIntent | None:
    return session.scalar(
        select(OrderIntent).where(OrderIntent.run_id == run_id).order_by(OrderIntent.created_at.desc()).limit(1)
    )


def create_intent_from_approval(session: Session, approval: ApprovalRequest, worker_id: str) -> OrderIntent:
    """Consume an approved request exactly once and create its intent atomically."""
    locked = session.scalar(select(ApprovalRequest).where(ApprovalRequest.id == approval.id).with_for_update())
    if locked is None or locked.status != "approved":
        raise LedgerError("APPROVAL_NOT_APPROVED", "Approval is not in the approved state")
    if locked.expires_at <= datetime.now(UTC):
        locked.status = "expired"
        raise LedgerError("APPROVAL_EXPIRED", "Approval expired before submission")
    existing = session.scalar(select(OrderIntent).where(OrderIntent.approval_request_id == locked.id))
    if existing is not None:
        return existing
    intent = OrderIntent(
        tenant_id=locked.tenant_id,
        run_id=locked.run_id,
        approval_request_id=locked.id,
        supplier_id=locked.supplier_id,
        quote_id=locked.quote_id,
        intent_key=new_intent_key(locked.run_id),
        approved_fingerprint=locked.fingerprint,
        max_amount=locked.max_amount,
        status="approved",
    )
    session.add(intent)
    session.flush()
    locked.status = "consumed"
    locked.consumed_by_intent_id = intent.id
    audit(
        session,
        locked.tenant_id,
        actor_type="worker",
        actor_id=worker_id,
        action="order_intent.created",
        entity_type="order_intent",
        entity_id=intent.id,
        run_id=locked.run_id,
        data={"approval_request_id": str(locked.id), "intent_key": intent.intent_key},
    )
    return intent


def transition(
    session: Session,
    intent_id: uuid.UUID,
    to: str,
    *,
    actor: str,
    reason: str | None = None,
    expect: tuple[str, ...] | None = None,
) -> OrderIntent:
    intent = session.scalar(select(OrderIntent).where(OrderIntent.id == intent_id).with_for_update())
    if intent is None:
        raise LedgerError("INTENT_NOT_FOUND", "Order intent not found")
    if expect and intent.status not in expect:
        raise LedgerError("INVALID_TRANSITION", f"Intent is {intent.status}, expected one of {expect}")
    previous = intent.status
    intent.status = to
    intent.status_reason = reason
    if to == "submitting" and intent.submit_window_start is None:
        intent.submit_window_start = datetime.now(UTC)
    session.flush()  # the trigger validates here
    audit(
        session,
        intent.tenant_id,
        actor_type="worker" if actor.startswith("worker") else "user",
        actor_id=actor,
        action=f"order_intent.{to}",
        entity_type="order_intent",
        entity_id=intent.id,
        run_id=intent.run_id,
        data={"from": previous, "to": to, "reason": reason},
    )
    return intent


def begin_attempt(session: Session, intent: OrderIntent, worker_id: str) -> OrderAttempt:
    n = (session.scalar(select(func.max(OrderAttempt.attempt_no)).where(OrderAttempt.intent_id == intent.id)) or 0) + 1
    attempt = OrderAttempt(tenant_id=intent.tenant_id, intent_id=intent.id, attempt_no=n, worker_id=worker_id)
    session.add(attempt)
    session.flush()
    return attempt
