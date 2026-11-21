"""Fix applier: applies APPROVED proposals to the sandbox only.

Guarantees:
  - nothing changes without an approval record (status APPROVED + an approve row)
  - idempotent: an already-APPLIED proposal is a no-op; each action also checks target state
  - precondition re-check: the conflict must still be detected with the same evidence it was
    approved on; otherwise the proposal becomes STALE and nothing is written
  - every outcome (applied, no-op, stale, refused) writes a before/after audit entry
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import text

from app.adapters.base import sqlite_engine
from app.applier.sandbox import assert_writable
from app.approval.db import ConflictRow, ProposalRow
from app.approval.store import NotFound, Store
from app.audit import log as audit
from app.core.detection import detect_dir
from app.core.models import Action, ConflictStatus, ProposalStatus
from app.tracing import get_tracer


@dataclass
class ApplyResult:
    proposal_id: int
    outcome: str  # applied | already_applied | stale | refused
    message: str
    before: dict | None = None
    after: dict | None = None
    conflict_still_detected: bool | None = None

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def _row(conn, sql: str, **p) -> dict | None:
    r = conn.execute(text(sql), p).mappings().first()
    return dict(r) if r else None


class Applier:
    def __init__(self, store: Store, sandbox_dir: Path, generated_dir: Path):
        self.store = store
        self.sandbox_dir = Path(sandbox_dir)
        self.generated_dir = Path(generated_dir)

    def _db(self, name: str) -> Path:
        return assert_writable(self.sandbox_dir / name, self.sandbox_dir, self.generated_dir)

    # ---- action implementations: each returns (before, after) and is idempotent ------------
    def _exec(self, action: Action, params: dict[str, Any], conflict_id: str, customer_key: str):
        if action == Action.NO_ACTION:
            return {}, {}
        if action in (Action.UPDATE_CRM_STATUS, Action.UPDATE_CRM_PLAN):
            col, val = ("status", params["new_status"]) if action == Action.UPDATE_CRM_STATUS \
                else ("plan", params["new_plan"])
            with sqlite_engine(self._db("crm.db")) as eng, eng.begin() as conn:
                before = _row(conn, "SELECT id, status, plan FROM accounts WHERE id=:id", id=params["account_id"])
                if before is None:
                    raise NotFound(f"CRM account {params['account_id']} not found")
                if before[col] != val:
                    conn.execute(text(f"UPDATE accounts SET {col}=:v WHERE id=:id"), {"v": val,
                                                                                     "id": params["account_id"]})
                after = _row(conn, "SELECT id, status, plan FROM accounts WHERE id=:id", id=params["account_id"])
            return before, after
        if action == Action.CANCEL_SUBSCRIPTION:
            q = "SELECT subscription_id, status, next_charge_date FROM subscriptions WHERE subscription_id=:s"
            with sqlite_engine(self._db("billing.db")) as eng, eng.begin() as conn:
                before = _row(conn, q, s=params["subscription_id"])
                if before is None:
                    raise NotFound(f"subscription {params['subscription_id']} not found")
                if before["status"] != "cancelled":
                    conn.execute(text("UPDATE subscriptions SET status='cancelled', next_charge_date=NULL"
                                      " WHERE subscription_id=:s"), {"s": params["subscription_id"]})
                after = _row(conn, q, s=params["subscription_id"])
            return before, after
        if action == Action.UNSUBSCRIBE_CONTACT:
            q = "SELECT contact_id, subscribed, lifecycle_stage FROM contacts WHERE contact_id=:c"
            with sqlite_engine(self._db("marketing.db")) as eng, eng.begin() as conn:
                before = _row(conn, q, c=params["contact_id"])
                if before is None:
                    raise NotFound(f"contact {params['contact_id']} not found")
                if before["subscribed"]:
                    conn.execute(text("UPDATE contacts SET subscribed=0 WHERE contact_id=:c"),
                                 {"c": params["contact_id"]})
                after = _row(conn, q, c=params["contact_id"])
            return before, after
        if action == Action.MERGE_BILLING_DUPLICATES:
            keep, remove = params["keep_customer_id"], params["remove_customer_id"]
            q = ("SELECT c.customer_id, c.merged_into, s.subscription_id, s.status FROM customers c"
                 " LEFT JOIN subscriptions s ON s.customer_id=c.customer_id WHERE c.customer_id=:c")
            with sqlite_engine(self._db("billing.db")) as eng, eng.begin() as conn:
                before = _row(conn, q, c=remove)
                if before is None or _row(conn, q, c=keep) is None:
                    raise NotFound("billing customer to merge not found")
                if before["merged_into"] != keep:
                    conn.execute(text("UPDATE customers SET merged_into=:k WHERE customer_id=:r"),
                                 {"k": keep, "r": remove})
                    conn.execute(text("UPDATE subscriptions SET status='cancelled', next_charge_date=NULL"
                                      " WHERE customer_id=:r"), {"r": remove})
                after = _row(conn, q, c=remove)
            return before, after
        if action == Action.FLAG_FOR_FINANCE_REVIEW:
            q = "SELECT flag_id, conflict_id, status, action_reason FROM review_flags WHERE conflict_id=:c"
            with sqlite_engine(self._db("billing.db")) as eng, eng.begin() as conn:
                before = _row(conn, q, c=conflict_id)
                if before is None:
                    conn.execute(text("INSERT INTO review_flags VALUES (:f, :c, :k, :r, :t, 'open')"),
                                 {"f": f"RF-{conflict_id}", "c": conflict_id, "k": customer_key,
                                  "r": params["reason"], "t": datetime.now(UTC).isoformat()})
                after = _row(conn, q, c=conflict_id)
            return before or {}, after
        raise ValueError(f"unsupported action {action}")  # pragma: no cover

    # ---- main entry point ---------------------------------------------------------------------
    def apply(self, proposal_id: int, actor: str) -> ApplyResult:
        tracer = get_tracer()
        with tracer.start_as_current_span("applier.apply") as span:
            span.set_attribute("tk.proposal_id", proposal_id)
            res = self._apply(proposal_id, actor)
            span.set_attribute("tk.outcome", res.outcome)
            return res

    def _apply(self, proposal_id: int, actor: str) -> ApplyResult:
        store = self.store
        with store.Session.begin() as s:
            p = s.get(ProposalRow, proposal_id)
            if p is None:
                raise NotFound(f"proposal {proposal_id} not found")
            if p.status == ProposalStatus.APPLIED.value:
                audit.append(s, actor=actor, event="apply_noop_already_applied", entity_type="proposal",
                             entity_id=str(proposal_id))
                return ApplyResult(proposal_id, "already_applied", "fix was already applied; nothing changed")
            approval = store.approval_record(s, proposal_id)
            if p.status != ProposalStatus.APPROVED.value or approval is None:
                audit.append(s, actor=actor, event="apply_refused_not_approved", entity_type="proposal",
                             entity_id=str(proposal_id), details={"status": p.status})
                return ApplyResult(proposal_id, "refused", f"proposal is {p.status}; only APPROVED fixes apply")
            conflict = s.get(ConflictRow, p.conflict_id)
            action, params = Action(p.action), dict(p.params or {})
            approved_evidence = conflict.evidence
            conflict_id, customer_key = conflict.id, conflict.customer_key

        # precondition: the same conflict must still be detected, with unchanged evidence
        current = {c.id: c for c in detect_dir(self.sandbox_dir, respect_review_flags=False).conflicts}
        now = current.get(conflict_id)
        if now is None or now.evidence != approved_evidence:
            reason = "conflict no longer detected" if now is None else "evidence changed since approval"
            with store.Session.begin() as s:
                s.get(ProposalRow, proposal_id).status = ProposalStatus.STALE.value
                audit.append(s, actor=actor, event="apply_stale", entity_type="proposal", entity_id=str(proposal_id),
                             before={"evidence": approved_evidence}, after={"evidence": now.evidence if now else None},
                             details={"reason": reason})
            return ApplyResult(proposal_id, "stale", f"precondition failed: {reason}; nothing applied")

        before, after = self._exec(action, params, conflict_id, customer_key)
        still = conflict_id in {c.id for c in detect_dir(self.sandbox_dir).conflicts}
        with store.Session.begin() as s:
            p = s.get(ProposalRow, proposal_id)
            p.status, p.applied_at = ProposalStatus.APPLIED.value, datetime.now(UTC)
            if not still:
                store.set_conflict_status(s, conflict_id, ConflictStatus.RESOLVED)
            audit.append(s, actor=actor, event="fix_applied", entity_type="proposal", entity_id=str(proposal_id),
                         before=before, after=after,
                         details={"action": action.value, "params": params, "conflict_id": conflict_id,
                                  "conflict_still_detected": still, "sandbox": str(self.sandbox_dir)})
        return ApplyResult(proposal_id, "applied", f"{action.value} applied to sandbox", before, after, still)
