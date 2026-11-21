"""Simulation driver: runs workers, plays the human approver, and jumps the simulated clock.

Used by tests, the evals and scripts/demo.py. It is *not* used in production workers (they run in real time).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Callable

from sqlalchemy import select

from app import clock
from app.approval import service as approvals
from app.data.db import session
from app.data.models import Approval, StaffUser
from app.orchestrator.engine import Orchestrator
from app.queue import outbox
from app.queue.worker import Worker

# approver(approval) -> ("approve"|"reject", reason) or None to leave it pending
Approver = Callable[[Approval], "tuple[str, str | None] | None"]


def approve_all(_ap: Approval):
    return ("approve", None)


@dataclass
class Decision:
    approval_id: str
    kind: str
    decision: str
    turnaround: timedelta


class Simulation:
    def __init__(self, orch: Orchestrator, approver: Approver | None = approve_all, worker_id: str = "sim-w1"):
        self.orch = orch
        self.approver = approver
        self.worker = Worker(worker_id, orch.handle_event)
        self.decisions: list[Decision] = []

    def pump(self) -> int:
        n = 0
        while True:
            did = self.worker.run_once()
            n += int(did)
            if not did:
                break
        return n + self.orch.tick()

    def staff_for(self, role: str) -> str:
        with session() as s:
            return s.scalars(select(StaffUser.username).where(StaffUser.role == role)).first() or ""

    def decide_pending(self) -> int:
        if self.approver is None:
            return 0
        with session() as s:
            pending = list(s.scalars(select(Approval).where(Approval.status == "pending").order_by(Approval.created_at)))
        n = 0
        for ap in pending:
            d = self.approver(ap)
            if d is None:
                continue
            verb, reason = d
            if verb == "reject" and not reason:
                reason = "Please revise."
            try:
                approvals.decide(ap.id, self.staff_for(ap.required_role), verb == "approve", reason)
            except approvals.ApprovalError:
                continue
            self.decisions.append(Decision(ap.id, ap.kind, verb, clock.now() - ap.created_at))
            n += 1
        return n

    def run(self, max_rounds: int = 200, expire_pending: bool = False) -> None:
        """Run until quiet. Jumps the clock to the next timer (and, if asked, to the next approval expiry)."""
        for _ in range(max_rounds):
            worked = self.pump()
            decided = self.decide_pending()
            if worked or decided:
                continue
            candidates = []
            nxt = outbox.next_pending_time()
            if nxt:
                candidates.append(nxt)
            if expire_pending:
                with session() as s:
                    exp = s.scalars(select(Approval.expires_at).where(Approval.status == "pending")
                                    .order_by(Approval.expires_at)).first()
                if exp:
                    candidates.append(exp)
            if not candidates:
                return
            target = min(candidates)
            if target > clock.now():
                clock.set_to(target)
            elif not worked and not decided:
                return
        raise RuntimeError("simulation did not settle")
