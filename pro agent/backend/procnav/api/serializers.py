"""Explicit response shapes. Storage paths, secrets and full addresses are never serialized."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ..core.models import (
    ApprovalRequest,
    BrowserStep,
    EvidenceArtifact,
    OrderIntent,
    PolicyDecision,
    ProcurementRequest,
    ProcurementRun,
    Quote,
    Supplier,
    SupplierOrder,
)


def money(v: Decimal | None) -> str | None:
    return f"{v:.2f}" if v is not None else None


def iso(v) -> str | None:
    return v.isoformat() if v is not None else None


def request_out(r: ProcurementRequest) -> dict[str, Any]:
    return {
        "id": str(r.id),
        "title": r.title,
        "canonical_product_id": r.canonical_product_id,
        "spec_requirements": r.spec_requirements,
        "quantity": r.quantity,
        "currency": r.currency,
        "budget_total": money(r.budget_total),
        "address_ref": r.address_ref,
        "delivery_deadline": iso(r.delivery_deadline),
        "allowed_supplier_ids": r.allowed_supplier_ids,
        "status": r.status,
        "version": r.version,
        "requester_id": str(r.requester_id),
        "created_at": iso(r.created_at),
    }


def run_out(r: ProcurementRun) -> dict[str, Any]:
    return {
        "id": str(r.id),
        "request_id": str(r.request_id),
        "status": r.status,
        "phase": r.phase,
        "mode": r.mode,
        "simulated_model": r.mode == "fixture",
        "model_name": r.model_name,
        "workflow": r.workflow,
        "action_count": r.action_count,
        "active_ms": r.active_ms,
        "waiting_ms": r.waiting_ms,
        "model_cost": f"{r.model_cost:.6f}",
        "model_input_tokens": r.model_input_tokens,
        "model_output_tokens": r.model_output_tokens,
        "retries": r.retries,
        "current_supplier": r.current_supplier,
        "selected_quote_id": str(r.selected_quote_id) if r.selected_quote_id else None,
        "approval_request_id": str(r.approval_request_id) if r.approval_request_id else None,
        "order_intent_id": str(r.order_intent_id) if r.order_intent_id else None,
        "handoff": r.handoff,
        "outcome": r.outcome,
        "summary": r.summary,
        "error_code": r.error_code,
        "cancel_requested": r.cancel_requested,
        "pause_requested": r.pause_requested,
        "started_at": iso(r.started_at),
        "finished_at": iso(r.finished_at),
        "created_at": iso(r.created_at),
    }


def step_out(s: BrowserStep) -> dict[str, Any]:
    return {
        "id": str(s.id),
        "seq": s.seq,
        "supplier": s.supplier_key,
        "tool": s.tool,
        "side_effect": s.side_effect,
        "input": s.input,
        "status": s.status,
        "observation": s.observation,
        "error_code": s.error_code,
        "url": s.url,
        "evidence_ids": s.evidence_ids,
        "explanation": s.explanation,
        "decided_by": s.decided_by,
        "started_at": iso(s.started_at),
        "duration_ms": s.duration_ms,
    }


def quote_out(q: Quote, supplier: Supplier, decision: PolicyDecision | None) -> dict[str, Any]:
    age = None
    if q.retrieved_at:
        from datetime import UTC, datetime

        age = int((datetime.now(UTC) - q.retrieved_at).total_seconds())
    return {
        "id": str(q.id),
        "version": q.version,
        "supersedes_id": str(q.supersedes_id) if q.supersedes_id else None,
        "supplier": {
            "id": str(supplier.id),
            "key": supplier.key,
            "name": supplier.name,
            "synthetic": supplier.is_simulated,
        },
        "sku": q.sku,
        "product_name": q.product_name,
        "canonical_id": q.canonical_id,
        "spec": q.normalized_spec,
        "quantity": q.quantity,
        "pack_size": q.pack_size,
        "stock_observed": q.stock_observed,
        "unit_price": money(q.unit_price),
        "subtotal": money(q.subtotal),
        "discount": money(q.discount),
        "tax": money(q.tax),
        "shipping": money(q.shipping),
        "total": money(q.total),
        "currency": q.currency,
        "price_basis": q.price_basis,
        "tax_basis": q.tax_basis,
        "delivery_date": iso(q.delivery_date),
        "delivery_confidence": q.delivery_confidence,
        "address_ref": q.address_ref,
        "supplier_quote_ref": q.supplier_quote_ref,
        "source_url": q.source_url,
        "retrieved_at": iso(q.retrieved_at),
        "age_seconds": age,
        "expires_at": iso(q.expires_at),
        "evidence_ids": q.evidence_ids,
        "extraction_method": q.extraction_method,
        "issues": q.issues,
        "canonical_hash": q.canonical_hash,
        "eligible": decision.eligible if decision else None,
        "policy_results": decision.results if decision else [],
        "policy_context": decision.context if decision else None,
    }


def approval_out(a: ApprovalRequest) -> dict[str, Any]:
    return {
        "id": str(a.id),
        "run_id": str(a.run_id),
        "request_id": str(a.request_id),
        "quote_id": str(a.quote_id),
        "supplier_id": str(a.supplier_id),
        "requester_id": str(a.requester_id),
        "binding": a.binding,
        "fingerprint": a.fingerprint,
        "cart_fingerprint": a.cart_fingerprint,
        "max_amount": money(a.max_amount),
        "currency": a.currency,
        "quantity": a.quantity,
        "delivery_deadline": iso(a.delivery_deadline),
        "address_ref": a.address_ref,
        "status": a.status,
        "expires_at": iso(a.expires_at),
        "supersedes_id": str(a.supersedes_id) if a.supersedes_id else None,
        "invalidation": a.invalidation,
        "created_at": iso(a.created_at),
    }


def intent_out(i: OrderIntent, order: SupplierOrder | None) -> dict[str, Any]:
    return {
        "id": str(i.id),
        "run_id": str(i.run_id),
        "approval_request_id": str(i.approval_request_id),
        "quote_id": str(i.quote_id),
        "intent_key": i.intent_key,
        "status": i.status,
        "status_reason": i.status_reason,
        "max_amount": money(i.max_amount),
        "approved_fingerprint": i.approved_fingerprint,
        "created_at": iso(i.created_at),
        "updated_at": iso(i.updated_at),
        "supplier_order": None
        if order is None
        else {
            "supplier_order_ref": order.supplier_order_ref,
            "sku": order.sku,
            "quantity": order.quantity,
            "total": money(order.total),
            "currency": order.currency,
            "delivery_date": iso(order.delivery_date),
            "reconciled_via": order.reconciled_via,
            "verified": order.verified,
            "verification": order.verification,
            "receipt_evidence_id": str(order.receipt_evidence_id) if order.receipt_evidence_id else None,
        },
    }


def evidence_out(e: EvidenceArtifact) -> dict[str, Any]:
    return {
        "id": str(e.id),
        "run_id": str(e.run_id) if e.run_id else None,
        "kind": e.kind,
        "label": e.label,
        "content_type": e.content_type,
        "size_bytes": e.size_bytes,
        "sha256": e.sha256,
        "redacted": e.redacted,
        "retention_until": iso(e.retention_until),
        "created_at": iso(e.created_at),
    }
