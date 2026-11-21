"""Approval requests bound to an exact purchase fingerprint, and authenticated decisions.

Only an authenticated user holding the approver role (and, by default policy, not the
requester) can decide. Browser content and model output can never create or alter approvals.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.audit import audit, run_event
from ..core.models import (
    Approval,
    ApprovalRequest,
    PolicyDecision,
    PolicyVersion,
    ProcurementRequest,
    Quote,
    Supplier,
)
from ..quotes.normalize import CART_FIELDS, sha256_hex


class ApprovalError(Exception):
    def __init__(self, code: str, message: str, status: int = 409):
        super().__init__(message)
        self.code = code
        self.status = status


def quote_cart_view(q: Quote, supplier_key: str) -> dict[str, Any]:
    view = {
        "supplier_key": supplier_key,
        "sku": q.sku,
        "quantity": q.quantity,
        "unit_price": q.unit_price,
        "discount": q.discount,
        "tax": q.tax,
        "shipping": q.shipping,
        "total": q.total,
        "currency": q.currency,
        "delivery_date": q.delivery_date,
        "address_ref": q.address_ref,
        "supplier_quote_ref": q.supplier_quote_ref,
    }
    return {k: _s(view[k]) for k in CART_FIELDS}


def _s(v: Any) -> Any:
    if isinstance(v, Decimal):
        return f"{v:.2f}"
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return v


def build_binding(req: ProcurementRequest, quote: Quote, supplier: Supplier, policy: PolicyVersion) -> dict[str, Any]:
    cart = quote_cart_view(quote, supplier.key)
    return {
        "request_id": str(req.id),
        "request_version": req.version,
        "supplier_id": str(supplier.id),
        "supplier_key": supplier.key,
        "quote_id": str(quote.id),
        "quote_hash": quote.canonical_hash,
        "cart": cart,
        "cart_fingerprint": sha256_hex(cart),
        "quantity": quote.quantity,
        "max_amount": _s(quote.total),
        "currency": quote.currency,
        "delivery_deadline": req.delivery_deadline.isoformat(),
        "address_ref": req.address_ref,
        "policy_version_id": str(policy.id),
        "policy_version": policy.version,
    }


def create_request(
    session: Session,
    *,
    run_id: uuid.UUID,
    req: ProcurementRequest,
    quote: Quote,
    supplier: Supplier,
    policy: PolicyVersion,
    supersedes: ApprovalRequest | None = None,
    reason: dict[str, Any] | None = None,
) -> ApprovalRequest:
    binding = build_binding(req, quote, supplier, policy)
    ttl = int(policy.rules.get("approval_ttl_seconds", 3600))
    ar = ApprovalRequest(
        tenant_id=req.tenant_id,
        run_id=run_id,
        request_id=req.id,
        request_version=req.version,
        quote_id=quote.id,
        supplier_id=supplier.id,
        requester_id=req.requester_id,
        binding=binding,
        fingerprint=sha256_hex(binding),
        cart_fingerprint=binding["cart_fingerprint"],
        max_amount=quote.total,
        currency=quote.currency,
        quantity=quote.quantity,
        delivery_deadline=req.delivery_deadline,
        address_ref=req.address_ref,
        policy_version_id=policy.id,
        status="pending",
        expires_at=datetime.now(UTC) + timedelta(seconds=ttl),
        supersedes_id=supersedes.id if supersedes else None,
        invalidation=reason,
    )
    session.add(ar)
    session.flush()
    audit(
        session,
        req.tenant_id,
        actor_type="agent",
        actor_id=None,
        action="approval.requested",
        entity_type="approval_request",
        entity_id=ar.id,
        run_id=run_id,
        data={
            "supplier": supplier.key,
            "total": binding["max_amount"],
            "supersedes": str(supersedes.id) if supersedes else None,
        },
    )
    run_event(
        session,
        req.tenant_id,
        run_id,
        "approval_requested",
        {
            "approval_request_id": str(ar.id),
            "supplier": supplier.key,
            "total": binding["max_amount"],
            "replaces": str(supersedes.id) if supersedes else None,
            "changes": (reason or {}).get("changes"),
        },
    )
    return ar


def invalidate(session: Session, ar: ApprovalRequest, changes: list[dict[str, str]], why: str) -> None:
    locked = session.scalar(select(ApprovalRequest).where(ApprovalRequest.id == ar.id).with_for_update())
    if locked.status in ("pending", "approved"):
        locked.status = "invalidated"
        locked.invalidation = {"reason": why, "changes": changes, "at": datetime.now(UTC).isoformat()}
        audit(
            session,
            locked.tenant_id,
            actor_type="agent",
            actor_id=None,
            action="approval.invalidated",
            entity_type="approval_request",
            entity_id=locked.id,
            run_id=locked.run_id,
            data={"reason": why, "changes": changes},
        )
        run_event(
            session,
            locked.tenant_id,
            locked.run_id,
            "approval_invalidated",
            {"approval_request_id": str(locked.id), "reason": why, "changes": changes},
        )


def decide(
    session: Session,
    *,
    approval_request_id: uuid.UUID,
    approver_id: uuid.UUID,
    approver_roles: frozenset[str],
    decision: str,
    reason: str,
    soft_overrides: list[dict[str, str]] | None = None,
) -> Approval:
    """Idempotent: deciding the same request again with the same decision returns the existing record."""
    if "approver" not in approver_roles:
        raise ApprovalError("FORBIDDEN_ROLE", "Only approvers can decide", 403)
    if decision not in ("approved", "rejected"):
        raise ApprovalError("VALIDATION_FAILED", "decision must be approved or rejected", 422)
    ar = session.scalar(select(ApprovalRequest).where(ApprovalRequest.id == approval_request_id).with_for_update())
    if ar is None:
        raise ApprovalError("NOT_FOUND", "Approval request not found", 404)
    existing = session.scalar(select(Approval).where(Approval.approval_request_id == ar.id))
    if existing is not None:
        if existing.decision == decision and existing.approver_id == approver_id:
            return existing
        raise ApprovalError("APPROVAL_NOT_PENDING", "This approval request has already been decided")
    if ar.status != "pending":
        raise ApprovalError("APPROVAL_NOT_PENDING", f"Approval request is {ar.status}")
    policy = session.get(PolicyVersion, ar.policy_version_id)
    if policy.rules.get("require_distinct_approver", True) and ar.requester_id == approver_id:
        raise ApprovalError("APPROVER_IS_REQUESTER", "The requester cannot approve their own purchase", 403)
    now = datetime.now(UTC)
    if ar.expires_at <= now:
        ar.status = "expired"
        session.flush()
        raise ApprovalError("APPROVAL_EXPIRED", "Approval request expired; the agent will request a fresh one")
    evaluation = session.scalar(
        select(PolicyDecision).where(PolicyDecision.quote_id == ar.quote_id).order_by(PolicyDecision.created_at.desc())
    )
    if decision == "approved" and (evaluation is None or not evaluation.eligible):
        raise ApprovalError("QUOTE_INELIGIBLE", "The bound quote does not pass hard policy rules", 409)
    quote = session.get(Quote, ar.quote_id)
    if quote.canonical_hash != ar.binding["quote_hash"]:
        raise ApprovalError("CONFLICT", "Quote no longer matches the approval binding")
    approval = Approval(
        tenant_id=ar.tenant_id,
        approval_request_id=ar.id,
        approver_id=approver_id,
        decision=decision,
        reason=reason[:2000],
        approved_fingerprint=ar.fingerprint,
        policy_evaluation=evaluation.results if evaluation else [],
        soft_overrides=soft_overrides or [],
        expires_at=ar.expires_at,
    )
    session.add(approval)
    ar.status = decision
    session.flush()
    audit(
        session,
        ar.tenant_id,
        actor_type="user",
        actor_id=approver_id,
        action=f"approval.{decision}",
        entity_type="approval_request",
        entity_id=ar.id,
        run_id=ar.run_id,
        data={"reason": reason[:500], "fingerprint": ar.fingerprint, "soft_overrides": soft_overrides or []},
    )
    run_event(session, ar.tenant_id, ar.run_id, f"approval_{decision}", {"approval_request_id": str(ar.id)})
    return approval
