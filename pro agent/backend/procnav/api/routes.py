"""HTTP API. Every handler derives tenant scope from the server-side session, never from input."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from ..agents import service
from ..approvals import service as approvals
from ..auth.deps import (
    CSRF_COOKIE,
    SESSION_COOKIE,
    current_principal,
    login_limiter,
    mutation_limiter,
    require_role,
)
from ..auth.service import Principal, authenticate, revoke
from ..core.audit import audit, run_event
from ..core.config import get_settings
from ..core.db import global_session, tenant_session
from ..core.models import (
    ApprovalRequest,
    AuditEvent,
    BrowserStep,
    EvalRun,
    EvidenceArtifact,
    OrderIntent,
    PolicyDecision,
    PolicyException,
    PolicyVersion,
    ProcurementRequest,
    ProcurementRun,
    Quote,
    RunEvent,
    Supplier,
    SupplierOrder,
    WorkerHeartbeat,
)
from ..evidence import store
from ..orders import ledger
from . import idempotency
from . import serializers as ser
from .errors import ApiError
from .exports import comparison_csv, run_summary_pdf

router = APIRouter(prefix="/api")


def _svc(err: service.ServiceError) -> ApiError:
    return ApiError(err.status, err.code, err.message, err.details)


def _page(limit: int, offset: int) -> tuple[int, int]:
    return max(1, min(limit, 100)), max(0, offset)


def _uuid(value: str, what: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise ApiError(404, "NOT_FOUND", f"{what} not found") from exc


# ------------------------------------------------------------------------------------------- health


@router.get("/health", tags=["system"])
def health():
    with global_session() as s:
        s.execute(select(1))
        beats = s.scalars(select(WorkerHeartbeat)).all()
    now = datetime.now(UTC)
    workers = [
        {"worker_id": b.worker_id, "age_seconds": int((now - b.seen_at).total_seconds()), "active_jobs": b.active_jobs}
        for b in beats
    ]
    return {
        "ok": True,
        "db": "ok",
        "workers_alive": sum(1 for w in workers if w["age_seconds"] < 60),
        "mode": get_settings().model_mode,
        "dry_run": get_settings().dry_run,
    }


# ------------------------------------------------------------------------------------------- auth


class LoginIn(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(max_length=500)
    tenant: str | None = Field(default=None, max_length=64)


def _principal_out(p: Principal) -> dict[str, Any]:
    return {
        "user": {"id": str(p.user_id), "email": p.email, "display_name": p.display_name},
        "tenant": {"id": str(p.tenant_id), "slug": p.tenant_slug, "name": p.tenant_name},
        "roles": sorted(p.roles),
        "csrf_token": p.csrf_token,
    }


@router.post("/auth/login", tags=["auth"], responses={401: {"description": "AUTH_INVALID"}})
def login(body: LoginIn, request: Request, response: Response):
    login_limiter.check(f"{request.client.host if request.client else '-'}:{body.email.lower()}")
    result = authenticate(body.email, body.password, body.tenant)
    if result is None:
        raise ApiError(401, "AUTH_INVALID", "Invalid email or password.")
    token, principal = result
    s = get_settings()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        secure=s.cookie_secure,
        samesite="lax",
        max_age=s.session_ttl_seconds,
        path="/",
    )
    response.set_cookie(
        CSRF_COOKIE,
        principal.csrf_token,
        httponly=False,
        secure=s.cookie_secure,
        samesite="lax",
        max_age=s.session_ttl_seconds,
        path="/",
    )
    with tenant_session(principal.tenant_id) as db:
        audit(
            db,
            principal.tenant_id,
            actor_type="user",
            actor_id=principal.user_id,
            action="auth.login",
            entity_type="user",
            entity_id=principal.user_id,
        )
    return _principal_out(principal)


@router.post("/auth/logout", tags=["auth"])
def logout(request: Request, response: Response, principal: Principal = Depends(current_principal)):
    revoke(request.cookies.get(SESSION_COOKIE))
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")
    return {"ok": True}


@router.get("/auth/session", tags=["auth"])
def session(principal: Principal = Depends(current_principal)):
    return _principal_out(principal)


# ------------------------------------------------------------------------------------------- reference data


@router.get("/catalog/products", tags=["reference"])
def canonical_products(principal: Principal = Depends(current_principal)):
    from ..agents.context import load_master_data

    _, canonical = load_master_data()
    return {"products": [{"id": k, **v} for k, v in canonical.items()]}


@router.get("/suppliers", tags=["suppliers"])
def list_suppliers(principal: Principal = Depends(current_principal)):
    with tenant_session(principal.tenant_id) as db:
        rows = db.scalars(select(Supplier).order_by(Supplier.key)).all()
        return {
            "suppliers": [
                {
                    "id": str(s.id),
                    "key": s.key,
                    "name": s.name,
                    "base_url": s.base_url,
                    "allowed_origins": s.allowed_origins,
                    "adapter": s.adapter,
                    "synthetic": s.is_simulated,
                    "enabled": s.enabled,
                    "eligibility_status": s.eligibility_status,
                    "status_api_supported": s.status_api_supported,
                    "conditional_submit_supported": s.conditional_submit_supported,
                }
                for s in rows
            ]
        }


class SupplierPatch(BaseModel):
    enabled: bool | None = None
    eligibility_status: str | None = Field(default=None, pattern="^(approved|suspended)$")


@router.patch("/suppliers/{supplier_id}", tags=["suppliers"])
def patch_supplier(supplier_id: str, body: SupplierPatch, principal: Principal = Depends(require_role("admin"))):
    with tenant_session(principal.tenant_id) as db:
        sup = db.get(Supplier, _uuid(supplier_id, "supplier"))
        if sup is None:
            raise ApiError(404, "NOT_FOUND", "supplier not found")
        changes = body.model_dump(exclude_none=True)
        for k, v in changes.items():
            setattr(sup, k, v)
        audit(
            db,
            principal.tenant_id,
            actor_type="user",
            actor_id=principal.user_id,
            action="supplier.updated",
            entity_type="supplier",
            entity_id=sup.id,
            data=changes,
        )
        return {"ok": True, "changes": changes}


@router.get("/policies", tags=["policies"])
def list_policies(principal: Principal = Depends(current_principal)):
    with tenant_session(principal.tenant_id) as db:
        rows = db.scalars(select(PolicyVersion).order_by(PolicyVersion.version.desc())).all()
        return {
            "policies": [
                {
                    "id": str(p.id),
                    "version": p.version,
                    "active": p.active,
                    "rules": p.rules,
                    "created_at": ser.iso(p.created_at),
                }
                for p in rows
            ]
        }


class PolicyIn(BaseModel):
    rules: dict[str, Any]


@router.post("/policies", tags=["policies"], status_code=201)
def create_policy(body: PolicyIn, principal: Principal = Depends(require_role("admin"))):
    from decimal import Decimal, InvalidOperation

    rules = body.rules
    required = {
        "allowed_currencies",
        "require_distinct_approver",
        "max_quote_age_seconds",
        "approval_ttl_seconds",
        "per_order_spending_limit",
        "destinations",
        "material_change_fields",
    }
    missing = required - rules.keys()
    if missing:
        raise ApiError(422, "VALIDATION_FAILED", "Policy is missing required keys", {"missing": sorted(missing)})
    try:
        Decimal(str(rules["per_order_spending_limit"]))
    except InvalidOperation as exc:
        raise ApiError(422, "VALIDATION_FAILED", "per_order_spending_limit must be a decimal") from exc
    if int(rules["approval_ttl_seconds"]) < 60:
        raise ApiError(422, "VALIDATION_FAILED", "approval_ttl_seconds must be >= 60")
    with tenant_session(principal.tenant_id) as db:
        latest = db.scalar(select(func.max(PolicyVersion.version))) or 0
        for p in db.scalars(select(PolicyVersion).where(PolicyVersion.active.is_(True))):
            p.active = False
        pv = PolicyVersion(
            tenant_id=principal.tenant_id, version=latest + 1, rules=rules, active=True, created_by=principal.user_id
        )
        db.add(pv)
        db.flush()
        audit(
            db,
            principal.tenant_id,
            actor_type="user",
            actor_id=principal.user_id,
            action="policy.activated",
            entity_type="policy_version",
            entity_id=pv.id,
            data={"version": pv.version},
        )
        return {"id": str(pv.id), "version": pv.version}


# ------------------------------------------------------------------------------------------- requests & runs


@router.post(
    "/requests",
    tags=["requests"],
    status_code=201,
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {
                        "title": "Ten business laptops for the Bengaluru team",
                        "canonical_product_id": "NW-PRO14-16-512",
                        "min_ram_gb": 16,
                        "min_ssd_gb": 512,
                        "quantity": 10,
                        "currency": "INR",
                        "budget_total": "500000.00",
                        "address_ref": "ADDR-BLR-01",
                        "delivery_deadline": "2026-10-14",
                        "allowed_suppliers": [],
                    }
                }
            }
        }
    },
)
def create_request(
    body: service.RequestIn, request: Request, principal: Principal = Depends(require_role("requester", "admin"))
):
    mutation_limiter.check(str(principal.user_id))
    key = idempotency.key_from(request)
    payload = body.model_dump(mode="json")
    with tenant_session(principal.tenant_id) as db:
        prior = idempotency.lookup(db, principal, "POST /api/requests", key, payload)
        if prior:
            return JSONResponse(prior["body"], status_code=prior["status"])
        try:
            req = service.create_request(db, principal.tenant_id, principal.user_id, body, key)
        except service.ServiceError as e:
            raise _svc(e) from e
        out = ser.request_out(req)
        idempotency.store(db, principal, "POST /api/requests", key, payload, 201, out)
        return out


@router.get("/requests", tags=["requests"])
def list_requests(limit: int = 25, offset: int = 0, principal: Principal = Depends(current_principal)):
    limit, offset = _page(limit, offset)
    with tenant_session(principal.tenant_id) as db:
        q = select(ProcurementRequest).order_by(ProcurementRequest.created_at.desc())
        if not (principal.has("approver") or principal.has("admin") or principal.has("viewer")):
            q = q.where(ProcurementRequest.requester_id == principal.user_id)
        rows = db.scalars(q.limit(limit).offset(offset)).all()
        out = []
        for r in rows:
            latest = db.scalar(
                select(ProcurementRun)
                .where(ProcurementRun.request_id == r.id)
                .order_by(ProcurementRun.created_at.desc())
                .limit(1)
            )
            out.append(ser.request_out(r) | {"latest_run": ser.run_out(latest) if latest else None})
        return {"items": out, "limit": limit, "offset": offset}


@router.get("/requests/{request_id}", tags=["requests"])
def get_request(request_id: str, principal: Principal = Depends(current_principal)):
    with tenant_session(principal.tenant_id) as db:
        r = db.get(ProcurementRequest, _uuid(request_id, "request"))
        if r is None:
            raise ApiError(404, "NOT_FOUND", "request not found")
        runs = db.scalars(
            select(ProcurementRun).where(ProcurementRun.request_id == r.id).order_by(ProcurementRun.created_at.desc())
        ).all()
        return ser.request_out(r) | {"runs": [ser.run_out(x) for x in runs]}


class RunIn(BaseModel):
    mode: str | None = Field(default=None, pattern="^(fixture|real)$")
    workflow: str = Field(default="bounded", pattern="^(bounded|single_pass)$")
    fixture_options: dict[str, Any] = Field(default_factory=dict)


ALLOWED_FIXTURE_OPTIONS = {"planted_bad_recommendation", "follow_injected_links"}


@router.post("/requests/{request_id}/runs", tags=["runs"], status_code=202)
def start_run(request_id: str, body: RunIn, request: Request, principal: Principal = Depends(current_principal)):
    if not (principal.has("requester") or principal.has("admin")):
        raise ApiError(403, "FORBIDDEN_ROLE", "Requires role: requester or admin.")
    if body.fixture_options and not principal.has("admin"):
        raise ApiError(403, "FORBIDDEN_ROLE", "Only administrators can set fixture options")
    unknown = set(body.fixture_options) - ALLOWED_FIXTURE_OPTIONS
    if unknown:
        raise ApiError(422, "VALIDATION_FAILED", "Unknown fixture options", {"options": sorted(unknown)})
    key = idempotency.key_from(request)
    payload = body.model_dump() | {"request_id": request_id}
    with tenant_session(principal.tenant_id) as db:
        prior = idempotency.lookup(db, principal, "POST /api/requests/{id}/runs", key, payload)
        if prior:
            return JSONResponse(prior["body"], status_code=prior["status"])
        req = db.get(ProcurementRequest, _uuid(request_id, "request"))
        if req is None or (req.requester_id != principal.user_id and not principal.has("admin")):
            raise ApiError(404, "NOT_FOUND", "request not found")
        try:
            run = service.start_run(
                db,
                principal.tenant_id,
                principal.user_id,
                req.id,
                idempotency_key=key,
                workflow=body.workflow,
                mode=body.mode,
                fixture_options=body.fixture_options,
            )
        except service.ServiceError as e:
            raise _svc(e) from e
        out = ser.run_out(run)
        idempotency.store(db, principal, "POST /api/requests/{id}/runs", key, payload, 202, out)
        return out


@router.get("/runs", tags=["runs"])
def list_runs(
    limit: int = 25, offset: int = 0, status: str | None = None, principal: Principal = Depends(current_principal)
):
    limit, offset = _page(limit, offset)
    with tenant_session(principal.tenant_id) as db:
        q = select(ProcurementRun).order_by(ProcurementRun.created_at.desc())
        if status:
            q = q.where(ProcurementRun.status == status)
        rows = db.scalars(q.limit(limit).offset(offset)).all()
        titles = {
            r.id: r.title
            for r in db.scalars(
                select(ProcurementRequest).where(ProcurementRequest.id.in_([x.request_id for x in rows]))
            )
        }
        return {
            "items": [ser.run_out(r) | {"request_title": titles.get(r.request_id)} for r in rows],
            "limit": limit,
            "offset": offset,
        }


def _run_or_404(db, run_id: str) -> ProcurementRun:
    run = db.get(ProcurementRun, _uuid(run_id, "run"))
    if run is None:
        raise ApiError(404, "NOT_FOUND", "run not found")
    return run


@router.get("/runs/{run_id}", tags=["runs"])
def get_run(run_id: str, principal: Principal = Depends(current_principal)):
    with tenant_session(principal.tenant_id) as db:
        run = _run_or_404(db, run_id)
        req = db.get(ProcurementRequest, run.request_id)
        return ser.run_out(run) | {
            "request": ser.request_out(req),
            "budgets": {
                "max_browser_actions": get_settings().max_browser_actions,
                "active_run_timeout_seconds": get_settings().active_run_timeout_seconds,
                "max_run_cost": f"{get_settings().max_run_cost}",
            },
        }


@router.get("/runs/{run_id}/steps", tags=["runs"])
def run_steps(run_id: str, principal: Principal = Depends(current_principal)):
    with tenant_session(principal.tenant_id) as db:
        run = _run_or_404(db, run_id)
        rows = db.scalars(select(BrowserStep).where(BrowserStep.run_id == run.id).order_by(BrowserStep.seq)).all()
        return {"items": [ser.step_out(s) for s in rows]}


def _events_after(tenant_id: uuid.UUID, run_id: uuid.UUID, after: int, limit: int = 200) -> list[dict[str, Any]]:
    with tenant_session(tenant_id) as db:
        rows = db.scalars(
            select(RunEvent).where(RunEvent.run_id == run_id, RunEvent.id > after).order_by(RunEvent.id).limit(limit)
        ).all()
        return [{"id": e.id, "type": e.type, "data": e.data, "at": ser.iso(e.created_at)} for e in rows]


@router.get(
    "/runs/{run_id}/events",
    tags=["runs"],
    description="Persisted run events. With Accept: text/event-stream returns SSE (reconnect with "
    "Last-Event-ID); otherwise JSON for polling with ?after=<last id>.",
)
async def run_events(run_id: str, request: Request, after: int = 0, principal: Principal = Depends(current_principal)):
    rid = _uuid(run_id, "run")
    with tenant_session(principal.tenant_id) as db:
        _run_or_404(db, run_id)
    last = int(request.headers.get("last-event-id") or after or 0)
    if "text/event-stream" not in request.headers.get("accept", ""):
        return {"items": await asyncio.to_thread(_events_after, principal.tenant_id, rid, last)}

    async def stream():
        cursor = last
        idle = 0
        while not await request.is_disconnected():
            items = await asyncio.to_thread(_events_after, principal.tenant_id, rid, cursor)
            for e in items:
                cursor = e["id"]
                yield f"id: {e['id']}\nevent: {e['type']}\ndata: {json.dumps(e, default=str)}\n\n"
            idle = 0 if items else idle + 1
            if idle and idle % 15 == 0:
                yield ": keep-alive\n\n"
            await asyncio.sleep(1.0)

    return StreamingResponse(
        stream(), media_type="text/event-stream", headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"}
    )


@router.post("/runs/{run_id}/cancel", tags=["runs"])
def cancel(run_id: str, principal: Principal = Depends(current_principal)):
    with tenant_session(principal.tenant_id) as db:
        run = _run_or_404(db, run_id)
        req = db.get(ProcurementRequest, run.request_id)
        if req.requester_id != principal.user_id and not principal.has("admin"):
            raise ApiError(403, "FORBIDDEN_ROLE", "Only the requester or an administrator can cancel")
        try:
            effect = service.cancel_run(db, run, principal.user_id)
        except service.ServiceError as e:
            raise _svc(e) from e
        return {"effect": effect, "status": run.status}


@router.post("/runs/{run_id}/pause", tags=["runs"])
def pause(run_id: str, principal: Principal = Depends(current_principal)):
    with tenant_session(principal.tenant_id) as db:
        run = _run_or_404(db, run_id)
        if run.status not in ("queued", "running"):
            raise ApiError(409, "INVALID_TRANSITION", f"Cannot pause a run that is {run.status}")
        run.pause_requested = True
        run_event(db, principal.tenant_id, run.id, "pause_requested", {"by": str(principal.user_id)})
        return {"effect": "will pause before the next browser action; submissions in progress are not interrupted"}


class ResumeIn(BaseModel):
    action: str = Field(default="retry", pattern="^(retry|skip|cancel)$")
    note: str = Field(default="", max_length=500)


@router.post("/runs/{run_id}/resume", tags=["runs"])
def resume(run_id: str, body: ResumeIn, principal: Principal = Depends(current_principal)):
    if not (principal.has("requester") or principal.has("admin")):
        raise ApiError(403, "FORBIDDEN_ROLE", "Requires role: requester or admin.")
    with tenant_session(principal.tenant_id) as db:
        run = _run_or_404(db, run_id)
        if run.status != "paused_for_human":
            raise ApiError(409, "INVALID_TRANSITION", f"Run is {run.status}, not paused")
        run.pause_requested = False
        service.enqueue_resume(db, run, "handoff", {"action": body.action})
        audit(
            db,
            principal.tenant_id,
            actor_type="user",
            actor_id=principal.user_id,
            action="run.resumed",
            entity_type="run",
            entity_id=run.id,
            run_id=run.id,
            data=body.model_dump(),
        )
        return {"ok": True, "action": body.action}


def _comparison(db, run: ProcurementRun) -> list[dict[str, Any]]:
    quotes = db.scalars(select(Quote).where(Quote.run_id == run.id).order_by(Quote.created_at)).all()
    out = []
    for q in quotes:
        sup = db.get(Supplier, q.supplier_id)
        dec = db.scalar(
            select(PolicyDecision)
            .where(PolicyDecision.quote_id == q.id)
            .order_by(PolicyDecision.created_at.desc())
            .limit(1)
        )
        out.append(ser.quote_out(q, sup, dec))
    eligible_first = sorted(
        out,
        key=lambda r: (not r["eligible"], float(r["total"] or 1e15), r["delivery_date"] or "9", r["supplier"]["key"]),
    )
    return eligible_first


@router.get("/runs/{run_id}/comparison", tags=["quotes"])
def comparison(run_id: str, principal: Principal = Depends(current_principal)):
    with tenant_session(principal.tenant_id) as db:
        run = _run_or_404(db, run_id)
        rows = _comparison(db, run)
        return {
            "run_id": str(run.id),
            "quotes": rows,
            "recommendation": (run.summary or {}).get("recommendation"),
            "selected_quote_id": str(run.selected_quote_id) if run.selected_quote_id else None,
            "ranking_rule": "eligible first; landed total ascending; then earliest delivery; then supplier key",
            "synthetic": True,
        }


@router.get("/runs/{run_id}/comparison.csv", tags=["quotes"])
def comparison_export(run_id: str, principal: Principal = Depends(current_principal)):
    with tenant_session(principal.tenant_id) as db:
        run = _run_or_404(db, run_id)
        body = comparison_csv(_comparison(db, run))
    return Response(
        body,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="comparison-{run_id[:8]}.csv"'},
    )


@router.get("/runs/{run_id}/summary.pdf", tags=["quotes"])
def summary_pdf(run_id: str, principal: Principal = Depends(current_principal)):
    with tenant_session(principal.tenant_id) as db:
        run = _run_or_404(db, run_id)
        req = db.get(ProcurementRequest, run.request_id)
        intent = ledger.intent_for_run(db, run.id)
        order = (
            ser.intent_out(intent, db.scalar(select(SupplierOrder).where(SupplierOrder.intent_id == intent.id)))
            if intent
            else None
        )
        pdf = run_summary_pdf(ser.run_out(run), ser.request_out(req), _comparison(db, run), order)
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="run-{run_id[:8]}.pdf"'},
    )


# ------------------------------------------------------------------------------------------- approvals


def _approval_detail(db, ar: ApprovalRequest) -> dict[str, Any]:
    run = db.get(ProcurementRun, ar.run_id)
    req = db.get(ProcurementRequest, ar.request_id)
    quote = db.get(Quote, ar.quote_id)
    sup = db.get(Supplier, ar.supplier_id)
    dec = db.scalar(
        select(PolicyDecision)
        .where(PolicyDecision.quote_id == quote.id)
        .order_by(PolicyDecision.created_at.desc())
        .limit(1)
    )
    previous = db.get(ApprovalRequest, ar.supersedes_id) if ar.supersedes_id else None
    return ser.approval_out(ar) | {
        "request": ser.request_out(req),
        "quote": ser.quote_out(quote, sup, dec),
        "run_status": run.status,
        "simulated_model": run.mode == "fixture",
        "previous": ser.approval_out(previous) if previous else None,
        "alternatives": [
            q
            for q in _comparison(db, run)
            if q["eligible"] and q["id"] != str(quote.id) and q["supplier"]["key"] != sup.key
        ],
    }


@router.get("/approvals", tags=["approvals"])
def approval_inbox(
    status: str = "pending", limit: int = 25, offset: int = 0, principal: Principal = Depends(current_principal)
):
    limit, offset = _page(limit, offset)
    with tenant_session(principal.tenant_id) as db:
        q = select(ApprovalRequest).order_by(ApprovalRequest.created_at.desc())
        if status != "all":
            q = q.where(ApprovalRequest.status == status)
        rows = db.scalars(q.limit(limit).offset(offset)).all()
        items = []
        for a in rows:
            sup = db.get(Supplier, a.supplier_id)
            req = db.get(ProcurementRequest, a.request_id)
            items.append(
                ser.approval_out(a)
                | {
                    "supplier_name": sup.name,
                    "request_title": req.title,
                    "can_decide": principal.has("approver") and a.requester_id != principal.user_id,
                }
            )
        return {"items": items, "limit": limit, "offset": offset}


@router.get("/approvals/{approval_id}", tags=["approvals"])
def approval_detail(approval_id: str, principal: Principal = Depends(current_principal)):
    with tenant_session(principal.tenant_id) as db:
        ar = db.get(ApprovalRequest, _uuid(approval_id, "approval"))
        if ar is None:
            raise ApiError(404, "NOT_FOUND", "approval not found")
        return _approval_detail(db, ar) | {
            "can_decide": principal.has("approver") and ar.requester_id != principal.user_id and ar.status == "pending"
        }


class DecisionIn(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    reason: str = Field(min_length=3, max_length=2000)
    acknowledged_fingerprint: str = Field(
        min_length=64, max_length=64, description="Fingerprint shown to the approver; must match the request"
    )


@router.post("/approvals/{approval_id}/decision", tags=["approvals"])
def decide(
    approval_id: str, body: DecisionIn, request: Request, principal: Principal = Depends(require_role("approver"))
):
    key = idempotency.key_from(request)
    payload = body.model_dump() | {"approval_id": approval_id}
    with tenant_session(principal.tenant_id) as db:
        prior = idempotency.lookup(db, principal, "POST /api/approvals/{id}/decision", key, payload)
        if prior:
            return JSONResponse(prior["body"], status_code=prior["status"])
        ar = db.get(ApprovalRequest, _uuid(approval_id, "approval"))
        if ar is None:
            raise ApiError(404, "NOT_FOUND", "approval not found")
        if body.acknowledged_fingerprint != ar.fingerprint:
            raise ApiError(409, "CONFLICT", "The purchase changed since you reviewed it; reload the approval")
        try:
            approval = approvals.decide(
                db,
                approval_request_id=ar.id,
                approver_id=principal.user_id,
                approver_roles=principal.roles,
                decision=body.decision,
                reason=body.reason,
            )
        except approvals.ApprovalError as e:
            raise ApiError(e.status, e.code, str(e)) from e
        run = db.get(ProcurementRun, ar.run_id)
        if run.status == "awaiting_approval":
            service.enqueue_resume(db, run, f"approval-{ar.id}")
        out = {
            "approval_request_id": str(ar.id),
            "decision": approval.decision,
            "status": ar.status,
            "decided_at": ser.iso(approval.decided_at),
        }
        idempotency.store(db, principal, "POST /api/approvals/{id}/decision", key, payload, 200, out)
        return out


class AlternativeIn(BaseModel):
    quote_id: str
    reason: str = Field(min_length=3, max_length=2000)


@router.post("/approvals/{approval_id}/select-alternative", tags=["approvals"])
def select_alternative(approval_id: str, body: AlternativeIn, principal: Principal = Depends(require_role("approver"))):
    with tenant_session(principal.tenant_id) as db:
        ar = db.get(ApprovalRequest, _uuid(approval_id, "approval"))
        if ar is None or ar.status != "pending":
            raise ApiError(409, "APPROVAL_NOT_PENDING", "Approval is not pending")
        if ar.requester_id == principal.user_id:
            raise ApiError(403, "APPROVER_IS_REQUESTER", "The requester cannot approve their own purchase")
        quote = db.get(Quote, _uuid(body.quote_id, "quote"))
        if quote is None or quote.run_id != ar.run_id:
            raise ApiError(404, "NOT_FOUND", "quote not found in this run")
        dec = db.scalar(
            select(PolicyDecision)
            .where(PolicyDecision.quote_id == quote.id)
            .order_by(PolicyDecision.created_at.desc())
            .limit(1)
        )
        if dec is None or not dec.eligible:
            raise ApiError(409, "HARD_POLICY_EXCEPTION", "Only quotes that pass every hard rule can be selected")
        soft = [r for r in dec.results if not r["hard"] and not r["passed"]]
        approvals.invalidate(db, ar, [], "approver_selected_alternative")
        new = approvals.create_request(
            db,
            run_id=ar.run_id,
            req=db.get(ProcurementRequest, ar.request_id),
            quote=quote,
            supplier=db.get(Supplier, quote.supplier_id),
            policy=db.get(PolicyVersion, ar.policy_version_id),
            supersedes=ar,
            reason={"reason": "approver_selected_alternative", "note": body.reason, "soft_overrides": soft},
        )
        db.get(ProcurementRun, ar.run_id).approval_request_id = new.id
        audit(
            db,
            principal.tenant_id,
            actor_type="user",
            actor_id=principal.user_id,
            action="approval.alternative_selected",
            entity_type="approval_request",
            entity_id=new.id,
            run_id=ar.run_id,
            data={"quote_id": body.quote_id, "reason": body.reason, "soft_overrides": soft},
        )
        run = db.get(ProcurementRun, ar.run_id)
        if run.status == "awaiting_approval":
            service.enqueue_resume(db, run, f"alternative-{new.id}")
        return {"approval_request_id": str(new.id), "fingerprint": new.fingerprint, "soft_overrides": soft}


class ExceptionIn(BaseModel):
    quote_id: str
    rule: str = Field(max_length=64)
    reason: str = Field(min_length=10, max_length=2000)


@router.post(
    "/policy-exceptions",
    tags=["policies"],
    status_code=201,
    description="Admin-only, explicit exception to one hard rule for one quote. Never created by the agent.",
)
def create_exception(body: ExceptionIn, principal: Principal = Depends(require_role("admin"))):
    with tenant_session(principal.tenant_id) as db:
        quote = db.get(Quote, _uuid(body.quote_id, "quote"))
        if quote is None:
            raise ApiError(404, "NOT_FOUND", "quote not found")
        exc = PolicyException(
            tenant_id=principal.tenant_id,
            run_id=quote.run_id,
            quote_id=quote.id,
            rule=body.rule,
            reason=body.reason,
            granted_by=principal.user_id,
        )
        db.add(exc)
        db.flush()
        audit(
            db,
            principal.tenant_id,
            actor_type="user",
            actor_id=principal.user_id,
            action="policy.exception_granted",
            entity_type="quote",
            entity_id=quote.id,
            run_id=quote.run_id,
            data=body.model_dump(),
        )
        return {"id": str(exc.id)}


# ------------------------------------------------------------------------------------------- orders


@router.get("/orders", tags=["orders"])
def list_orders(limit: int = 25, offset: int = 0, principal: Principal = Depends(current_principal)):
    limit, offset = _page(limit, offset)
    with tenant_session(principal.tenant_id) as db:
        rows = db.scalars(select(OrderIntent).order_by(OrderIntent.created_at.desc()).limit(limit).offset(offset)).all()
        out = []
        for i in rows:
            so = db.scalar(select(SupplierOrder).where(SupplierOrder.intent_id == i.id))
            sup = db.get(Supplier, i.supplier_id)
            out.append(ser.intent_out(i, so) | {"supplier_name": sup.name})
        return {"items": out, "limit": limit, "offset": offset}


@router.get("/orders/{intent_id}", tags=["orders"])
def get_order(intent_id: str, principal: Principal = Depends(current_principal)):
    with tenant_session(principal.tenant_id) as db:
        i = db.get(OrderIntent, _uuid(intent_id, "order"))
        if i is None:
            raise ApiError(404, "NOT_FOUND", "order not found")
        so = db.scalar(select(SupplierOrder).where(SupplierOrder.intent_id == i.id))
        attempts = db.scalars(
            select(ledger.OrderAttempt)
            .where(ledger.OrderAttempt.intent_id == i.id)
            .order_by(ledger.OrderAttempt.attempt_no)
        ).all()
        sup = db.get(Supplier, i.supplier_id)
        history = db.scalars(select(AuditEvent).where(AuditEvent.entity_id == str(i.id)).order_by(AuditEvent.id)).all()
        return ser.intent_out(i, so) | {
            "supplier_name": sup.name,
            "attempts": [
                {
                    "attempt_no": a.attempt_no,
                    "worker_id": a.worker_id,
                    "outcome": a.outcome,
                    "detail": a.detail,
                    "evidence_ids": a.evidence_ids,
                    "started_at": ser.iso(a.started_at),
                    "finished_at": ser.iso(a.finished_at),
                }
                for a in attempts
            ],
            "history": [
                {"action": h.action, "data": h.data, "at": ser.iso(h.created_at), "actor": h.actor_type}
                for h in history
            ],
        }


@router.post(
    "/orders/{intent_id}/reconcile",
    tags=["orders"],
    description="Request a fresh order-history check. Never resubmits the order.",
)
def request_reconcile(intent_id: str, principal: Principal = Depends(current_principal)):
    if not (principal.has("approver") or principal.has("admin")):
        raise ApiError(403, "FORBIDDEN_ROLE", "Requires role: approver or admin.")
    with tenant_session(principal.tenant_id) as db:
        i = db.get(OrderIntent, _uuid(intent_id, "order"))
        if i is None:
            raise ApiError(404, "NOT_FOUND", "order not found")
        if i.status not in ledger.IN_FLIGHT:
            raise ApiError(409, "INVALID_TRANSITION", f"Order is {i.status}; nothing to reconcile")
        run = db.get(ProcurementRun, i.run_id)
        if run.status == "paused_for_human":
            service.enqueue_resume(db, run, "reconcile", {"action": "retry"})
        audit(
            db,
            principal.tenant_id,
            actor_type="user",
            actor_id=principal.user_id,
            action="order.reconcile_requested",
            entity_type="order_intent",
            entity_id=i.id,
            run_id=i.run_id,
        )
        return {"ok": True, "status": i.status}


# ------------------------------------------------------------------------------------------- evidence & audit


@router.get("/runs/{run_id}/evidence", tags=["evidence"])
def list_evidence(run_id: str, principal: Principal = Depends(current_principal)):
    with tenant_session(principal.tenant_id) as db:
        run = _run_or_404(db, run_id)
        rows = db.scalars(
            select(EvidenceArtifact).where(EvidenceArtifact.run_id == run.id).order_by(EvidenceArtifact.created_at)
        ).all()
        return {"items": [ser.evidence_out(e) for e in rows]}


@router.get("/evidence/{evidence_id}", tags=["evidence"])
def download_evidence(evidence_id: str, principal: Principal = Depends(current_principal)):
    with tenant_session(principal.tenant_id) as db:
        art = db.get(EvidenceArtifact, _uuid(evidence_id, "evidence"))  # RLS: other tenants' rows are invisible
        if art is None:
            raise ApiError(404, "NOT_FOUND", "evidence not found")
        try:
            data = store.read(art)
        except (FileNotFoundError, ValueError, PermissionError) as exc:
            raise ApiError(
                410, "EVIDENCE_UNAVAILABLE", "Evidence file is unavailable or failed integrity checks"
            ) from exc
        audit(
            db,
            principal.tenant_id,
            actor_type="user",
            actor_id=principal.user_id,
            action="evidence.downloaded",
            entity_type="evidence",
            entity_id=art.id,
            run_id=art.run_id,
        )
        ext = art.storage_path.rsplit(".", 1)[-1]
    return Response(
        data,
        media_type=art.content_type,
        headers={
            "Content-Disposition": f'inline; filename="evidence-{evidence_id[:8]}.{ext}"',
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/audit", tags=["audit"])
def audit_log(
    run_id: str | None = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    principal: Principal = Depends(current_principal),
):
    with tenant_session(principal.tenant_id) as db:
        q = select(AuditEvent).order_by(AuditEvent.id.desc())
        if run_id:
            q = q.where(AuditEvent.run_id == _uuid(run_id, "run"))
        rows = db.scalars(q.limit(min(limit, 500)).offset(max(0, offset))).all()
        return {
            "items": [
                {
                    "id": a.id,
                    "actor_type": a.actor_type,
                    "actor_id": a.actor_id,
                    "action": a.action,
                    "entity_type": a.entity_type,
                    "entity_id": a.entity_id,
                    "run_id": str(a.run_id) if a.run_id else None,
                    "data": a.data,
                    "at": ser.iso(a.created_at),
                }
                for a in rows
            ]
        }


# ------------------------------------------------------------------------------------------- evaluation & fixtures


@router.get("/evals", tags=["evaluation"])
def list_evals(principal: Principal = Depends(current_principal)):
    with tenant_session(principal.tenant_id) as db:
        rows = db.scalars(select(EvalRun).order_by(EvalRun.created_at.desc()).limit(50)).all()
        return {
            "items": [
                {
                    "id": str(e.id),
                    "label": e.label,
                    "mode": e.mode,
                    "config": e.config,
                    "metrics": e.metrics,
                    "gates": e.gates,
                    "results": e.results,
                    "created_at": ser.iso(e.created_at),
                }
                for e in rows
            ]
        }


def _control(method: str, path: str, body: dict | None = None) -> Any:
    s = get_settings()
    try:
        r = httpx.request(
            method,
            s.fixture_control_url + path,
            json=body,
            timeout=15,
            headers={"X-Control-Token": s.fixture_control_token},
        )
    except httpx.HTTPError as exc:
        raise ApiError(503, "FIXTURE_CONTROL_UNAVAILABLE", "Fixture control service is unreachable") from exc
    if r.status_code >= 400:
        raise ApiError(502, "FIXTURE_CONTROL_UNAVAILABLE", f"Fixture control returned {r.status_code}")
    return r.json()


@router.get("/admin/fixtures/scenarios", tags=["fixtures"])
def scenarios(principal: Principal = Depends(require_role("admin"))):
    return {"scenarios": _control("GET", "/_control/scenarios"), "state": _control("GET", "/_control/state")}


class ScenarioIn(BaseModel):
    scenario: str = Field(max_length=64)


@router.post(
    "/admin/fixtures/reset",
    tags=["fixtures"],
    description="Operator-only scenario control. Destructive to synthetic supplier data only.",
)
def reset_fixtures(body: ScenarioIn, principal: Principal = Depends(require_role("admin"))):
    result = _control("POST", "/_control/reset", {"scenario": body.scenario})
    with tenant_session(principal.tenant_id) as db:
        audit(
            db,
            principal.tenant_id,
            actor_type="user",
            actor_id=principal.user_id,
            action="fixtures.reset",
            entity_type="fixtures",
            entity_id=body.scenario,
        )
    return result


class MutateIn(BaseModel):
    supplier: str = Field(pattern="^(alpha|beta|gamma)$")
    products: dict[str, dict[str, Any]]


@router.post(
    "/admin/fixtures/mutate",
    tags=["fixtures"],
    description="Operator-only: change a synthetic offer, e.g. to demonstrate a post-approval price change.",
)
def mutate_fixtures(body: MutateIn, principal: Principal = Depends(require_role("admin"))):
    result = _control("POST", "/_control/mutate", body.model_dump())
    with tenant_session(principal.tenant_id) as db:
        audit(
            db,
            principal.tenant_id,
            actor_type="user",
            actor_id=principal.user_id,
            action="fixtures.mutated",
            entity_type="fixtures",
            entity_id=body.supplier,
            data=body.model_dump(),
        )
    return result
