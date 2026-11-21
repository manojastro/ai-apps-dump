from datetime import timedelta

from sqlalchemy import func, select

from app import clock
from app.data import db
from app.data.models import (
    Appointment,
    Approval,
    AuditEntry,
    Communication,
    Observation,
    SupplyOrder,
    Workflow,
)
from app.orchestrator.engine import CrashAfter, Orchestrator, SimulatedCrash
from app.orchestrator.runner import Simulation, approve_all
from app.queue import outbox


def count(model, *where):
    with db.session() as s:
        return s.scalar(select(func.count()).select_from(model).where(*where))


def snapshot():
    """Side-effect fingerprint used to compare a crashed+resumed run with a clean run."""
    with db.session() as s:
        return {
            "appointments": s.scalar(select(func.count()).select_from(Appointment)),
            "communications": s.scalar(select(func.count()).select_from(Communication)),
            "sent": s.scalar(select(func.count()).select_from(Communication).where(Communication.status == "sent_simulated")),
            "orders": s.scalar(select(func.count()).select_from(SupplyOrder)),
            "approvals": s.scalar(select(func.count()).select_from(Approval)),
            "flagged": s.scalar(select(func.count()).select_from(Observation).where(Observation.flagged.is_(True))),
            "workflows": sorted((w.id, w.type, w.status, w.data.get("outcome")) for w in s.scalars(select(Workflow))),
            "ok_mutations": s.scalar(select(func.count()).select_from(AuditEntry).where(
                AuditEntry.status == "ok", AuditEntry.tool.in_(
                    ["book_appointment", "draft_communication", "draft_supply_order", "request_approval",
                     "flag_checkin_for_review"]))),
        }


def run_with_crash(events, crash_at: int | None, approver=approve_all, expire_pending=False):
    """Run `events` to completion, killing the 'process' at the crash_at-th crash point (if given), then
    restarting with a brand-new orchestrator and resuming. Returns (snapshot, crash_point)."""
    for typ, payload in events:
        outbox.enqueue(typ, payload)
    fault = CrashAfter(crash_at) if crash_at else None
    orch = Orchestrator(fault=fault)
    sim = Simulation(orch, approver)
    point = None
    try:
        sim.run(expire_pending=expire_pending)
    except SimulatedCrash:
        point = fault.point
        clock.advance(timedelta(minutes=10))  # the claim lease expires while the process is down
        orch2 = Orchestrator()  # restart: fresh process
        orch2.resume()
        Simulation(orch2, approver).run(expire_pending=expire_pending)
    return snapshot(), point
