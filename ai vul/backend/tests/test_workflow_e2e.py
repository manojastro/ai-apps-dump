"""End-to-end LangGraph workflow tests on the seeded simulated enterprise (mock AI, mock ServiceNow)."""

from __future__ import annotations

from sqlalchemy import func, select

from app.graphs.runner import WorkflowRunner, get_runner, make_checkpointer, set_runner
from app.models.enums import WorkflowStatus
from app.models.remediation import RemediationPlan
from app.models.servicenow import ServiceNowRecord, SnSimRecord
from app.models.vulnerability import Finding
from app.models.workflow import AgentExecution, ToolCall, WorkflowRun
from app.services import simulation, workflow_ops
from tests.conftest import finding_id, principal


def _run(db, run_id: str) -> WorkflowRun:
    db.expire_all()
    run = db.get(WorkflowRun, run_id)
    assert run is not None
    return run


def _sn_count(db, correlation_prefix: str) -> int:
    rows = db.scalars(select(SnSimRecord).where(SnSimRecord.table_name.in_(["change_request", "change_task"])))
    return sum(1 for r in rows if str(r.fields.get("correlation_id", "")).startswith(correlation_prefix))


def test_full_lifecycle_critical_internet_facing(db) -> None:
    analyst = principal(db, "analyst@northstar.example")
    approver = principal(db, "approver@northstar.example")
    fid = finding_id(db, "pay-api-01", "CVE-2021-44228")

    run = get_runner().start(fid, analyst.id)
    run = _run(db, run.id)
    assert run.status == WorkflowStatus.WAITING_APPROVAL, run.error
    nodes = {e.node_name for e in db.scalars(select(AgentExecution).where(AgentExecution.workflow_run_id == run.id))}
    assert {
        "normalize",
        "correlate_asset",
        "enrich_threat",
        "calculate_risk",
        "plan_remediation",
        "analyze_change_impact",
        "validate_evidence",
    } <= nodes
    assert db.scalar(select(func.count()).select_from(ToolCall).where(ToolCall.workflow_run_id == run.id)) >= 5

    plan = db.get(RemediationPlan, run.plan_id)
    assert plan.target_version == "2.15.0" and plan.status == "ASSESSMENT_COMPLETE"
    assert plan.validation["status"] in ("passed", "needs_expert_validation")
    assert all(not e.get("invalid") for e in plan.evidence_refs)
    finding = db.get(Finding, fid)
    assert finding.risk_score == 100 and finding.priority == "P1"

    req = workflow_ops.request_approval(db, plan.id, analyst, "urgent")
    workflow_ops.decide_approval(db, req.id, approver, "approve", "go")
    run = _run(db, run.id)
    assert run.status == WorkflowStatus.WAITING_EVIDENCE, run.error
    records = list(db.scalars(select(ServiceNowRecord).where(ServiceNowRecord.plan_id == plan.id)))
    assert {r.table_name for r in records} == {"change_request", "change_task"}
    assert all(r.sync_state == "SYNCED" and r.number for r in records)
    assert all(r.record_url is None for r in records)  # simulator never fabricates links

    # Closing the change in ServiceNow alone must NOT verify the finding.
    change = next(r for r in records if r.table_name == "change_request")
    for _ in range(6):
        simulation.advance_change(db, change.id, analyst)
    workflow_ops.refresh_servicenow_status(db, analyst, plan.id)
    db.expire_all()
    assert db.get(Finding, fid).verification_state == "pending_rescan"

    # Rescan before patching -> verification failed, workflow keeps waiting.
    workflow_ops.submit_rescan(db, fid, analyst)
    assert _run(db, run.id).status == WorkflowStatus.WAITING_EVIDENCE
    assert db.get(Finding, fid).verification_state == "verification_failed"

    # Patch the simulated host, rescan -> verified and closed.
    f = db.get(Finding, fid)
    simulation.apply_patch(db, f.reported_device_id, "apache", "log4j", "2.17.1", analyst)
    workflow_ops.submit_rescan(db, fid, analyst)
    run = _run(db, run.id)
    assert run.status == WorkflowStatus.COMPLETED
    f = db.get(Finding, fid)
    assert f.verification_state == "verified_remediated" and f.status == "closed"
    assert run.summary["outcome"] == "verified_remediated"


def test_rejection_prevents_servicenow_write(db) -> None:
    analyst = principal(db, "analyst@northstar.example")
    approver = principal(db, "approver@northstar.example")
    fid = finding_id(db, "mq-broker-01", "CVE-2023-46604")
    run = get_runner().start(fid, analyst.id)
    run = _run(db, run.id)
    plan = db.get(RemediationPlan, run.plan_id)
    assert plan.change_impact["affected_services"] and len(plan.change_impact["affected_services"]) >= 3  # multi-service
    req = workflow_ops.request_approval(db, plan.id, analyst, None)
    workflow_ops.decide_approval(db, req.id, approver, "reject", "Out of maintenance window")
    run = _run(db, run.id)
    assert run.status == WorkflowStatus.REJECTED
    assert db.scalar(select(func.count()).select_from(ServiceNowRecord).where(ServiceNowRecord.plan_id == plan.id)) == 0
    assert _sn_count(db, f"aegis-{req.id}") == 0


def test_sync_failure_retry_is_idempotent(db) -> None:
    analyst = principal(db, "analyst@northstar.example")
    approver = principal(db, "approver@northstar.example")
    admin = principal(db, "admin@northstar.example")
    fid = finding_id(db, "store-app-01", "CVE-2021-44228")
    run = get_runner().start(fid, analyst.id)
    plan = db.get(RemediationPlan, _run(db, run.id).plan_id)
    req = workflow_ops.request_approval(db, plan.id, analyst, None)

    # The remote create succeeds but the response is lost (partial success).
    simulation.set_failure_mode(db, "lost_response", 1, admin)
    workflow_ops.decide_approval(db, req.id, approver, "approve", "ok")
    run = _run(db, run.id)
    assert run.status == WorkflowStatus.WAITING_SYNC_RETRY
    assert _sn_count(db, f"aegis-{req.id}-change") == 1  # it exists remotely already

    workflow_ops.retry_sync(db, req.id, analyst)
    run = _run(db, run.id)
    assert run.status == WorkflowStatus.WAITING_EVIDENCE
    assert _sn_count(db, f"aegis-{req.id}-change") == 1  # adopted, not duplicated
    assert _sn_count(db, f"aegis-{req.id}-task") == 1
    # Repeated sync requests stay idempotent.
    workflow_ops.retry_sync(db, req.id, analyst)
    assert _sn_count(db, f"aegis-{req.id}-change") == 1


def test_auth_failure_then_recovery(db) -> None:
    analyst = principal(db, "analyst@northstar.example")
    approver = principal(db, "approver@northstar.example")
    admin = principal(db, "admin@northstar.example")
    fid = finding_id(db, "pay-api-02", "CVE-2021-44228")
    run = get_runner().start(fid, analyst.id)
    plan = db.get(RemediationPlan, _run(db, run.id).plan_id)
    req = workflow_ops.request_approval(db, plan.id, analyst, None)
    simulation.set_failure_mode(db, "auth_failure", 2, admin)
    workflow_ops.decide_approval(db, req.id, approver, "approve", "ok")
    assert _run(db, run.id).status == WorkflowStatus.WAITING_SYNC_RETRY
    rec = db.scalar(select(ServiceNowRecord).where(ServiceNowRecord.plan_id == plan.id))
    assert rec.sync_state == "SYNC_FAILED" and "401" in rec.last_error
    workflow_ops.retry_sync(db, req.id, analyst)  # consumes the 2nd injected failure
    assert _run(db, run.id).status == WorkflowStatus.WAITING_SYNC_RETRY
    workflow_ops.retry_sync(db, req.id, analyst)
    assert _run(db, run.id).status == WorkflowStatus.WAITING_EVIDENCE
    assert _sn_count(db, f"aegis-{req.id}-change") == 1


def test_ambiguous_asset_requires_manual_review(db) -> None:
    analyst = principal(db, "analyst@northstar.example")
    run = db.scalar(select(WorkflowRun).where(WorkflowRun.status == WorkflowStatus.WAITING_MANUAL_REVIEW))
    assert run is not None
    finding = db.get(Finding, run.finding_id)
    assert finding.correlation_status == "ambiguous" and len(finding.correlation_candidates) == 2
    assert run.plan_id is None  # nothing planned on an unresolved asset
    prod = next(c for c in finding.correlation_candidates if c["environment"] == "production")
    workflow_ops.manual_review(db, run.id, analyst, "asset_resolved", prod["asset_id"], "confirmed with plant team")
    run = _run(db, run.id)
    assert run.status == WorkflowStatus.WAITING_APPROVAL, run.error
    db.expire_all()
    f = db.get(Finding, run.finding_id)
    assert f.asset_id == prod["asset_id"] and f.correlation_status == "matched"


def test_resume_after_restart_uses_durable_checkpoint(db, seeded_db: str) -> None:
    analyst = principal(db, "analyst@northstar.example")
    approver = principal(db, "approver@northstar.example")
    fid = finding_id(db, "order-svc-01", "CVE-2021-44228")
    run = get_runner().start(fid, analyst.id)
    plan_id = _run(db, run.id).plan_id
    # Simulate an application restart: brand-new runner + checkpointer on the same database.
    saver, _ = make_checkpointer(seeded_db)
    set_runner(WorkflowRunner(checkpointer=saver, synchronous=True))
    req = workflow_ops.request_approval(db, plan_id, analyst, None)
    workflow_ops.decide_approval(db, req.id, approver, "approve", "after restart")
    assert _run(db, run.id).status == WorkflowStatus.WAITING_EVIDENCE


def test_duplicate_active_investigation_rejected(db) -> None:
    import pytest

    from app.graphs.runner import WorkflowConflict

    analyst = principal(db, "analyst@northstar.example")
    active = db.scalar(select(WorkflowRun).where(WorkflowRun.status == WorkflowStatus.WAITING_APPROVAL))
    with pytest.raises(WorkflowConflict):
        get_runner().start(active.finding_id, analyst.id)
