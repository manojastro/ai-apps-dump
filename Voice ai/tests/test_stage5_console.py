from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app import clock
from app.approval import service as approvals
from app.console.app import create_app
from app.data import db
from app.data.models import Approval, Communication, Observation, Workflow
from app.orchestrator.engine import Orchestrator
from app.orchestrator.runner import Simulation
from app.queue import outbox
from tests.helpers import count


def client_for(user: str) -> TestClient:
    c = TestClient(create_app(), follow_redirects=False)
    r = c.post("/login", data={"username": user, "password": "demo"})
    assert r.status_code == 303
    return c


def wf_of(prefix):
    with db.session() as s:
        return s.scalars(select(Workflow).where(Workflow.id.like(f"{prefix}%"))).one()


def make_pending_all_roles():
    with db.session() as s:
        hi = s.scalars(select(Observation).where(Observation.pain_score >= 7)).first()
        from app.data.models import SupplyItem
        for it in s.scalars(select(SupplyItem).limit(3)):
            it.on_hand = 0
        hi_id, hi_pid = hi.id, hi.patient_id
    outbox.enqueue("VISIT_COMPLETED", {"patient_id": "pat-0001"})
    outbox.enqueue("CHECKIN_RECEIVED", {"checkin_id": hi_id, "patient_id": hi_pid})
    outbox.enqueue("STOCK_LOW", {})
    sim = Simulation(Orchestrator(), approver=None)
    sim.pump()
    return sim


def test_login_required_and_bad_password(seeded):
    c = TestClient(create_app(), follow_redirects=False)
    assert c.get("/approvals").status_code == 303  # redirected to /login
    assert c.get("/api/approvals").status_code == 401
    r = c.post("/login", data={"username": "nurse1", "password": "wrong"})
    assert r.status_code == 200 and "Invalid credentials" in r.text


def test_staff_only_see_approvals_for_their_role(seeded):
    make_pending_all_roles()
    seen = {}
    for user, role in (("frontdesk1", "front_desk"), ("nurse1", "nurse"), ("inventory1", "inventory")):
        items = client_for(user).get("/api/approvals").json()
        assert items and all(i["required_role"] == role for i in items)
        seen[user] = {i["kind"] for i in items}
    assert seen == {"frontdesk1": {"communication"}, "nurse1": {"checkin_review"}, "inventory1": {"supply_order"}}


def test_wrong_role_cannot_decide(seeded):
    make_pending_all_roles()
    with db.session() as s:
        order_ap = s.scalars(select(Approval).where(Approval.kind == "supply_order")).one().id
    r = client_for("nurse1").post(f"/approvals/{order_ap}/decide", data={"decision": "approve"},
                                  headers={"accept": "application/json"})
    assert r.status_code == 403
    assert approvals.get(order_ap).status == "pending"


def test_reject_requires_reason_and_approve_works(seeded):
    make_pending_all_roles()
    with db.session() as s:
        comm_ap = s.scalars(select(Approval).where(Approval.kind == "communication")).one().id
    c = client_for("frontdesk1")
    r = c.post(f"/approvals/{comm_ap}/decide", data={"decision": "reject", "reason": ""},
               headers={"accept": "application/json"})
    assert r.status_code == 400 and "reason" in r.json()["error"]
    r = c.post(f"/approvals/{comm_ap}/decide", data={"decision": "approve"})
    assert r.status_code == 303
    assert approvals.get(comm_ap).status == "approved" and approvals.get(comm_ap).decided_by == "frontdesk1"
    r = c.post(f"/approvals/{comm_ap}/decide", data={"decision": "approve"}, headers={"accept": "application/json"})
    assert r.status_code == 400  # cannot decide twice


def test_rejection_reason_reaches_agent_for_exactly_one_redraft(seeded):
    outbox.enqueue("VISIT_COMPLETED", {"patient_id": "pat-0001"})
    sim = Simulation(Orchestrator(), approver=None)
    sim.pump()
    first = approvals.pending_for_role("front_desk")[0]
    approvals.decide(first.id, "frontdesk1", False, "Please make it shorter")
    sim.pump()
    pend = approvals.pending_for_role("front_desk")
    assert len(pend) == 1 and pend[0].id != first.id
    assert "Hello" in pend[0].payload["body"] and pend[0].payload["body"] != first.payload["body"]  # re-drafted
    assert wf_of("post_visit").data["rejection_reason"] == "Please make it shorter"
    approvals.decide(pend[0].id, "frontdesk1", False, "still no")
    sim.pump()
    wf = wf_of("post_visit")
    assert wf.data["outcome"] == "message_rejected"  # only ONE re-draft
    assert count(Communication) == 2


def test_expired_approval_triggers_redraft_then_escalates(seeded, monkeypatch):
    monkeypatch.setenv("EIR_APPROVAL_TTL_HOURS", "1")
    outbox.enqueue("VISIT_COMPLETED", {"patient_id": "pat-0001"})
    sim = Simulation(Orchestrator(), approver=None)
    sim.pump()
    clock.advance(timedelta(hours=2))
    sim.pump()  # tick expires the first approval, workflow re-drafts
    assert count(Approval, Approval.status == "expired") == 1
    assert count(Communication) == 2
    assert wf_of("post_visit").status == "WAITING_APPROVAL"
    clock.advance(timedelta(hours=2))
    sim.pump()  # second expiry: escalate to staff
    wf = wf_of("post_visit")
    assert wf.status == "ESCALATED" and wf.data["outcome"] == "escalated"
    assert count(Communication, Communication.status == "sent_simulated") == 0


def test_expired_approval_cannot_be_decided(seeded, monkeypatch):
    monkeypatch.setenv("EIR_APPROVAL_TTL_HOURS", "1")
    outbox.enqueue("VISIT_COMPLETED", {"patient_id": "pat-0001"})
    Simulation(Orchestrator(), approver=None).pump()
    ap = approvals.pending_for_role("front_desk")[0]
    clock.advance(timedelta(hours=2))
    with pytest.raises(approvals.ApprovalError):
        approvals.decide(ap.id, "frontdesk1", True)


def test_workflow_view_traces_step_by_step(seeded):
    make_pending_all_roles()
    wf = wf_of("post_visit")
    c = client_for("frontdesk1")
    page = c.get(f"/workflows/{wf.id}").text
    for needle in ("DRAFT_MESSAGE", "AWAIT_MSG_APPROVAL", "draft_communication", "request_approval", "followup", "pending"):
        assert needle in page
    assert c.get("/workflows").status_code == 200 and c.get("/workflows/nope").status_code == 404


def test_audit_search_filters(seeded):
    make_pending_all_roles()
    c = client_for("frontdesk1")
    page = c.get("/audit?tool=draft_communication").text
    assert "draft_communication" in page and "flag_checkin_for_review" not in page
    assert "pat-0001" in c.get("/audit?patient_id=pat-0001").text
    assert c.get("/audit?date_from=garbage").status_code == 400
    assert c.get("/audit?actor=recovery").status_code == 200


def test_review_tasks_nurse_only_and_xss_safe(seeded):
    with db.session() as s:
        o = s.scalars(select(Observation).where(Observation.pain_score >= 7)).first()
        o.free_text = "<script>alert('x')</script>"
        oid, pid = o.id, o.patient_id
    outbox.enqueue("CHECKIN_RECEIVED", {"checkin_id": oid, "patient_id": pid})
    Simulation(Orchestrator(), approver=None).pump()
    assert client_for("frontdesk1").get("/reviews").status_code == 403
    page = client_for("nurse1").get("/reviews").text
    assert "<script>alert" not in page and "&lt;script&gt;" in page
