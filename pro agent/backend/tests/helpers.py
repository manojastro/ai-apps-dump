"""Shared helpers for integration tests that drive the real worker against live mock portals."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
from sqlalchemy import select

from procnav.agents import service
from procnav.approvals import service as approvals
from procnav.core.db import global_session, tenant_session
from procnav.core.models import ApprovalRequest, ProcurementRun, Tenant, User
from procnav.workers import jobs
from procnav.workers.runner import execute

CONTROL = "http://127.0.0.1:8309"
CTRL_H = {"X-Control-Token": "dev-control-token"}
WORKER = "test-worker"


def control(path: str, body: dict | None = None, method: str = "POST"):
    r = httpx.request(method, CONTROL + path, json=body, headers=CTRL_H, timeout=30)
    r.raise_for_status()
    return r.json()


def reset_scenario(name: str) -> None:
    control("/_control/reset", {"scenario": name})


def portal_orders(supplier: str | None = None) -> list[dict]:
    return control("/_control/orders" + (f"?supplier={supplier}" if supplier else ""), method="GET")["orders"]


def ids(tenant: str = "acme"):
    with global_session() as s:
        t = s.scalar(select(Tenant).where(Tenant.slug == tenant))
        users = {
            u.email.split("@")[0]: u.id for u in s.scalars(select(User).where(User.email.like(f"%@{tenant}.test")))
        }
    return t.id, users


def create_request_and_run(
    tenant: str = "acme",
    fixture_options: dict | None = None,
    workflow: str = "bounded",
    budget: str = "500000.00",
    quantity: int = 10,
):
    tid, users = ids(tenant)
    with tenant_session(tid) as db:
        req = service.create_request(
            db,
            tid,
            users["requester"],
            service.RequestIn(
                title="Ten business laptops",
                canonical_product_id="NW-PRO14-16-512",
                min_ram_gb=16,
                min_ssd_gb=512,
                quantity=quantity,
                budget_total=Decimal(budget),
                address_ref="ADDR-BLR-01",
                delivery_deadline=(datetime.now(UTC) + timedelta(days=7)).date(),
            ),
            idempotency_key=None,
        )
        run = service.start_run(
            db,
            tid,
            users["requester"],
            req.id,
            idempotency_key=None,
            workflow=workflow,
            mode="fixture",
            fixture_options=fixture_options,
        )
        return tid, users, req.id, run.id


def drive(run_id: uuid.UUID, max_jobs: int = 10) -> None:
    """Run queued jobs for this run in-process until none remain."""
    for _ in range(max_jobs):
        claimed = [j for j in jobs.claim(WORKER, 120, limit=5)]
        mine = [j for j in claimed if j.run_id == run_id]
        for j in claimed:
            if j.run_id != run_id:
                jobs.release(j.id, WORKER, 0)
        if not mine:
            return
        for j in mine:
            execute(j, WORKER)


def run_row(tid, run_id) -> ProcurementRun:
    with tenant_session(tid) as db:
        return db.get(ProcurementRun, run_id)


def approve(tid, users, run_id, approver: str = "approver", decision: str = "approved"):
    with tenant_session(tid) as db:
        run = db.get(ProcurementRun, run_id)
        ar = db.get(ApprovalRequest, run.approval_request_id)
        approvals.decide(
            db,
            approval_request_id=ar.id,
            approver_id=users[approver],
            approver_roles=frozenset({"approver"}),
            decision=decision,
            reason="test decision",
        )
        service.enqueue_resume(db, run, "approval")
        return ar.id
