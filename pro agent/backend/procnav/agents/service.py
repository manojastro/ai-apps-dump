"""Application services for requests, runs, cancellation and human resolution."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.audit import audit, run_event
from ..core.config import get_settings
from ..core.models import (
    ApprovalRequest,
    PolicyVersion,
    ProcurementRequest,
    ProcurementRun,
    RequestItem,
    Supplier,
)
from ..orders import ledger
from ..workers import jobs
from .context import load_master_data


class ServiceError(Exception):
    def __init__(self, status: int, code: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details or {}


class RequestIn(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    canonical_product_id: str = Field(max_length=64)
    min_ram_gb: int = Field(ge=1, le=1024)
    min_ssd_gb: int = Field(ge=1, le=65536)
    quantity: int = Field(ge=1, le=1000)
    currency: str = Field(default="INR", pattern="^[A-Z]{3}$")
    budget_total: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    address_ref: str = Field(max_length=64)
    delivery_deadline: date
    allowed_suppliers: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("delivery_deadline")
    @classmethod
    def _future(cls, v: date) -> date:
        if v <= datetime.now(UTC).date():
            raise ValueError("delivery_deadline must be in the future")
        return v


def create_request(
    db: Session, tenant_id: uuid.UUID, requester_id: uuid.UUID, data: RequestIn, idempotency_key: str | None
) -> ProcurementRequest:
    if idempotency_key:
        existing = db.scalar(
            select(ProcurementRequest).where(
                ProcurementRequest.requester_id == requester_id, ProcurementRequest.idempotency_key == idempotency_key
            )
        )
        if existing:
            return existing
    _, canonical = load_master_data()
    if data.canonical_product_id not in canonical:
        raise ServiceError(422, "REQUEST_INCOMPLETE", "Unknown canonical product", {"field": "canonical_product_id"})
    policy = db.scalar(select(PolicyVersion).where(PolicyVersion.active.is_(True)))
    if data.address_ref not in policy.rules.get("destinations", {}):
        raise ServiceError(422, "REQUEST_INCOMPLETE", "Unknown destination reference", {"field": "address_ref"})
    suppliers = db.scalars(select(Supplier).where(Supplier.enabled.is_(True))).all()
    by_key = {s.key: s for s in suppliers}
    keys = data.allowed_suppliers or sorted(by_key)
    unknown = [k for k in keys if k not in by_key]
    if unknown:
        raise ServiceError(422, "VALIDATION_FAILED", "Unknown suppliers", {"suppliers": unknown})
    base = canonical[data.canonical_product_id]
    spec = {
        "family": base["family"],
        "cpu": base["cpu"],
        "min_ram_gb": data.min_ram_gb,
        "min_ssd_gb": data.min_ssd_gb,
        "storage_type": base["storage_type"],
        "os": base["os"],
    }
    req = ProcurementRequest(
        tenant_id=tenant_id,
        requester_id=requester_id,
        title=data.title,
        canonical_product_id=data.canonical_product_id,
        spec_requirements=spec,
        quantity=data.quantity,
        currency=data.currency,
        budget_total=data.budget_total,
        address_ref=data.address_ref,
        delivery_deadline=data.delivery_deadline,
        allowed_supplier_ids=[str(by_key[k].id) for k in keys],
        status="submitted",
        version=1,
        idempotency_key=idempotency_key,
    )
    db.add(req)
    db.flush()
    db.add(
        RequestItem(
            tenant_id=tenant_id,
            request_id=req.id,
            canonical_product_id=data.canonical_product_id,
            quantity=data.quantity,
            spec=spec,
        )
    )
    audit(
        db,
        tenant_id,
        actor_type="user",
        actor_id=requester_id,
        action="request.created",
        entity_type="request",
        entity_id=req.id,
        data={"title": data.title, "quantity": data.quantity},
    )
    return req


def start_run(
    db: Session,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    request_id: uuid.UUID,
    *,
    idempotency_key: str | None,
    workflow: str = "bounded",
    mode: str | None = None,
    fixture_options: dict[str, Any] | None = None,
) -> ProcurementRun:
    s = get_settings()
    req = db.get(ProcurementRequest, request_id)
    if req is None:
        raise ServiceError(404, "NOT_FOUND", "Request not found")
    if idempotency_key:
        existing = db.scalar(
            select(ProcurementRun).where(
                ProcurementRun.request_id == request_id, ProcurementRun.idempotency_key == idempotency_key
            )
        )
        if existing:
            return existing
    active = db.scalar(
        select(ProcurementRun).where(
            ProcurementRun.request_id == request_id,
            ProcurementRun.status.in_(
                (
                    "queued",
                    "running",
                    "awaiting_approval",
                    "submitting",
                    "reconciling",
                    "cancellation_requested",
                    "paused_for_human",
                )
            ),
        )
    )
    if active:
        raise ServiceError(409, "RUN_ACTIVE", "This request already has an active run", {"run_id": str(active.id)})
    mode = mode or s.model_mode
    if mode == "real" and not s.model_api_key:
        raise ServiceError(422, "VALIDATION_FAILED", "Real-model mode is not configured")
    policy = db.scalar(select(PolicyVersion).where(PolicyVersion.active.is_(True)))
    run = ProcurementRun(
        tenant_id=tenant_id,
        request_id=request_id,
        request_version=req.version,
        policy_version_id=policy.id,
        status="queued",
        phase="queued",
        mode=mode,
        model_name=s.model_name if mode == "real" else "fixture-deterministic-v1",
        workflow=workflow,
        fixture_options=fixture_options or {},
        created_by=user_id,
        idempotency_key=idempotency_key,
    )
    db.add(run)
    db.flush()
    jobs.enqueue(db, tenant_id=tenant_id, run_id=run.id, kind="start", dedupe_key=f"start:{run.id}")
    req.status = "in_progress"
    audit(
        db,
        tenant_id,
        actor_type="user",
        actor_id=user_id,
        action="run.started",
        entity_type="run",
        entity_id=run.id,
        run_id=run.id,
        data={"mode": mode, "workflow": workflow},
    )
    run_event(
        db, tenant_id, run.id, "run_queued", {"mode": mode, "workflow": workflow, "simulated_model": mode == "fixture"}
    )
    return run


def enqueue_resume(db: Session, run: ProcurementRun, reason: str, payload: dict[str, Any] | None = None) -> None:
    jobs.enqueue(
        db,
        tenant_id=run.tenant_id,
        run_id=run.id,
        kind="resume",
        dedupe_key=f"resume:{run.id}:{reason}:{uuid.uuid4().hex[:8]}",
        payload=payload or {},
    )


def cancel_run(db: Session, run: ProcurementRun, user_id: uuid.UUID) -> str:
    """Cancellation never pretends to cancel an external order. In-flight submissions become
    cancellation_requested until the supplier outcome is known."""
    if run.status in ("completed", "failed", "canceled", "rejected", "no_eligible_offer", "needs_clarification"):
        raise ServiceError(409, "RUN_NOT_CANCELABLE", f"Run is already {run.status}")
    run.cancel_requested = True
    intent = ledger.intent_for_run(db, run.id)
    effect = "cancel_requested"
    if intent is not None and intent.status == "submitting":
        ledger.transition(
            db,
            intent.id,
            "cancellation_requested",
            actor=str(user_id),
            reason="user requested cancellation during submission",
        )
        run.status = "cancellation_requested"
        effect = "cancellation_requested_pending_supplier_outcome"
    elif intent is not None and intent.status in ("submitted", "unknown", "reconciled"):
        effect = "order_may_exist_reconcile_first"
    elif run.status in ("awaiting_approval", "paused_for_human", "queued"):
        run.status = "canceled"
        run.outcome = "canceled"
        run.finished_at = datetime.now(UTC)
        if run.approval_request_id:
            ar = db.get(ApprovalRequest, run.approval_request_id)
            if ar and ar.status in ("pending", "approved"):
                from ..approvals.service import invalidate

                invalidate(db, ar, [], "run_canceled")
        effect = "canceled"
    audit(
        db,
        run.tenant_id,
        actor_type="user",
        actor_id=user_id,
        action="run.cancel_requested",
        entity_type="run",
        entity_id=run.id,
        run_id=run.id,
        data={"effect": effect},
    )
    run_event(db, run.tenant_id, run.id, "cancel_requested", {"effect": effect})
    return effect
