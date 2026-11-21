from datetime import timedelta

import pytest
from sqlalchemy import select

from app import clock
from app.data import db
from app.data.models import Appointment, Approval, Communication, Observation, SupplyOrder, Workflow
from app.orchestrator.engine import Orchestrator
from app.orchestrator.runner import Simulation, approve_all
from app.queue import outbox
from app.tools.checkins import threshold_reasons
from tests.conftest import T0
from tests.helpers import count, run_with_crash, snapshot


def wf_of(prefix):
    with db.session() as s:
        return s.scalars(select(Workflow).where(Workflow.id.like(f"{prefix}%"))).one()


def high_checkin():
    with db.session() as s:
        return s.scalars(select(Observation).where(Observation.pain_score >= 7)).first()


def low_checkin():
    with db.session() as s:
        return s.scalars(select(Observation).where((Observation.pain_score < 7) & (Observation.temperature < 38.0))).first()


def lowstock_event():
    return [("STOCK_LOW", {"sku": "SKU-001"})]


def make_low_stock():
    from app.data.models import SupplyItem
    with db.session() as s:
        for it in s.scalars(select(SupplyItem).limit(3)):
            it.on_hand = 0


def test_post_visit_end_to_end_with_simulated_clock(seeded):
    outbox.enqueue("VISIT_COMPLETED", {"patient_id": "pat-0001", "appointment_id": "appt-0001"})
    sim = Simulation(Orchestrator())
    sim.run()
    wf = wf_of("post_visit")
    assert (wf.status, wf.data["outcome"]) == ("COMPLETED", "followup_booked")
    assert count(Communication, Communication.status == "sent_simulated") == 1
    with db.session() as s:
        appt = s.get(Appointment, wf.data["appointment_id"])
        assert appt.patient_id == "pat-0001" and appt.reason == "Follow-up visit"
    steps = [h["to"] for h in wf.history]
    for expected in ("DRAFT_MESSAGE", "AWAIT_MSG_APPROVAL", "SEND", "AWAIT_TIMER", "PROPOSE_SLOT",
                     "AWAIT_BOOKING_APPROVAL", "BOOK"):
        assert expected in steps
    assert clock.now() >= T0 + timedelta(days=3)  # the clock really jumped 3 days
    assert [d.kind for d in sim.decisions] == ["communication", "followup_booking"]


def test_post_visit_waits_for_timer_before_proposing(seeded):
    outbox.enqueue("VISIT_COMPLETED", {"patient_id": "pat-0001"})
    sim = Simulation(Orchestrator())
    sim.pump()
    sim.decide_pending()
    sim.pump()
    wf = wf_of("post_visit")
    assert wf.status == "WAITING_TIMER"
    clock.advance(timedelta(days=2))
    sim.pump()
    assert wf_of("post_visit").status == "WAITING_TIMER"  # only 2 days: still waiting
    clock.advance(timedelta(days=1, minutes=1))
    sim.pump()
    assert wf_of("post_visit").status == "WAITING_APPROVAL"  # proposal made, booking awaits staff


def test_recovery_watch_flagged_and_unflagged(seeded):
    hi, lo = high_checkin(), low_checkin()
    outbox.enqueue("CHECKIN_RECEIVED", {"checkin_id": hi.id, "patient_id": hi.patient_id})
    outbox.enqueue("CHECKIN_RECEIVED", {"checkin_id": lo.id, "patient_id": lo.patient_id})
    Simulation(Orchestrator()).run()
    with db.session() as s:
        wfs = {w.data["checkin_id"]: w for w in s.scalars(select(Workflow))}
    assert wfs[lo.id].data["outcome"] == "recorded_no_flag"
    assert wfs[hi.id].data["outcome"] == "reviewed"
    assert count(Approval, Approval.kind == "checkin_review") == 1
    assert threshold_reasons(hi.pain_score, hi.temperature)


def test_restock_end_to_end(seeded):
    make_low_stock()
    outbox.enqueue("STOCK_LOW", {})
    Simulation(Orchestrator()).run()
    wf = wf_of("restock")
    assert (wf.status, wf.data["outcome"]) == ("COMPLETED", "order_approved")
    assert count(SupplyOrder, SupplyOrder.status == "approved") == 1


def test_booking_outside_rules_needs_approval(seeded):
    # give the patient 3 future bookings, so the next one is outside the rules
    from app.tools import call_tool
    slots = call_tool("scheduler", "find_slots", {"limit": 5}).data["items"]
    for i in range(3):
        r = call_tool("scheduler", "book_appointment", {"patient_id": "pat-0005", "slot_id": slots[i]["slot_id"],
                                                        "idempotency_key": f"pre{i}"})
        assert r.data["status"] in ("booked", "requires_approval")
    outbox.enqueue("BOOKING_REQUESTED", {"patient_id": "pat-0005", "reason": "Consultation"})
    sim = Simulation(Orchestrator(), approver=None)
    sim.pump()
    wf = wf_of("booking")
    assert wf.status == "WAITING_APPROVAL"  # pat-0005 already holds 3 future bookings
    n_before = count(Appointment, Appointment.patient_id == "pat-0005")
    sim.approver = approve_all
    sim.run()
    wf = wf_of("booking")
    assert (wf.status, wf.data["outcome"]) == ("COMPLETED", "booked_after_approval")
    assert count(Appointment, Appointment.patient_id == "pat-0005") == n_before + 1


def test_rejection_triggers_exactly_one_redraft(seeded):
    outbox.enqueue("VISIT_COMPLETED", {"patient_id": "pat-0001"})

    def reject_first_message(ap):
        if ap.kind == "communication":
            return ("reject", "Too long, please shorten") if ap.payload["body"].startswith("Hello") and "thank you for visiting us" in ap.payload["body"] else ("approve", None)
        return ("approve", None)

    Simulation(Orchestrator(), reject_first_message).run()
    wf = wf_of("post_visit")
    assert count(Communication) == 2
    with db.session() as s:
        statuses = sorted(c.status for c in s.scalars(select(Communication)))
    assert statuses == ["rejected", "sent_simulated"]
    assert wf.data["outcome"] == "followup_booked"


def test_two_rejections_stop_the_workflow(seeded):
    outbox.enqueue("VISIT_COMPLETED", {"patient_id": "pat-0001"})
    Simulation(Orchestrator(), lambda ap: ("reject", "no")).run()
    wf = wf_of("post_visit")
    assert wf.data["outcome"] == "message_rejected" and count(Communication, Communication.status == "sent_simulated") == 0


def test_cannot_send_without_approval(seeded):
    """Even if a workflow reached SEND by mistake, an unapproved message is never marked sent."""
    outbox.enqueue("VISIT_COMPLETED", {"patient_id": "pat-0001"})
    sim = Simulation(Orchestrator(), approver=None)
    sim.pump()
    assert count(Communication, Communication.status == "sent_simulated") == 0
    from app.orchestrator.workflows import pv_send
    st = Orchestrator().load(wf_of("post_visit").id)
    assert pv_send(Orchestrator(), st).kind == "fail"


# ------------------------------------------------------------------ crash + resume (the core durability claim)
SCENARIOS = {
    "post_visit": lambda: [("VISIT_COMPLETED", {"patient_id": "pat-0001", "appointment_id": "appt-0001"})],
    "recovery": lambda: [("CHECKIN_RECEIVED", {"checkin_id": high_checkin().id, "patient_id": high_checkin().patient_id})],
    "restock": lambda: (make_low_stock(), [("STOCK_LOW", {})])[1],
    "booking": lambda: [("BOOKING_REQUESTED", {"patient_id": "pat-0007", "reason": "Consultation"})],
}


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_crash_at_every_point_resumes_without_duplicates(tmp_path, name):
    """Kill the process at each crash point in turn; after restart+resume the end state must equal a clean run."""
    from app.data import db as dbm
    from app.data.seed import SeedConfig, seed
    from tests.conftest import SMALL

    def fresh(tag):
        clock.freeze(T0)
        dbm.init_db(f"sqlite:///{tmp_path / (name + tag + '.db')}")
        seed(SeedConfig(**SMALL, start=T0.date() + timedelta(days=7)))

    fresh("clean")
    clean, _ = run_with_crash(SCENARIOS[name](), None)
    assert clean["workflows"], "scenario produced no workflow"
    crash_points = set()
    n = 1
    while True:
        fresh(f"c{n}")
        snap, point = run_with_crash(SCENARIOS[name](), n)
        if point is None:  # ran to completion without reaching the n-th crash point
            break
        crash_points.add(point)
        assert snap == clean, f"crash #{n} at {point}: state diverged\n{snap}\nvs\n{clean}"
        n += 1
    clock.reset()
    assert n > 2, "expected several crash points per workflow"
    print(f"{name}: {n - 1} crash points verified: {sorted(crash_points)}")


def test_two_workers_same_timer_event_no_double_booking(seeded):
    outbox.enqueue("VISIT_COMPLETED", {"patient_id": "pat-0001"})
    sim = Simulation(Orchestrator())
    sim.pump()
    sim.decide_pending()
    sim.pump()
    wf_id = wf_of("post_visit").id
    # deliver the same timer wake-up twice, concurrently-ish, through two orchestrators
    before = count(Appointment, Appointment.patient_id == "pat-0001")
    clock.advance(timedelta(days=3, minutes=1))
    outbox.enqueue("TIMER_DUE", {"workflow_id": wf_id}, dedupe_key="dup-a")
    outbox.enqueue("TIMER_DUE", {"workflow_id": wf_id}, dedupe_key="dup-b")
    sim.run()
    assert count(Appointment, Appointment.patient_id == "pat-0001") == before + 1
    assert wf_of("post_visit").data["outcome"] == "followup_booked"


def test_resume_reloads_unfinished_workflows(seeded):
    outbox.enqueue("VISIT_COMPLETED", {"patient_id": "pat-0001"})
    Simulation(Orchestrator(), approver=None).pump()
    # brand-new process: state is in the DB, nothing in memory
    o2 = Orchestrator()
    st = o2.load(wf_of("post_visit").id)
    assert st.status == "WAITING_APPROVAL" and st.step == "AWAIT_MSG_APPROVAL"
    assert snapshot()["communications"] == 1


def test_workflow_history_is_recorded(seeded):
    outbox.enqueue("STOCK_LOW", {})
    make_low_stock()
    Simulation(Orchestrator()).run()
    h = wf_of("restock").history
    assert h[0]["note"] == "created" and h[-1]["status"] == "COMPLETED" and all("ts" in x for x in h)
