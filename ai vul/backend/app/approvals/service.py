"""Human-in-the-loop approval engine.

Guarantees
----------
* Only principals with ``approval:decide`` may decide; denied attempts are recorded.
* Separation of duties: the requester (and the plan's author/editor) cannot approve their own
  high/critical-risk request when SoD is enabled.
* Approved payloads are immutable snapshots with a SHA-256 hash; any material plan change
  invalidates open or not-yet-synced approvals.
* Decisions use an atomic compare-and-set (``WHERE state='PENDING'``) so concurrent or
  repeated submissions cannot produce two decisions.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.approvals.state_machine import PLAN_TRANSITIONS, check_transition
from app.core.config import get_settings
from app.core.types import canonical_hash, utcnow
from app.models.enums import ApprovalState, PlanStatus
from app.models.identity import User
from app.models.remediation import ApprovalDecision, ApprovalRequest, RemediationPlan
from app.models.servicenow import ServiceNowRecord
from app.models.vulnerability import Finding
from app.security.auth import Principal
from app.security.permissions import Permission
from app.services.audit import record_audit

APPROVAL_POLICY_VERSION = "aegis-approval-policy-v1"
SOD_RISK_LEVELS = {"critical", "high"}

MATERIAL_FIELDS = (
    "title",
    "summary",
    "recommended_action",
    "target_version",
    "prerequisites",
    "implementation_steps",
    "verification_steps",
    "rollback_steps",
    "testing_requirements",
    "expected_impact",
    "maintenance_window",
    "required_approvers",
)


class ApprovalError(Exception):
    status_code = 400


class ApprovalForbidden(ApprovalError):
    status_code = 403


class ApprovalConflict(ApprovalError):
    status_code = 409


class ApprovalInvalid(ApprovalError):
    status_code = 422


def plan_material_payload(plan: RemediationPlan) -> dict[str, Any]:
    return {f: getattr(plan, f) for f in MATERIAL_FIELDS} | {"finding_id": plan.finding_id, "plan_id": plan.id}


def compute_plan_hash(plan: RemediationPlan) -> str:
    return canonical_hash(plan_material_payload(plan))


def _context_snapshot(db: Session, plan: RemediationPlan) -> dict[str, Any]:
    finding = db.get(Finding, plan.finding_id)
    assert finding is not None
    asset, vuln = finding.asset, finding.vulnerability
    service = asset.business_service if asset else None
    return {
        "finding_id": finding.id,
        "cve_id": vuln.cve_id,
        "risk_score": finding.risk_score,
        "risk_level": finding.risk_level,
        "priority": finding.priority,
        "asset": None
        if asset is None
        else {
            "id": asset.id,
            "hostname": asset.hostname,
            "environment": asset.environment,
            "cmdb_sys_id": asset.cmdb_sys_id,
            "business_service": service.name if service else None,
            "business_service_sys_id": service.cmdb_sys_id if service else None,
        },
        "change_impact": plan.change_impact,
    }


def _plan_for_update(db: Session, plan_id: str) -> RemediationPlan:
    plan = db.scalar(select(RemediationPlan).where(RemediationPlan.id == plan_id).with_for_update())
    if plan is None:
        raise ApprovalInvalid("Remediation plan not found")
    return plan


def request_approval(
    db: Session, plan_id: str, actor: Principal, comment: str | None = None, assigned_approver_id: str | None = None
) -> ApprovalRequest:
    if not actor.can(Permission.APPROVAL_REQUEST):
        raise ApprovalForbidden("Not permitted to request approvals")
    plan = _plan_for_update(db, plan_id)
    if plan.status not in (PlanStatus.DRAFT, PlanStatus.ASSESSMENT_COMPLETE, PlanStatus.CHANGES_REQUESTED):
        raise ApprovalConflict(f"Plan is {plan.status}; approval can only be requested for a draft or assessed plan")
    blocking = [i for i in (plan.validation or {}).get("issues", []) if i.get("blocking")]
    if blocking:
        raise ApprovalInvalid(f"Plan has blocking validation issues: {[i['code'] for i in blocking]}")
    if db.scalar(
        select(ApprovalRequest).where(ApprovalRequest.plan_id == plan.id, ApprovalRequest.state == ApprovalState.PENDING)
    ):
        raise ApprovalConflict("An approval request is already pending for this plan")
    if assigned_approver_id:
        approver = db.get(User, assigned_approver_id)
        if approver is None or not approver.is_active or approver.role not in ("approver", "admin"):
            raise ApprovalInvalid("Assigned approver must be an active approver")

    material = plan_material_payload(plan)
    plan.content_hash = canonical_hash(material)
    context = _context_snapshot(db, plan)
    req = ApprovalRequest(
        plan_id=plan.id,
        requested_by=actor.id,
        assigned_approver_id=assigned_approver_id,
        state=ApprovalState.PENDING,
        risk_level=context["risk_level"],
        payload_snapshot={"plan": material, "context": context, "revision": plan.revision},
        payload_hash=plan.content_hash,
        policy_version=APPROVAL_POLICY_VERSION,
        separation_of_duties=get_settings().separation_of_duties,
        request_comment=(comment or "")[:2000] or None,
    )
    check_transition(PLAN_TRANSITIONS, plan.status, PlanStatus.PENDING_APPROVAL, "plan")
    previous = plan.status
    plan.status = PlanStatus.PENDING_APPROVAL
    db.add(req)
    db.flush()
    record_audit(
        db,
        actor=actor,
        action="approval_requested",
        target_type="remediation_plan",
        target_id=plan.id,
        previous_state={"status": previous},
        new_state={"status": plan.status, "approval_request_id": req.id, "payload_hash": req.payload_hash},
        details={"risk_level": req.risk_level, "revision": plan.revision},
    )
    return req


def _deny(db: Session, req: ApprovalRequest, actor: Principal, decision: str, reason: str, exc: type[ApprovalError]) -> None:
    db.add(ApprovalDecision(approval_request_id=req.id, actor_id=actor.id, decision=decision, outcome="denied", reason=reason))
    record_audit(
        db,
        actor=actor,
        action=f"approval_{decision}_denied",
        target_type="approval_request",
        target_id=req.id,
        details={"reason": reason, "plan_id": req.plan_id},
        outcome="denied",
    )
    db.commit()
    raise exc(reason)


DECISION_STATE = {
    "approve": ApprovalState.APPROVED,
    "reject": ApprovalState.REJECTED,
    "request_changes": ApprovalState.CHANGES_REQUESTED,
}
PLAN_STATE = {
    "approve": PlanStatus.APPROVED,
    "reject": PlanStatus.REJECTED,
    "request_changes": PlanStatus.CHANGES_REQUESTED,
}


def decide(db: Session, approval_id: str, actor: Principal, decision: str, comment: str | None = None) -> ApprovalRequest:
    if decision not in DECISION_STATE:
        raise ApprovalInvalid(f"Unknown decision '{decision}'")
    req = db.get(ApprovalRequest, approval_id)
    if req is None:
        raise ApprovalInvalid("Approval request not found")
    if not actor.can(Permission.APPROVAL_DECIDE):
        _deny(db, req, actor, decision, f"role '{actor.role}' is not authorised to decide approvals", ApprovalForbidden)
    plan = db.get(RemediationPlan, req.plan_id)
    assert plan is not None
    if req.separation_of_duties and (req.risk_level in SOD_RISK_LEVELS or req.risk_level is None):
        authors = {req.requested_by, plan.created_by, plan.edited_by} - {None}
        if actor.id in authors:
            _deny(
                db,
                req,
                actor,
                decision,
                "separation of duties: requester/author cannot decide their own high-risk request",
                ApprovalForbidden,
            )
    if req.assigned_approver_id and actor.id != req.assigned_approver_id and actor.role != "admin":
        _deny(db, req, actor, decision, "request is assigned to a different approver", ApprovalForbidden)
    if decision in ("reject", "request_changes") and not (comment and comment.strip()):
        raise ApprovalInvalid("A comment is required when rejecting or requesting changes")
    if req.state != ApprovalState.PENDING:
        raise ApprovalConflict(f"Approval request already {req.state}")

    # Integrity: the snapshot must still hash to the approved value and match the live plan.
    snapshot_hash = canonical_hash(req.payload_snapshot.get("plan", {}))
    if snapshot_hash != req.payload_hash or compute_plan_hash(plan) != req.payload_hash:
        db.execute(
            update(ApprovalRequest)
            .where(ApprovalRequest.id == req.id, ApprovalRequest.state == ApprovalState.PENDING)
            .values(state=ApprovalState.INVALIDATED, decision_comment="Plan content changed after request")
        )
        plan.status = PlanStatus.DRAFT
        record_audit(
            db,
            actor=actor,
            action="approval_invalidated",
            target_type="approval_request",
            target_id=req.id,
            details={"reason": "payload hash mismatch"},
            outcome="denied",
        )
        db.commit()
        raise ApprovalConflict("Plan changed since approval was requested; the request was invalidated")

    now = utcnow()
    result = db.execute(
        update(ApprovalRequest)
        .where(ApprovalRequest.id == req.id, ApprovalRequest.state == ApprovalState.PENDING)
        .values(
            state=DECISION_STATE[decision], decided_by=actor.id, decided_at=now, decision_comment=(comment or "")[:2000] or None
        )
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:  # type: ignore[attr-defined]
        db.rollback()
        raise ApprovalConflict("Approval request was decided concurrently by another user")
    db.refresh(req)
    previous = plan.status
    check_transition(PLAN_TRANSITIONS, plan.status, PLAN_STATE[decision], "plan")
    plan.status = PLAN_STATE[decision]
    db.add(
        ApprovalDecision(approval_request_id=req.id, actor_id=actor.id, decision=decision, outcome="accepted", comment=comment)
    )
    record_audit(
        db,
        actor=actor,
        action=f"approval_{decision}",
        target_type="approval_request",
        target_id=req.id,
        previous_state={"approval_state": ApprovalState.PENDING, "plan_status": previous},
        new_state={"approval_state": req.state, "plan_status": plan.status},
        details={"plan_id": plan.id, "payload_hash": req.payload_hash, "comment": comment},
    )
    db.flush()
    return req


def cancel_request(db: Session, approval_id: str, actor: Principal) -> ApprovalRequest:
    req = db.get(ApprovalRequest, approval_id)
    if req is None:
        raise ApprovalInvalid("Approval request not found")
    if req.requested_by != actor.id and actor.role != "admin":
        raise ApprovalForbidden("Only the requester or an administrator can cancel a request")
    result = db.execute(
        update(ApprovalRequest)
        .where(ApprovalRequest.id == req.id, ApprovalRequest.state == ApprovalState.PENDING)
        .values(state=ApprovalState.CANCELLED, decided_at=utcnow(), decided_by=actor.id)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:  # type: ignore[attr-defined]
        raise ApprovalConflict("Only pending requests can be cancelled")
    plan = db.get(RemediationPlan, req.plan_id)
    assert plan is not None
    plan.status = PlanStatus.DRAFT
    db.refresh(req)
    record_audit(db, actor=actor, action="approval_cancelled", target_type="approval_request", target_id=req.id)
    return req


def invalidate_for_plan_change(db: Session, plan: RemediationPlan, actor: Principal, reason: str) -> int:
    """Material plan edits invalidate pending approvals and approvals not yet synchronised."""
    synced = db.scalar(select(ServiceNowRecord).where(ServiceNowRecord.plan_id == plan.id))
    if synced is not None:
        raise ApprovalConflict("Plan already synchronised to ServiceNow; create a new revision instead of editing")
    count = 0
    for req in db.scalars(
        select(ApprovalRequest).where(
            ApprovalRequest.plan_id == plan.id, ApprovalRequest.state.in_([ApprovalState.PENDING, ApprovalState.APPROVED])
        )
    ):
        prev = req.state
        req.state = ApprovalState.INVALIDATED
        req.decision_comment = f"Invalidated: {reason}"
        count += 1
        record_audit(
            db,
            actor=actor,
            action="approval_invalidated",
            target_type="approval_request",
            target_id=req.id,
            previous_state={"state": prev},
            new_state={"state": req.state},
            details={"reason": reason},
        )
    return count
