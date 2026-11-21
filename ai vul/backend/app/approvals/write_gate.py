"""Deterministic ServiceNow write gate.

This is the only path to an external write. It re-derives authorisation from the database
on every call - it never trusts workflow state, tool arguments, or model output - so a
prompt, a tampered graph state, or a replayed request cannot bypass human approval.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.approvals.service import SOD_RISK_LEVELS, compute_plan_hash
from app.core.config import get_settings
from app.core.types import canonical_hash
from app.integrations.servicenow.factory import write_allowlist
from app.models.enums import ApprovalState, PlanStatus
from app.models.identity import User
from app.models.remediation import ApprovalRequest, RemediationPlan
from app.security.auth import Principal
from app.security.permissions import Permission, has_permission
from app.services.audit import record_audit


@dataclass
class GateDecision:
    allowed: bool
    reasons: list[str] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)
    snapshot: dict[str, Any] | None = None


def evaluate_write_gate(db: Session, approval_request_id: str, tables: set[str]) -> GateDecision:
    checks: dict[str, bool] = {}
    reasons: list[str] = []

    def check(name: str, ok: bool, reason: str) -> None:
        checks[name] = ok
        if not ok:
            reasons.append(reason)

    req = db.get(ApprovalRequest, approval_request_id)
    if req is None:
        return GateDecision(False, ["approval request not found"], {"approval_exists": False})
    plan = db.get(RemediationPlan, req.plan_id)
    check("approval_exists", True, "")
    check("approval_approved", req.state == ApprovalState.APPROVED, f"approval state is {req.state}, not APPROVED")
    approver = db.get(User, req.decided_by) if req.decided_by else None
    check(
        "approver_authorised",
        bool(approver and approver.is_active and has_permission(approver.role, Permission.APPROVAL_DECIDE)),
        "decision was not made by an active, authorised approver",
    )
    if req.separation_of_duties and (req.risk_level in SOD_RISK_LEVELS or req.risk_level is None) and plan is not None:
        authors = {req.requested_by, plan.created_by, plan.edited_by} - {None}
        check("separation_of_duties", req.decided_by not in authors, "approver is also the requester/author")
    snapshot_ok = canonical_hash(req.payload_snapshot.get("plan", {})) == req.payload_hash
    check("snapshot_integrity", snapshot_ok, "approved payload snapshot hash mismatch")
    check(
        "plan_unchanged",
        plan is not None and compute_plan_hash(plan) == req.payload_hash and plan.status == PlanStatus.APPROVED,
        "plan changed or is no longer in APPROVED state since the approval decision",
    )
    settings = get_settings()
    writes_enabled = settings.servicenow_mode == "mock" or settings.enable_servicenow_writes
    check("writes_enabled", writes_enabled, "ENABLE_SERVICENOW_WRITES is false for the real ServiceNow instance")
    allowed_tables = write_allowlist()
    check(
        "table_allowlisted", tables <= allowed_tables, f"tables {sorted(tables - allowed_tables)} are not on the write allowlist"
    )
    return GateDecision(not reasons, reasons, checks, req.payload_snapshot if not reasons else None)


def authorize_write(db: Session, approval_request_id: str, tables: set[str], actor: Principal) -> GateDecision:
    decision = evaluate_write_gate(db, approval_request_id, tables)
    record_audit(
        db,
        actor=actor,
        action="servicenow_write_gate",
        target_type="approval_request",
        target_id=approval_request_id,
        details={"allowed": decision.allowed, "checks": decision.checks, "reasons": decision.reasons, "tables": sorted(tables)},
        outcome="success" if decision.allowed else "denied",
    )
    return decision
