"""Milestones 3-4 gates: real browser flows through the durable worker against live mock portals.

Requires: dev PostgreSQL, migrated+seeded app DB, and `python -m mockportals.main` running.
Each test resets the fixture scenario through the private control API (never via agent tools).
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import select

from procnav.agents import graph as graph_module
from procnav.approvals import service as approvals
from procnav.core.db import tenant_session
from procnav.core.models import (
    ApprovalRequest,
    BrowserStep,
    OrderIntent,
    PolicyDecision,
    Quote,
    RunEvent,
    SupplierOrder,
)
from procnav.workers import jobs
from procnav.workers.runner import execute

from .helpers import (
    WORKER,
    approve,
    control,
    create_request_and_run,
    drive,
    portal_orders,
    reset_scenario,
    run_row,
)

pytestmark = pytest.mark.browser


@pytest.fixture(scope="module", autouse=True)
def portals_up():
    try:
        httpx.get("http://127.0.0.1:8309/healthz", timeout=3).raise_for_status()
    except Exception:  # noqa: BLE001
        pytest.skip("mock portals not running (python -m mockportals.main)")


def events(tid, run_id, type_=None):
    with tenant_session(tid) as db:
        q = select(RunEvent).where(RunEvent.run_id == run_id).order_by(RunEvent.id)
        rows = [(e.type, e.data) for e in db.scalars(q)]
    return [d for t, d in rows if t == type_] if type_ else rows


def quote_by_sku(tid, run_id, sku):
    with tenant_session(tid) as db:
        q = db.scalars(select(Quote).where(Quote.run_id == run_id, Quote.sku == sku).order_by(Quote.created_at)).first()
        dec = db.scalars(select(PolicyDecision).where(PolicyDecision.quote_id == q.id)).first() if q else None
        return q, dec


def failed_rules(dec):
    return {r["rule"] for r in dec.results if r["hard"] and not r["passed"]}


def run_to_completion(scenario, *, fixture_options=None, before_approval=None, approvals_expected=1):
    reset_scenario(scenario)
    tid, users, req_id, run_id = create_request_and_run(fixture_options=fixture_options)
    drive(run_id)
    for _ in range(approvals_expected + 2):
        r = run_row(tid, run_id)
        if r.status != "awaiting_approval":
            break
        if before_approval:
            before_approval()
            before_approval = None
        approve(tid, users, run_id)
        drive(run_id)
    return tid, users, run_id


def test_happy_path_exactly_one_order_with_verified_receipt():
    tid, _, run_id = run_to_completion("happy_path")
    r = run_row(tid, run_id)
    assert (r.status, r.outcome) == ("completed", "purchased")
    orders = portal_orders()
    assert len(orders) == 1 and orders[0]["sku"] == "B-77821" and orders[0]["total"] == "474000.00"
    with tenant_session(tid) as db:
        intent = db.scalar(select(OrderIntent).where(OrderIntent.run_id == run_id))
        so = db.scalar(select(SupplierOrder).where(SupplierOrder.intent_id == intent.id))
        assert intent.status == "reconciled" and so.verified and so.supplier_order_ref == orders[0]["order_ref"]
        assert orders[0]["po_reference"] == intent.intent_key
    _, dec = quote_by_sku(tid, run_id, "G-PRO14-16")
    assert failed_rules(dec) == {"budget.landed_total"}  # tax and freight push it over budget
    assert r.action_count <= 80 and r.waiting_ms >= 0


def test_planted_bad_recommendation_rejected_by_verifier():
    tid, _, run_id = run_to_completion(
        "incompatible_spec", fixture_options={"planted_bad_recommendation": "A-NW14-8-512"}
    )
    rejected = events(tid, run_id, "verifier_rejected_recommendation")
    assert rejected and {f["rule"] for f in rejected[0]["failed_rules"]} == {"spec.ram_gb"}
    rule = next(f for f in rejected[0]["failed_rules"] if f["rule"] == "spec.ram_gb")
    assert rule["observed"] == "8 GB" and rule["expected"] == ">= 16 GB"
    assert run_row(tid, run_id).outcome == "purchased"
    assert [o["sku"] for o in portal_orders()] == ["B-77821"]


def test_insufficient_stock_moves_to_alpha():
    tid, _, run_id = run_to_completion("insufficient_stock")
    _, dec = quote_by_sku(tid, run_id, "B-77821")
    assert "stock.available" in failed_rules(dec)
    assert [(o["supplier"], o["total"]) for o in portal_orders()] == [("alpha", "491200.00")]


def test_tax_driven_budget_breach_yields_no_purchase():
    tid, _, run_id = run_to_completion("tax_budget_breach")
    r = run_row(tid, run_id)
    assert r.outcome == "no_eligible_offer" and portal_orders() == []
    q, dec = quote_by_sku(tid, run_id, "G-PRO14-16")
    assert q.unit_price * q.quantity < Decimal("500000") and failed_rules(dec) == {"budget.landed_total"}
    statuses = r.summary["suppliers"]
    assert statuses["alpha"]["status"] == "unavailable" and statuses["beta"]["status"] == "unavailable"


def test_ambiguous_pack_rejected():
    tid, _, run_id = run_to_completion("ambiguous_pack")
    _, dec = quote_by_sku(tid, run_id, "A-NW14-16-512-P5")
    assert "unit.pack_size" in failed_rules(dec)
    assert run_row(tid, run_id).outcome == "no_eligible_offer" and portal_orders() == []


def test_changed_layout_recovers_with_semantic_locators():
    tid, _, run_id = run_to_completion("changed_layout")
    assert [(o["supplier"], o["sku"]) for o in portal_orders()] == [("alpha", "A-NW14-16-512")]
    q, _ = quote_by_sku(tid, run_id, "A-NW14-16-512")
    assert q.normalized_spec["ram_gb"] == 16 and q.total == Decimal("491200.00")


def test_session_expiry_relogin():
    tid, _, run_id = run_to_completion("session_expiry")
    kinds = [e["kind"] for e in events(tid, run_id, "recovery")]
    assert "session_expired_relogin" in kinds
    assert run_row(tid, run_id).outcome == "purchased" and len(portal_orders()) == 1


def test_unavailable_supplier_partial_comparison():
    tid, _, run_id = run_to_completion("unavailable_supplier")
    r = run_row(tid, run_id)
    assert r.summary["suppliers"]["gamma"]["status"] == "unavailable"
    assert r.outcome == "purchased" and portal_orders()[0]["supplier"] == "beta"


def test_malicious_page_cannot_redirect_or_change_policy():
    tid, _, run_id = run_to_completion("malicious_instructions", fixture_options={"follow_injected_links": True})
    with tenant_session(tid) as db:
        blocked = db.scalars(
            select(BrowserStep).where(BrowserStep.run_id == run_id, BrowserStep.status == "blocked")
        ).all()
    assert blocked and all(b.error_code == "BLOCKED_NAVIGATION" for b in blocked)
    assert run_row(tid, run_id).outcome == "purchased"
    orders = portal_orders()
    assert len(orders) == 1 and orders[0]["qty"] == 10 and orders[0]["total"] == "474000.00"
    requests = control("/_control/requests", method="GET")["requests"]
    assert not any("claim-offer" in r["path"] for r in requests)


def test_price_change_after_approval_requires_fresh_approval():
    tid, _, run_id = run_to_completion("price_change_after_approval", approvals_expected=2)
    inval = events(tid, run_id, "approval_invalidated")
    assert inval and any(
        c["field"] == "total" and c["approved"] == "474000.00" and c["current"] == "491000.00"
        for c in inval[0]["changes"]
    )
    with tenant_session(tid) as db:
        ars = db.scalars(
            select(ApprovalRequest).where(ApprovalRequest.run_id == run_id).order_by(ApprovalRequest.created_at)
        ).all()
    assert [a.status for a in ars] == ["invalidated", "consumed"]
    orders = portal_orders()
    assert len(orders) == 1 and orders[0]["total"] == "491000.00"


def test_price_change_before_approval_detected_on_revalidation():
    mutate = lambda: control(
        "/_control/mutate",
        {
            "supplier": "beta",  # noqa: E731
            "products": {"B-77821": {"unit_price": "48900.00"}},
        },
    )
    tid, _, run_id = run_to_completion("price_change_before_approval", before_approval=mutate, approvals_expected=2)
    assert events(tid, run_id, "approval_invalidated")
    assert [o["total"] for o in portal_orders()] == ["491000.00"]


def test_timeout_after_commit_reconciles_without_second_order():
    tid, _, run_id = run_to_completion("timeout_success")
    assert events(tid, run_id, "reconciled")
    orders = portal_orders()
    assert len(orders) == 1
    with tenant_session(tid) as db:
        intent = db.scalar(select(OrderIntent).where(OrderIntent.run_id == run_id))
        so = db.scalar(select(SupplierOrder).where(SupplierOrder.intent_id == intent.id))
    assert intent.status == "reconciled" and so.reconciled_via == "order_history" and so.verified


def test_duplicate_worker_delivery_creates_one_order():
    reset_scenario("happy_path")
    tid, users, _, run_id = create_request_and_run()
    drive(run_id)
    approve(tid, users, run_id)
    with tenant_session(tid) as db:  # a second delivery of the same resume
        from procnav.agents import service

        service.enqueue_resume(db, run_row(tid, run_id), "duplicate")
    claimed = jobs.claim(WORKER, 300, limit=5)
    threads = [threading.Thread(target=execute, args=(j, f"{WORKER}-{i}")) for i, j in enumerate(claimed)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    drive(run_id)
    assert run_row(tid, run_id).outcome == "purchased"
    assert len(portal_orders()) == 1


def test_mfa_pauses_safely_for_a_human():
    tid, _, run_id = run_to_completion("mfa_challenge")
    r = run_row(tid, run_id)
    assert r.status == "paused_for_human" and r.handoff["reason"] == "authentication_required"
    assert portal_orders() == []


def test_worker_restart_resumes_from_checkpoint(monkeypatch):
    reset_scenario("happy_path")
    tid, users, _, run_id = create_request_and_run()
    original = graph_module.normalize
    calls = {"n": 0}

    def crash_once(state):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("simulated worker crash")
        return original(state)

    monkeypatch.setattr(graph_module, "normalize", crash_once)
    claimed = [j for j in jobs.claim(WORKER, 120, limit=5) if j.run_id == run_id]
    assert execute(claimed[0], WORKER) == "failed"
    with tenant_session(tid) as db:
        from procnav.core.models import Job

        job = db.scalar(select(Job).where(Job.run_id == run_id))
        job.available_at = datetime.now(UTC) - timedelta(seconds=1)
    drive(run_id)
    assert events(tid, run_id, "resumed_from_checkpoint")
    approve(tid, users, run_id)
    drive(run_id)
    assert run_row(tid, run_id).outcome == "purchased" and len(portal_orders()) == 1


def test_requester_cannot_approve_and_expired_approval_rejected():
    reset_scenario("happy_path")
    tid, users, _, run_id = create_request_and_run()
    drive(run_id)
    with tenant_session(tid) as db:
        ar = db.get(ApprovalRequest, run_row(tid, run_id).approval_request_id)
        with pytest.raises(approvals.ApprovalError) as e1:
            approvals.decide(
                db,
                approval_request_id=ar.id,
                approver_id=users["requester"],
                approver_roles=frozenset({"approver", "requester"}),
                decision="approved",
                reason="self",
            )
        assert e1.value.code == "APPROVER_IS_REQUESTER"
        with pytest.raises(approvals.ApprovalError) as e2:
            approvals.decide(
                db,
                approval_request_id=ar.id,
                approver_id=users["viewer"],
                approver_roles=frozenset({"viewer"}),
                decision="approved",
                reason="no role",
            )
        assert e2.value.code == "FORBIDDEN_ROLE"
    with tenant_session(tid) as db:
        ar = db.get(ApprovalRequest, run_row(tid, run_id).approval_request_id)
        ar.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    with tenant_session(tid) as db, pytest.raises(approvals.ApprovalError) as e3:
        approvals.decide(
            db,
            approval_request_id=ar.id,
            approver_id=users["approver"],
            approver_roles=frozenset({"approver"}),
            decision="approved",
            reason="late",
        )
    assert e3.value.code == "APPROVAL_EXPIRED"
    assert portal_orders() == []


def test_transient_failure_and_delayed_confirmation_recover():
    tid, _, run_id = run_to_completion("transient_failure")
    assert any(e["kind"].startswith("http_502") for e in events(tid, run_id, "recovery"))
    assert run_row(tid, run_id).outcome == "purchased"
    tid, _, run_id = run_to_completion("delayed_confirmation")
    assert run_row(tid, run_id).outcome == "purchased"
    assert any(e["kind"] == "receipt_pending_wait" for e in events(tid, run_id, "recovery"))


def test_discount_dropped_at_checkout_uses_checkout_total():
    tid, _, run_id = run_to_completion("discount_change")
    q, _ = quote_by_sku(tid, run_id, "G-PRO14-16")
    assert q.total == Decimal("481400.00")
    assert any("not applied at checkout" in i for i in q.issues)
