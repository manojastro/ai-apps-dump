"""High-level operations that combine services with workflow resumption (used by API, MCP and seeding)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.orchestration import evaluate_verification
from app.approvals import service as approvals
from app.core.types import utcnow
from app.graphs.runner import WorkflowConflict, get_runner
from app.integrations.defender.mock import MockDefenderAdapter
from app.models.enterprise import Asset
from app.models.enums import FindingStatus, RemediationState, VerificationState, WorkflowStatus
from app.models.remediation import ApprovalRequest, RemediationPlan
from app.models.servicenow import ServiceNowRecord
from app.models.vulnerability import Finding, ScanEvidence
from app.models.workflow import WorkflowEvent, WorkflowRun
from app.security.auth import Principal
from app.services.audit import record_audit
from app.services.servicenow_sync import ServiceNowSyncService

NON_OVERRIDABLE = {"asset_unresolved", "unsafe_instruction", "invalid_citation", "missing_rollback", "missing_verification"}


def _run_for_plan(db: Session, plan_id: str) -> WorkflowRun | None:
    plan = db.get(RemediationPlan, plan_id)
    if plan is None or not plan.workflow_run_id:
        return None
    return db.get(WorkflowRun, plan.workflow_run_id)


def request_approval(
    db: Session, plan_id: str, actor: Principal, comment: str | None, assigned_approver_id: str | None = None
) -> ApprovalRequest:
    req = approvals.request_approval(db, plan_id, actor, comment, assigned_approver_id)
    run = _run_for_plan(db, plan_id)
    if run is not None:
        run.waiting_reason = "Approval requested; awaiting approver decision"
        db.add(
            WorkflowEvent(
                workflow_run_id=run.id,
                event_type="approval_requested",
                node="human_approval",
                message=f"Approval requested by {actor.full_name}",
                payload={"approval_request_id": req.id},
            )
        )
    db.commit()
    return req


def decide_approval(db: Session, approval_id: str, actor: Principal, decision: str, comment: str | None) -> ApprovalRequest:
    req = approvals.decide(db, approval_id, actor, decision, comment)
    run = _run_for_plan(db, req.plan_id)
    db.commit()
    if run is not None and decision in ("approve", "reject") and run.status == WorkflowStatus.WAITING_APPROVAL:
        get_runner().resume(
            run.id,
            {"type": "approval", "approval_request_id": req.id, "actor_id": actor.id},
            expected={WorkflowStatus.WAITING_APPROVAL},
        )
    elif run is not None:
        with_db_event(db, run.id, "human_approval", f"Approver requested changes: {comment}")
    return req


def with_db_event(db: Session, run_id: str, node: str, message: str) -> None:
    db.add(WorkflowEvent(workflow_run_id=run_id, event_type="human_input", node=node, message=message, payload={}))
    db.commit()


def manual_review(db: Session, run_id: str, actor: Principal, action: str, asset_id: str | None, note: str | None) -> None:
    run = db.get(WorkflowRun, run_id)
    if run is None or run.status != WorkflowStatus.WAITING_MANUAL_REVIEW:
        raise WorkflowConflict("Workflow is not waiting for manual review")
    finding = db.get(Finding, run.finding_id)
    assert finding is not None
    if action == "asset_resolved":
        asset = db.get(Asset, asset_id or "")
        if asset is None:
            raise WorkflowConflict("Select a valid CMDB asset to resolve the match")
        candidates = {c.get("asset_id") for c in finding.correlation_candidates or []}
        if candidates and asset.id not in candidates:
            raise WorkflowConflict("Asset must be one of the correlation candidates")
        previous = finding.asset_id
        finding.asset_id = asset.id
        finding.correlation_status = "matched"
        finding.correlation_confidence = 1.0
        finding.source_evidence = {
            **finding.source_evidence,
            "match_rule": "analyst_confirmed",
            "match_explanation": f"Confirmed by {actor.email}: {note or ''}",
        }
        record_audit(
            db,
            actor=actor,
            action="asset_match_confirmed",
            target_type="finding",
            target_id=finding.id,
            previous_state={"asset_id": previous},
            new_state={"asset_id": asset.id},
            details={"note": note},
        )
    elif action == "proceed":
        plan = db.get(RemediationPlan, run.plan_id) if run.plan_id else None
        if plan is not None:
            validation = dict(plan.validation or {})
            issues = []
            for issue in validation.get("issues", []):
                if issue.get("blocking"):
                    if issue["code"] in NON_OVERRIDABLE:
                        raise WorkflowConflict(f"Issue '{issue['code']}' cannot be overridden; fix the plan or dismiss")
                    issue = {
                        **issue,
                        "blocking": False,
                        "severity": "acknowledged",
                        "acknowledged_by": actor.email,
                        "acknowledged_note": note,
                    }
                issues.append(issue)
            plan.validation = {**validation, "issues": issues, "route": "approval", "acknowledged_by": actor.email}
            if plan.status == "DRAFT":
                plan.status = "ASSESSMENT_COMPLETE"
        record_audit(
            db, actor=actor, action="manual_review_override", target_type="workflow_run", target_id=run_id, details={"note": note}
        )
    elif action == "dismiss":
        record_audit(
            db,
            actor=actor,
            action="investigation_dismissed",
            target_type="workflow_run",
            target_id=run_id,
            details={"note": note},
        )
    else:
        raise WorkflowConflict(f"Unknown manual review action '{action}'")
    db.commit()
    get_runner().resume(
        run_id,
        {"type": "manual_review", "action": action, "asset_id": asset_id, "note": note, "actor_id": actor.id},
        expected={WorkflowStatus.WAITING_MANUAL_REVIEW},
    )


def retry_sync(db: Session, approval_id: str, actor: Principal) -> dict[str, Any]:
    req = db.get(ApprovalRequest, approval_id)
    if req is None:
        raise WorkflowConflict("Approval request not found")
    run = _run_for_plan(db, req.plan_id)
    record_audit(db, actor=actor, action="servicenow_sync_retry_requested", target_type="approval_request", target_id=approval_id)
    db.commit()
    if run is not None and run.status == WorkflowStatus.WAITING_SYNC_RETRY:
        get_runner().resume(run.id, {"type": "sync_retry", "actor_id": actor.id}, expected={WorkflowStatus.WAITING_SYNC_RETRY})
        return {"mode": "workflow_resumed", "run_id": run.id}
    outcome = ServiceNowSyncService(db).sync_approved_plan(approval_id, actor)
    db.commit()
    return {
        "mode": "direct",
        "ok": outcome.ok,
        "error": outcome.error,
        "gate_reasons": outcome.gate_reasons,
        "records": [r.number for r in outcome.records],
    }


def refresh_servicenow_status(db: Session, actor: Principal, plan_id: str | None = None) -> list[ServiceNowRecord]:
    q = select(ServiceNowRecord).where(ServiceNowRecord.sys_id.is_not(None))
    if plan_id:
        q = q.where(ServiceNowRecord.plan_id == plan_id)
    records = list(db.scalars(q))
    svc = ServiceNowSyncService(db)
    for rec in records:
        svc.refresh_status(rec, actor)
    db.commit()
    return records


def submit_rescan(db: Session, finding_id: str, actor: Principal) -> ScanEvidence:
    """Ask the scanner for fresh evidence on the finding's asset, then trigger verification."""
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise WorkflowConflict("Finding not found")
    if finding.scanner not in ("mock_defender",):
        raise WorkflowConflict(f"Targeted rescan is not supported for scanner '{finding.scanner}'; upload scan evidence instead")
    result = MockDefenderAdapter(db).rescan(
        finding.reported_device_id, finding.reported_asset_identifier, finding.vulnerability.cve_id
    )
    ev = ScanEvidence(
        finding_id=finding.id,
        asset_identifier=result.asset_identifier,
        device_id=result.device_id,
        cve_id=result.cve_id,
        scanner=finding.scanner,
        scan_id=result.scan_id,
        scanned_at=result.scanned_at,
        vulnerable=result.vulnerable,
        software_name=result.software_name,
        software_version=result.software_version,
        kind="rescan",
        raw={**result.raw, "detail": result.detail},
        submitted_by=actor.email,
    )
    db.add(ev)
    record_audit(
        db,
        actor=actor,
        action="scan_evidence_collected",
        target_type="finding",
        target_id=finding.id,
        details={"scan_id": ev.scan_id, "vulnerable": ev.vulnerable, "version": ev.software_version},
    )
    db.commit()
    _after_evidence(db, finding, actor)
    return ev


def submit_uploaded_evidence(db: Session, finding_id: str, actor: Principal, data: dict[str, Any]) -> ScanEvidence:
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise WorkflowConflict("Finding not found")
    ev = ScanEvidence(
        finding_id=finding.id,
        asset_identifier=str(data["asset_identifier"])[:255],
        device_id=data.get("device_id"),
        cve_id=finding.vulnerability.cve_id,
        scanner=str(data.get("scanner", "upload"))[:32],
        scan_id=str(data.get("scan_id") or f"upload-{utcnow().strftime('%Y%m%d%H%M%S')}")[:64],
        scanned_at=data["scanned_at"],
        vulnerable=bool(data["vulnerable"]),
        software_name=data.get("software_name"),
        software_version=data.get("software_version"),
        kind="upload",
        raw={"uploaded": True},
        submitted_by=actor.email,
    )
    db.add(ev)
    record_audit(
        db,
        actor=actor,
        action="scan_evidence_uploaded",
        target_type="finding",
        target_id=finding.id,
        details={"scan_id": ev.scan_id, "vulnerable": ev.vulnerable},
    )
    db.commit()
    _after_evidence(db, finding, actor)
    return ev


def _after_evidence(db: Session, finding: Finding, actor: Principal) -> None:
    run = db.scalar(
        select(WorkflowRun).where(WorkflowRun.finding_id == finding.id, WorkflowRun.status == WorkflowStatus.WAITING_EVIDENCE)
    )
    if run is not None:
        get_runner().resume(run.id, {"type": "evidence", "actor_id": actor.id}, expected={WorkflowStatus.WAITING_EVIDENCE})
        return
    # No workflow waiting (e.g. imported history): evaluate directly with the same rules.
    plan = db.scalar(
        select(RemediationPlan).where(RemediationPlan.finding_id == finding.id).order_by(RemediationPlan.created_at.desc())
    )
    result = evaluate_verification(db, finding, plan)
    previous = finding.verification_state
    finding.verification_state = result.verification_state
    if result.verification_state == VerificationState.VERIFIED_REMEDIATED:
        finding.status = FindingStatus.REMEDIATED
        finding.remediated_at = utcnow()
        if plan is not None:
            plan.remediation_state = RemediationState.IMPLEMENTED
    record_audit(
        db,
        actor=actor,
        action="verification_evaluated",
        target_type="finding",
        target_id=finding.id,
        previous_state={"verification_state": previous},
        new_state={"verification_state": finding.verification_state},
        details={"checks": result.checks},
    )
    db.commit()
