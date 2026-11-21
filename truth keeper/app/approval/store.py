"""Approval service: persists conflicts and proposals, records human decisions, writes audit entries."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select

from app.approval.db import ApprovalRow, ConflictRow, ProposalRow, make_engine, make_session_factory
from app.audit import log as audit
from app.core.models import Conflict, ConflictStatus, ProposalStatus
from app.core.proposer import ProposalResult
from app.core.regressions import build_case, save_case


class NotFound(LookupError):
    pass


class InvalidTransition(ValueError):
    pass


def conflict_to_dict(row: ConflictRow) -> dict:
    return {"id": row.id, "type": row.type, "customer_key": row.customer_key, "evidence": row.evidence,
            "impact": row.impact, "impact_usd": row.impact_usd, "status": row.status,
            "first_detected_at": row.first_detected_at.isoformat(),
            "last_detected_at": row.last_detected_at.isoformat()}


def proposal_to_dict(row: ProposalRow) -> dict:
    return {"id": row.id, "conflict_id": row.conflict_id, "status": row.status, "action": row.action,
            "params": row.params, "explanation": row.explanation, "confidence": row.confidence,
            "needs_human_note": row.needs_human_note, "prompt_version": row.prompt_version, "model": row.model,
            "llm_mode": row.llm_mode, "attempts": row.attempts, "first_try_valid": row.first_try_valid,
            "failure_category": row.failure_category, "failure_reason": row.failure_reason,
            "input_tokens": row.input_tokens, "output_tokens": row.output_tokens, "latency_ms": row.latency_ms,
            "created_at": row.created_at.isoformat(),
            "applied_at": row.applied_at.isoformat() if row.applied_at else None}


class Store:
    def __init__(self, db_path: Path, regressions_dir: Path | None = None):
        self.engine = make_engine(db_path)
        self.Session = make_session_factory(self.engine)
        self.regressions_dir = regressions_dir

    def close(self) -> None:
        self.engine.dispose()

    # ---- conflicts -------------------------------------------------------------------------
    def sync_conflicts(self, conflicts: list[Conflict], actor: str = "pipeline") -> dict[str, int]:
        """Insert new conflicts, refresh evidence of existing ones, mark vanished OPEN ones GONE."""
        seen = {c.id for c in conflicts}
        stats = {"new": 0, "updated": 0, "gone": 0}
        with self.Session.begin() as s:
            for c in conflicts:
                row = s.get(ConflictRow, c.id)
                impact = c.impact.model_dump() if c.impact else None
                if row is None:
                    s.add(ConflictRow(id=c.id, type=c.type.value, customer_key=c.customer_key, evidence=c.evidence,
                                      impact=impact, impact_usd=c.impact.amount_usd if c.impact else 0.0,
                                      status=ConflictStatus.OPEN.value))
                    audit.append(s, actor=actor, event="conflict_detected", entity_type="conflict", entity_id=c.id,
                                 after={"type": c.type.value, "customer_key": c.customer_key})
                    stats["new"] += 1
                else:
                    row.evidence, row.impact = c.evidence, impact
                    row.impact_usd = c.impact.amount_usd if c.impact else 0.0
                    row.last_detected_at = datetime.now(UTC)
                    if row.status != ConflictStatus.OPEN.value:
                        row.status = ConflictStatus.OPEN.value
                    stats["updated"] += 1
            for row in s.scalars(select(ConflictRow).where(ConflictRow.status == ConflictStatus.OPEN.value)):
                if row.id not in seen:
                    row.status = ConflictStatus.GONE.value
                    audit.append(s, actor=actor, event="conflict_gone", entity_type="conflict", entity_id=row.id)
                    stats["gone"] += 1
        return stats

    def get_conflict(self, conflict_id: str) -> dict:
        with self.Session() as s:
            row = s.get(ConflictRow, conflict_id)
            if row is None:
                raise NotFound(f"conflict {conflict_id} not found")
            return conflict_to_dict(row)

    def set_conflict_status(self, s, conflict_id: str, status: ConflictStatus) -> None:
        row = s.get(ConflictRow, conflict_id)
        if row is not None:
            row.status = status.value

    # ---- proposals -------------------------------------------------------------------------
    def save_proposal(self, r: ProposalResult, actor: str = "pipeline") -> dict:
        with self.Session.begin() as s:
            out = r.output
            row = ProposalRow(
                conflict_id=r.conflict_id, status=r.status.value,
                action=out.action.value if out else None, params=out.params if out else None,
                explanation=out.explanation if out else None, confidence=out.confidence if out else None,
                needs_human_note=out.needs_human_note if out else None, prompt_version=r.prompt_version,
                model=r.model, llm_mode=r.llm_mode, attempts=len(r.attempts), first_try_valid=r.first_try_valid,
                failure_category=r.failure_category, failure_reason=r.failure_reason,
                attempt_log=r.attempts_dicts(), input_tokens=r.input_tokens, output_tokens=r.output_tokens,
                latency_ms=r.latency_ms,
            )
            s.add(row)
            s.flush()
            audit.append(s, actor=actor, event="proposal_created", entity_type="proposal", entity_id=str(row.id),
                         after={"status": row.status, "action": row.action, "params": row.params},
                         details={"conflict_id": r.conflict_id, "prompt_version": r.prompt_version,
                                  "model": r.model, "attempts": row.attempts,
                                  "failure_category": r.failure_category})
            return proposal_to_dict(row)

    def latest_proposal_status(self, conflict_id: str) -> str | None:
        with self.Session() as s:
            row = s.scalars(select(ProposalRow).where(ProposalRow.conflict_id == conflict_id)
                            .order_by(ProposalRow.id.desc()).limit(1)).first()
            return row.status if row else None

    def get_proposal(self, proposal_id: int) -> dict:
        with self.Session() as s:
            row = s.get(ProposalRow, proposal_id)
            if row is None:
                raise NotFound(f"proposal {proposal_id} not found")
            conflict = s.get(ConflictRow, row.conflict_id)
            approvals = s.scalars(select(ApprovalRow).where(ApprovalRow.proposal_id == proposal_id)
                                  .order_by(ApprovalRow.id)).all()
            d = proposal_to_dict(row)
            d["attempt_log"] = row.attempt_log
            d["conflict"] = conflict_to_dict(conflict) if conflict else None
            d["approvals"] = [{"decision": a.decision, "reviewer": a.reviewer, "note": a.note,
                               "decided_at": a.decided_at.isoformat()} for a in approvals]
            d["audit"] = [audit.to_dict(e) for e in audit.entries(s, entity_id=str(proposal_id))]
            return d

    def list_queue(self, type: str | None = None, status: str | None = None, min_impact: float | None = None,
                   proposal_status: str | None = None) -> list[dict]:
        """Conflicts joined with their latest proposal, sorted by money at risk (desc)."""
        with self.Session() as s:
            latest = (select(ProposalRow.conflict_id, func.max(ProposalRow.id).label("pid"))
                      .group_by(ProposalRow.conflict_id).subquery())
            q = (select(ConflictRow, ProposalRow)
                 .outerjoin(latest, latest.c.conflict_id == ConflictRow.id)
                 .outerjoin(ProposalRow, ProposalRow.id == latest.c.pid))
            if type:
                q = q.where(ConflictRow.type == type)
            if status:
                q = q.where(ConflictRow.status == status)
            if min_impact is not None:
                q = q.where(ConflictRow.impact_usd >= min_impact)
            if proposal_status:
                q = q.where(ProposalRow.status == proposal_status)
            q = q.order_by(ConflictRow.impact_usd.desc(), ConflictRow.id)
            out = []
            for c, p in s.execute(q).all():
                d = conflict_to_dict(c)
                d["proposal"] = proposal_to_dict(p) if p else None
                out.append(d)
            return out

    # ---- decisions -------------------------------------------------------------------------
    def _decide(self, proposal_id: int, decision: str, reviewer: str, note: str | None) -> dict:
        if not reviewer or not reviewer.strip():
            raise InvalidTransition("reviewer is required")
        with self.Session.begin() as s:
            row = s.get(ProposalRow, proposal_id)
            if row is None:
                raise NotFound(f"proposal {proposal_id} not found")
            if row.status != ProposalStatus.PENDING_REVIEW.value:
                raise InvalidTransition(f"proposal {proposal_id} is {row.status}; only PENDING_REVIEW can be decided")
            before = {"status": row.status}
            row.status = (ProposalStatus.APPROVED if decision == "approve" else ProposalStatus.REJECTED).value
            s.add(ApprovalRow(proposal_id=proposal_id, decision=decision, reviewer=reviewer.strip(), note=note))
            audit.append(s, actor=reviewer.strip(), event=f"proposal_{decision}d", entity_type="proposal",
                         entity_id=str(proposal_id), before=before, after={"status": row.status},
                         details={"note": note, "action": row.action, "params": row.params})
            conflict = s.get(ConflictRow, row.conflict_id)
            snapshot = {"row": proposal_to_dict(row), "attempt_log": row.attempt_log,
                        "conflict": conflict_to_dict(conflict) if conflict else None}
        if decision == "reject" and self.regressions_dir is not None and snapshot["conflict"]:
            c = snapshot["conflict"]
            save_case(self.regressions_dir, build_case(
                source="rejected",
                conflict={"id": c["id"], "type": c["type"], "customer_key": c["customer_key"],
                          "evidence": c["evidence"]},
                prompt_version=snapshot["row"]["prompt_version"],
                recorded_responses=[a.get("raw") for a in snapshot["attempt_log"]],
                expect_mock={"status": "PENDING_REVIEW", "action": snapshot["row"]["action"]},
                expected_action=None,
                note=f"rejected by {reviewer}: {note}",
            ))
        return snapshot["row"]

    def approve(self, proposal_id: int, reviewer: str, note: str | None = None) -> dict:
        return self._decide(proposal_id, "approve", reviewer, note)

    def reject(self, proposal_id: int, reviewer: str, reason: str) -> dict:
        if not reason or not reason.strip():
            raise InvalidTransition("a rejection needs a reason")
        return self._decide(proposal_id, "reject", reviewer, reason)

    def approval_record(self, s, proposal_id: int) -> ApprovalRow | None:
        return s.scalars(select(ApprovalRow).where(ApprovalRow.proposal_id == proposal_id,
                                                   ApprovalRow.decision == "approve")).first()

    def audit_entries(self, entity_id: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        with self.Session() as s:
            return [audit.to_dict(e) for e in audit.entries(s, entity_id=entity_id, limit=limit)]

    def stats(self) -> dict:
        with self.Session() as s:
            def count(model, col, val):
                return s.scalar(select(func.count()).select_from(model).where(col == val)) or 0
            return {
                "conflicts_open": count(ConflictRow, ConflictRow.status, "OPEN"),
                "conflicts_resolved": count(ConflictRow, ConflictRow.status, "RESOLVED"),
                "money_at_risk_open_usd": round(s.scalar(select(func.coalesce(func.sum(ConflictRow.impact_usd), 0.0))
                                                         .where(ConflictRow.status == "OPEN")) or 0.0, 2),
                **{f"proposals_{st.value.lower()}": count(ProposalRow, ProposalRow.status, st.value)
                   for st in ProposalStatus},
            }
