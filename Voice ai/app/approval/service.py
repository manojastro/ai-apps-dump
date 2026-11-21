"""Human approval queue. Agents can request approvals; only staff (via decide) can grant them."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select

from app import clock
from app.audit import log as audit
from app.config import get_settings
from app.data.db import session
from app.data.models import Approval, Communication, StaffUser, SupplyOrder
from app.queue import outbox

# Which staff role must decide each kind of approval.
KIND_ROLE = {
    "communication": "front_desk",
    "booking_exception": "front_desk",
    "followup_booking": "front_desk",
    "supply_order": "inventory",
    "checkin_review": "nurse",
}


class ApprovalError(Exception):
    pass


def default_expiry(kind: str) -> datetime:
    return clock.now() + timedelta(hours=get_settings().approval_ttl_hours)


def decide(approval_id: str, username: str, approve: bool, reason: str | None = None) -> Approval:
    """Record a staff decision. Rejections need a reason. Idempotent only in the sense that a second
    decision on a non-pending approval is refused."""
    reason = (reason or "").strip() or None
    with session() as s:
        user = s.get(StaffUser, username)
        ap = s.get(Approval, approval_id)
        if user is None:
            raise ApprovalError("unknown staff user")
        if ap is None:
            raise ApprovalError("unknown approval")
        if user.role != ap.required_role:
            audit.write(actor=f"staff:{username}", tool="approval.decide", args={"id": approval_id}, status="denied",
                        workflow_id=ap.workflow_id, detail=f"role {user.role} cannot decide {ap.required_role} items")
            raise ApprovalError(f"role '{user.role}' may not decide '{ap.kind}' approvals")
        if ap.status != "pending":
            raise ApprovalError(f"approval is already {ap.status}")
        if ap.expires_at <= clock.now():
            ap.status = "expired"
            s.flush()
            raise ApprovalError("approval has expired")
        if not approve and not reason:
            raise ApprovalError("a reason is required when rejecting")
        ap.status = "approved" if approve else "rejected"
        ap.decided_by, ap.decided_at, ap.decision_reason = username, clock.now(), reason
        _apply_side_effects(s, ap)
        wf_id, ap_id, status = ap.workflow_id, ap.id, ap.status
    audit.write(actor=f"staff:{username}", tool="approval.decide", args={"id": approval_id, "approve": approve},
                status="ok", workflow_id=wf_id, detail=f"{status}" + (f": {reason}" if reason else ""))
    outbox.enqueue("APPROVAL_DECIDED", {"approval_id": ap_id, "workflow_id": wf_id}, dedupe_key=f"approval:{ap_id}")
    with session() as s:
        return s.get(Approval, approval_id)  # type: ignore[return-value]


def _apply_side_effects(s, ap: Approval) -> None:
    if ap.kind == "communication":
        c = s.get(Communication, ap.ref_id)
        if c and c.status == "draft":
            c.status = "approved" if ap.status == "approved" else "rejected"
    elif ap.kind == "supply_order":
        o = s.get(SupplyOrder, ap.ref_id)
        if o and o.status == "pending_approval":
            o.status = "approved" if ap.status == "approved" else "rejected"


def expire_overdue() -> list[str]:
    """Mark pending approvals past their deadline as expired; wake their workflows."""
    now = clock.now()
    expired: list[tuple[str, str | None]] = []
    with session() as s:
        for ap in s.scalars(select(Approval).where(Approval.status == "pending", Approval.expires_at <= now)):
            ap.status = "expired"
            ap.decision_reason = "expired without decision"
            if ap.kind == "communication":
                c = s.get(Communication, ap.ref_id)
                if c and c.status == "draft":
                    c.status = "rejected"
            elif ap.kind == "supply_order":
                o = s.get(SupplyOrder, ap.ref_id)
                if o and o.status == "pending_approval":
                    o.status = "rejected"
            expired.append((ap.id, ap.workflow_id))
    for ap_id, wf_id in expired:
        audit.write(actor="system", tool="approval.expire", args={"id": ap_id}, status="ok", workflow_id=wf_id)
        outbox.enqueue("APPROVAL_DECIDED", {"approval_id": ap_id, "workflow_id": wf_id}, dedupe_key=f"approval:{ap_id}")
    return [a for a, _ in expired]


def pending_for_role(role: str) -> list[Approval]:
    with session() as s:
        return list(s.scalars(select(Approval).where(Approval.status == "pending", Approval.required_role == role)
                              .order_by(Approval.created_at, Approval.id)))


def get(approval_id: str) -> Approval | None:
    with session() as s:
        return s.get(Approval, approval_id)
