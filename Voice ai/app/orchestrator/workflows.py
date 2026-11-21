"""Workflow definitions: one deterministic state machine per type.

Each handler is idempotent and returns what to do next. Agents do the thinking inside a step; code decides
the transitions. Approvals and timers are the only places a workflow waits.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Callable

from app import clock
from app.agents.fleet import FollowUpAgent, RecoveryMonitorAgent, SchedulerAgent, SupplyAgent
from app.data.db import session
from app.data.models import Approval, Communication, Observation
from app.orchestrator.engine import (
    Orchestrator,
    StepResult,
    WorkflowState,
    complete,
    escalate,
    fail,
    goto,
    wait_approval,
    wait_timer,
)
from app.queue import outbox
from app.tools import call_tool

FOLLOWUP_DELAY = timedelta(days=3)
MAX_REDRAFTS = 1


@dataclass
class WorkflowDef:
    initial: str
    steps: dict[str, Callable[[Orchestrator, WorkflowState], StepResult]]


def _approval(approval_id: str | None) -> Approval | None:
    if not approval_id:
        return None
    with session() as s:
        return s.get(Approval, approval_id)


def _decision(wf: WorkflowState, key: str = "approval_id") -> tuple[str, Approval | None]:
    ap = _approval(wf.data.get(key))
    return (ap.status if ap else "missing"), ap


def _redraft_or_stop(wf: WorkflowState, ap: Approval, redraft_step: str, rejected_outcome: str) -> StepResult:
    """Rejection/expiry: allow one re-draft (reason passed to the agent), then stop or escalate."""
    if wf.data.get("redrafts", 0) < MAX_REDRAFTS:
        wf.data["redrafts"] = wf.data.get("redrafts", 0) + 1
        wf.data["rejection_reason"] = ap.decision_reason or ap.status
        return goto(redraft_step, f"{ap.status}: re-draft #{wf.data['redrafts']}")
    if ap.status == "expired":
        return escalate("approval expired twice; needs staff attention")
    return complete(rejected_outcome, "rejected after re-draft")


def _attempt_key(wf: WorkflowState, tag: str) -> str:
    return f"{wf.id}:{tag}{wf.data.get('redrafts', 0)}"


# =========================================================================== shared booking steps
def _book_after_approval(orch: Orchestrator, wf: WorkflowState, outcome: str) -> StepResult:
    if wf.data.get("action") == "reschedule":
        r = call_tool("orchestrator", "reschedule_appointment",
                      {"appointment_id": wf.data["appointment_id"], "new_slot_id": wf.data["slot_id"],
                       "approval_id": wf.data["approval_id"], "idempotency_key": f"{wf.id}:book"},
                      workflow_id=wf.id, patient_scope=wf.data["patient_id"])
    else:
        r = call_tool("orchestrator", "book_appointment",
                      {"patient_id": wf.data["patient_id"], "slot_id": wf.data["slot_id"],
                       "reason": wf.data.get("reason") or "Follow-up", "approval_id": wf.data["approval_id"],
                       "idempotency_key": f"{wf.id}:book"},
                      workflow_id=wf.id, patient_scope=wf.data["patient_id"])
    if r.status == "ok" and r.data["status"] == "booked":
        wf.data["appointment_id"] = r.data["appointment_id"]
        return complete(outcome)
    return escalate(f"booking after approval failed: {r.error or r.data}")


def _scheduler_step(orch: Orchestrator, wf: WorkflowState, action: str, next_wait: str) -> StepResult:
    task = {"action": action, "patient_id": wf.data["patient_id"], "reason": wf.data.get("reason", "")}
    if wf.data.get("appointment_id") and action == "reschedule":
        task["appointment_id"] = wf.data["appointment_id"]
    untrusted = {"booking_notes": wf.data["notes"]} if wf.data.get("notes") else None
    run = SchedulerAgent(orch.llm).run(task, untrusted=untrusted, workflow_id=wf.id,
                                       task_key=_attempt_key(wf, "sched"), patient_scope=wf.data["patient_id"])
    if run.status != "DONE":
        return fail(f"scheduler agent {run.status}: {run.error}")
    r = run.result
    wf.data["agent_outcome"] = r["outcome"]
    if r["outcome"] in ("booked", "rescheduled"):
        wf.data["appointment_id"] = r["appointment_id"]
        return complete("rescheduled" if r["outcome"] == "rescheduled" else "booked")
    if r["outcome"] == "approval_requested":
        wf.data.update(approval_id=r["approval_id"], slot_id=r["slot_id"])
        return wait_approval(next_wait, "waiting for staff approval")
    if r["outcome"] == "no_slots":
        return complete("no_slots_available")
    return fail(f"scheduler could not complete: {r.get('note')}")


# =========================================================================== BOOKING
def booking_schedule(orch, wf):
    return _scheduler_step(orch, wf, wf.data.get("action", "book"), "AWAIT_BOOKING_APPROVAL")


def booking_await_approval(orch, wf):
    status, ap = _decision(wf)
    if status == "pending":
        return wait_approval("AWAIT_BOOKING_APPROVAL")
    if status == "approved":
        return goto("BOOK")
    return complete("booking_declined" if status == "rejected" else "booking_approval_expired")


def booking_book(orch, wf):
    return _book_after_approval(orch, wf, "rescheduled_after_approval" if wf.data.get("action") == "reschedule"
                                else "booked_after_approval")


# =========================================================================== POST_VISIT
def pv_draft(orch, wf):
    task = {"patient_id": wf.data["patient_id"], "visit_summary": wf.data.get("visit_summary", "Visit completed"),
            "rejection_reason": wf.data.get("rejection_reason")}
    untrusted = {"patient_note": wf.data["patient_note"]} if wf.data.get("patient_note") else None
    run = FollowUpAgent(orch.llm).run(task, untrusted=untrusted, workflow_id=wf.id,
                                      task_key=_attempt_key(wf, "draft"), patient_scope=wf.data["patient_id"])
    if run.status != "DONE" or run.result["approval_id"] == "none":
        return fail(f"follow-up agent {run.status}: {run.error or 'draft rejected by tool guard'}")
    wf.data.update(communication_id=run.result["communication_id"], approval_id=run.result["approval_id"])
    return wait_approval("AWAIT_MSG_APPROVAL", "message draft awaiting approval")


def pv_await_msg(orch, wf):
    status, ap = _decision(wf)
    if status == "pending":
        return wait_approval("AWAIT_MSG_APPROVAL")
    if status == "approved":
        return goto("SEND")
    return _redraft_or_stop(wf, ap, "DRAFT_MESSAGE", "message_rejected")


def pv_send(orch, wf):
    """Simulated send. Idempotent: a second run (after a crash) finds it already sent and does nothing."""
    with session() as s:
        c = s.get(Communication, wf.data["communication_id"])
        if c is None or c.status not in ("approved", "sent_simulated"):
            return fail("refusing to send: communication is not approved")
        if c.status == "approved":
            c.status, c.sent_at = "sent_simulated", clock.now()
    outbox.enqueue("TIMER_DUE", {"workflow_id": wf.id, "purpose": "followup_slot"},
                   available_at=clock.now() + FOLLOWUP_DELAY, dedupe_key=f"{wf.id}:followup_timer")
    return wait_timer("AWAIT_TIMER", "message sent (simulated); follow-up timer set for +3 days")


def pv_await_timer(orch, wf):
    if wf.data.get("timer_fired"):
        return goto("PROPOSE_SLOT")
    return wait_timer("AWAIT_TIMER")


def pv_propose(orch, wf):
    wf.data["reason"] = "Follow-up visit"
    wf.data.pop("redrafts", None)  # fresh attempt counter for the booking phase
    return _scheduler_step(orch, wf, "followup_proposal", "AWAIT_BOOKING_APPROVAL")


def pv_await_booking(orch, wf):
    status, ap = _decision(wf)
    if status == "pending":
        return wait_approval("AWAIT_BOOKING_APPROVAL")
    if status == "approved":
        return goto("BOOK")
    return complete("followup_declined" if status == "rejected" else "followup_approval_expired")


def pv_book(orch, wf):
    return _book_after_approval(orch, wf, "followup_booked")


# =========================================================================== RECOVERY_WATCH
def rw_evaluate(orch, wf):
    pid = wf.data["patient_id"]
    res, run = RecoveryMonitorAgent(orch.llm).evaluate(wf.data["checkin_id"], workflow_id=wf.id,
                                                       task_key=f"{wf.id}:eval", patient_scope=pid)
    if run is not None and run.status == "FAILED":
        return fail(run.error or "check-in could not be read")
    wf.data["summary_source"] = res.summary_source
    if not res.flagged:
        return complete("recorded_no_flag", "below thresholds; recorded and closed")
    if not res.approval_id:
        return fail("flagged but could not create review task")
    wf.data.update(approval_id=res.approval_id, reasons=res.reasons)
    return wait_approval("AWAIT_REVIEW", "flagged by fixed threshold; staff review task created")


def rw_await_review(orch, wf):
    status, ap = _decision(wf)
    if status == "pending":
        return wait_approval("AWAIT_REVIEW")
    if status == "expired":
        return escalate("review task not handled in time")
    with session() as s:
        obs = s.get(Observation, wf.data["checkin_id"])
        if obs:
            obs.status = "reviewed"
    return complete("reviewed" if status == "approved" else "review_returned")


# =========================================================================== RESTOCK
def rs_draft(orch, wf):
    task = {"horizon_days": 14, "trigger": wf.data.get("trigger", "stock_low"),
            "rejection_reason": wf.data.get("rejection_reason")}
    run = SupplyAgent(orch.llm).run(task, workflow_id=wf.id, task_key=_attempt_key(wf, "order"))
    if run.status != "DONE":
        return fail(f"supply agent {run.status}: {run.error}")
    r = run.result
    if r["outcome"] == "no_restock_needed":
        return complete("no_restock_needed")
    if not r.get("approval_id"):
        return fail("order drafted but approval could not be requested")
    wf.data.update(order_id=r["order_id"], approval_id=r["approval_id"])
    return wait_approval("AWAIT_ORDER_APPROVAL", "order draft awaiting approval")


def rs_await_order(orch, wf):
    status, ap = _decision(wf)
    if status == "pending":
        return wait_approval("AWAIT_ORDER_APPROVAL")
    if status == "approved":
        return complete("order_approved")
    return _redraft_or_stop(wf, ap, "DRAFT_ORDER", "order_rejected")


WORKFLOWS: dict[str, WorkflowDef] = {
    "BOOKING": WorkflowDef("SCHEDULE", {"SCHEDULE": booking_schedule, "AWAIT_BOOKING_APPROVAL": booking_await_approval,
                                        "BOOK": booking_book}),
    "POST_VISIT": WorkflowDef("DRAFT_MESSAGE", {
        "DRAFT_MESSAGE": pv_draft, "AWAIT_MSG_APPROVAL": pv_await_msg, "SEND": pv_send,
        "AWAIT_TIMER": pv_await_timer, "PROPOSE_SLOT": pv_propose,
        "AWAIT_BOOKING_APPROVAL": pv_await_booking, "BOOK": pv_book}),
    "RECOVERY_WATCH": WorkflowDef("EVALUATE", {"EVALUATE": rw_evaluate, "AWAIT_REVIEW": rw_await_review}),
    "RESTOCK": WorkflowDef("DRAFT_ORDER", {"DRAFT_ORDER": rs_draft, "AWAIT_ORDER_APPROVAL": rs_await_order}),
}

CREATING_EVENTS = {
    "BOOKING_REQUESTED": "BOOKING",
    "VISIT_COMPLETED": "POST_VISIT",
    "CHECKIN_RECEIVED": "RECOVERY_WATCH",
    "STOCK_LOW": "RESTOCK",
}
