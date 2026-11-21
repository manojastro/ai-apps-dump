"""Deterministic workflow engine. Every transition is persisted; unfinished workflows resume after a crash.

Crash safety comes from three things working together:
1. Each step handler is idempotent: all state-changing tool calls use deterministic idempotency keys
   (workflow id + step tag + attempt number), so re-running a half-finished step does not repeat actions.
2. The transition is persisted AFTER the step's work, guarded by an optimistic version check.
3. The queue is at-least-once: an event whose worker died is redelivered after its lease expires.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Callable

from sqlalchemy import select, update

from app import clock
from app.data.db import session
from app.data.models import Approval, Workflow
from app.llm.client import LLMClient, get_llm
from app.obs.tracing import span
from app.queue import outbox

TERMINAL = {"COMPLETED", "FAILED", "ESCALATED"}


class SimulatedCrash(BaseException):
    """Raised by fault injectors to emulate the process being killed (not caught by workers)."""


class ConcurrencyConflict(Exception):
    """Another worker advanced this workflow first; the event is retried."""


@dataclass
class StepResult:
    kind: str  # goto | wait_approval | wait_timer | complete | escalate | fail
    step: str | None = None
    note: str = ""
    outcome: str | None = None


def goto(step: str, note: str = "") -> StepResult:
    return StepResult("goto", step, note)


def wait_approval(step: str, note: str = "") -> StepResult:
    return StepResult("wait_approval", step, note)


def wait_timer(step: str, note: str = "") -> StepResult:
    return StepResult("wait_timer", step, note)


def complete(outcome: str, note: str = "") -> StepResult:
    return StepResult("complete", None, note, outcome)


def escalate(note: str) -> StepResult:
    return StepResult("escalate", None, note)


def fail(note: str) -> StepResult:
    return StepResult("fail", None, note)


@dataclass
class WorkflowState:
    id: str
    type: str
    step: str
    status: str
    data: dict
    version: int
    history: list = field(default_factory=list)


class CrashAfter:
    """Fault injector: raise SimulatedCrash at the n-th crash point (1-based)."""

    def __init__(self, n: int):
        self.n, self.seen, self.fired, self.point = n, 0, False, None

    def __call__(self, point: str) -> None:
        self.seen += 1
        if self.seen == self.n and not self.fired:
            self.fired, self.point = True, point
            raise SimulatedCrash(point)


class Orchestrator:
    def __init__(self, llm: LLMClient | None = None, fault: Callable[[str], None] | None = None):
        self.llm = llm or get_llm()
        self.fault = fault or (lambda point: None)

    # ------------------------------------------------------------------ events
    def handle_event(self, ev: outbox.ClaimedEvent) -> None:
        from app.orchestrator.workflows import CREATING_EVENTS, WORKFLOWS

        with span("event.process", {"event_id": ev.id, "type": ev.type}):
            p = ev.payload
            if ev.type in CREATING_EVENTS:
                wf_type = CREATING_EVENTS[ev.type]
                wf_id = f"{wf_type.lower()}-{ev.id}"
                self._create(wf_id, wf_type, WORKFLOWS[wf_type].initial, dict(p), ev.id)
                self.advance(wf_id)
            elif ev.type == "TIMER_DUE":
                if p.get("workflow_id"):
                    self._wake_timer(p["workflow_id"])
                elif p.get("kind") == "nightly_restock":
                    wf_id = f"restock-{ev.id}"
                    self._create(wf_id, "RESTOCK", WORKFLOWS["RESTOCK"].initial, {"trigger": "nightly"}, ev.id)
                    self.advance(wf_id)
                    if p.get("recurring"):
                        nxt = clock.now() + timedelta(days=1)
                        outbox.enqueue("TIMER_DUE", p, available_at=nxt, dedupe_key=f"nightly:{nxt:%Y%m%d}")
            elif ev.type == "APPROVAL_DECIDED":
                if p.get("workflow_id"):
                    self.advance(p["workflow_id"])
            self.fault("after_handle_event")

    def _create(self, wf_id: str, wf_type: str, step: str, data: dict, event_id: int | None) -> None:
        now = clock.now()
        with session() as s:
            if s.get(Workflow, wf_id) is None:
                s.add(Workflow(id=wf_id, type=wf_type, status="RUNNING", step=step, data=data, event_id=event_id,
                               version=0, created_at=now, updated_at=now,
                               history=[{"ts": now.isoformat(), "from": None, "to": step, "status": "RUNNING",
                                         "note": "created"}]))

    def _wake_timer(self, wf_id: str) -> None:
        state = self.load(wf_id)
        if state is None or state.status in TERMINAL:
            return
        if not state.data.get("timer_fired"):
            data = {**state.data, "timer_fired": True}
            self._persist(state, state.step, "RUNNING", data, "timer fired")
        self.advance(wf_id)

    # ------------------------------------------------------------------ persistence
    def load(self, wf_id: str) -> WorkflowState | None:
        with session() as s:
            w = s.get(Workflow, wf_id)
            if w is None:
                return None
            return WorkflowState(w.id, w.type, w.step, w.status, copy.deepcopy(w.data), w.version,
                                 copy.deepcopy(w.history))

    def _persist(self, state: WorkflowState, step: str, status: str, data: dict, note: str) -> None:
        now = clock.now()
        history = state.history + [{"ts": now.isoformat(), "from": state.step, "to": step, "status": status,
                                    "note": note}]
        with session() as s:
            r = s.execute(update(Workflow).where(Workflow.id == state.id, Workflow.version == state.version)
                          .values(step=step, status=status, data=data, history=history,
                                  version=state.version + 1, updated_at=now))
            if r.rowcount != 1:
                raise ConcurrencyConflict(f"workflow {state.id} changed concurrently")
        state.step, state.status, state.data, state.history = step, status, data, history
        state.version += 1

    # ------------------------------------------------------------------ advancing
    def advance(self, wf_id: str, max_steps: int = 50) -> WorkflowState | None:
        from app.orchestrator.workflows import WORKFLOWS

        for _ in range(max_steps):
            state = self.load(wf_id)
            if state is None or state.status in TERMINAL:
                return state
            handler = WORKFLOWS[state.type].steps[state.step]
            working = WorkflowState(**{**state.__dict__, "data": copy.deepcopy(state.data)})
            with span("workflow.step", {"workflow_id": wf_id, "type": state.type, "step": state.step}) as sp:
                res = handler(self, working)
                sp.set_attribute("result", res.kind)
            self.fault(f"{state.type}:{state.step}")  # crash window: work done, transition not yet saved
            new_step, new_status, data = state.step, state.status, working.data
            if res.kind == "goto":
                new_step, new_status = res.step, "RUNNING"
            elif res.kind == "wait_approval":
                new_step, new_status = res.step, "WAITING_APPROVAL"
            elif res.kind == "wait_timer":
                new_step, new_status = res.step, "RUNNING" if data.get("timer_fired") else "WAITING_TIMER"
            elif res.kind == "complete":
                new_status, data = "COMPLETED", {**data, "outcome": res.outcome}
            elif res.kind == "escalate":
                new_status, data = "ESCALATED", {**data, "outcome": "escalated", "escalation": res.note}
            elif res.kind == "fail":
                new_status, data = "FAILED", {**data, "outcome": "failed", "failure": res.note}
            if (new_step, new_status, data) != (state.step, state.status, state.data):
                self._persist(state, new_step, new_status, data, res.note or res.kind)
            if new_status != "RUNNING":
                return self.load(wf_id)
        return self.load(wf_id)

    # ------------------------------------------------------------------ housekeeping
    def tick(self) -> int:
        """Expire overdue approvals and nudge workflows waiting on decided approvals."""
        from app.approval.service import expire_overdue

        expire_overdue()
        n = 0
        with session() as s:
            waiting = s.execute(select(Workflow.id, Workflow.data).where(Workflow.status == "WAITING_APPROVAL")).all()
            decided = {a for (a,) in s.execute(select(Approval.id).where(Approval.status != "pending"))}
        for wf_id, data in waiting:
            if data.get("approval_id") in decided:
                self.advance(wf_id)
                n += 1
        return n

    def resume(self) -> int:
        """On startup: continue workflows that were mid-step when the process died, and re-check waiting ones."""
        with session() as s:
            running = list(s.scalars(select(Workflow.id).where(Workflow.status == "RUNNING")))
        for wf_id in running:
            self.advance(wf_id)
        self.tick()
        return len(running)
