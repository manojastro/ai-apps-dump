"""Investigations (workflow runs), agent traces, remediation plans and approvals."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.change_risk import ChangeRiskAnalysisAgent
from app.agents.correlation import AssetCorrelationAgent
from app.agents.intel import ThreatIntelligenceAgent, VulnerabilityIntelligenceAgent
from app.agents.orchestration import RemediationVerificationAgent, ServiceNowOrchestrationAgent
from app.agents.planning import PlanStep, RemediationPlanningAgent
from app.agents.risk import RiskAssessmentAgent
from app.agents.validation import ValidationAgent, validate_plan
from app.api import serializers as ser
from app.api.deps import Page, domain_errors, page_params, paginate
from app.approvals import service as approvals
from app.core.db import SessionLocal, get_db
from app.graphs.investigation import GRAPH_TOPOLOGY
from app.graphs.runner import get_runner
from app.models.enums import PlanStatus, WorkflowStatus
from app.models.remediation import ApprovalRequest, RemediationPlan, RiskAssessment
from app.models.servicenow import ServiceNowRecord
from app.models.vulnerability import Finding
from app.models.workflow import AgentExecution, ToolCall, WorkflowEvent, WorkflowRun
from app.security.auth import Principal, require
from app.security.permissions import Permission
from app.services import workflow_ops
from app.services.audit import record_audit
from app.services.policy_store import get_risk_policy

router = APIRouter(tags=["workflows"])
Reader = Depends(require(Permission.READ))
AGENTS = [
    VulnerabilityIntelligenceAgent,
    AssetCorrelationAgent,
    ThreatIntelligenceAgent,
    RiskAssessmentAgent,
    RemediationPlanningAgent,
    ChangeRiskAnalysisAgent,
    ValidationAgent,
    ServiceNowOrchestrationAgent,
    RemediationVerificationAgent,
]


@router.get("/api/agents")
def list_agents(_: Principal = Reader) -> dict:
    return {"agents": [a.describe() for a in AGENTS], "topology": GRAPH_TOPOLOGY}


@router.get("/api/workflows")
def list_workflows(
    status: str | None = None, page: Page = Depends(page_params), _: Principal = Reader, db: Session = Depends(get_db)
) -> dict:
    q = select(WorkflowRun).order_by(WorkflowRun.started_at.desc())
    if status:
        q = q.where(WorkflowRun.status.in_(status.split(",")))
    return paginate(db, q, page, lambda r: ser.workflow_run(r, db))


def _node_states(db: Session, run: WorkflowRun) -> dict[str, dict[str, Any]]:
    states: dict[str, dict[str, Any]] = {}
    for e in db.scalars(
        select(AgentExecution).where(AgentExecution.workflow_run_id == run.id).order_by(AgentExecution.started_at)
    ):
        prev = states.get(e.node_name, {"attempts": 0})
        states[e.node_name] = {
            "status": e.status,
            "attempts": prev["attempts"] + 1,
            "latency_ms": e.latency_ms,
            "execution_id": e.id,
        }
    visited = {ev.node for ev in db.scalars(select(WorkflowEvent).where(WorkflowEvent.workflow_run_id == run.id)) if ev.node}
    for node in visited - set(states):
        states[node] = {"status": "completed", "attempts": 1}
    if run.current_node and run.status.startswith("waiting"):
        states[run.current_node] = {**states.get(run.current_node, {}), "status": "waiting"}
    if run.current_node and run.status in (WorkflowStatus.BLOCKED, WorkflowStatus.FAILED):
        states[run.current_node] = {**states.get(run.current_node, {}), "status": "failed"}
    return states


@router.get("/api/workflows/{run_id}")
def get_workflow(run_id: str, _: Principal = Reader, db: Session = Depends(get_db)) -> dict:
    run = db.get(WorkflowRun, run_id)
    if run is None:
        raise HTTPException(404, "Workflow run not found")
    execs = list(
        db.scalars(select(AgentExecution).where(AgentExecution.workflow_run_id == run_id).order_by(AgentExecution.started_at))
    )
    tools = list(db.scalars(select(ToolCall).where(ToolCall.workflow_run_id == run_id).order_by(ToolCall.created_at)))
    events = list(db.scalars(select(WorkflowEvent).where(WorkflowEvent.workflow_run_id == run_id).order_by(WorkflowEvent.id)))
    finding = db.get(Finding, run.finding_id)
    risk = db.scalar(
        select(RiskAssessment).where(RiskAssessment.workflow_run_id == run_id).order_by(RiskAssessment.calculated_at.desc())
    )
    plan = db.get(RemediationPlan, run.plan_id) if run.plan_id else None
    approval = None
    if plan:
        req = db.scalar(
            select(ApprovalRequest).where(ApprovalRequest.plan_id == plan.id).order_by(ApprovalRequest.created_at.desc())
        )
        approval = ser.approval(req, db) if req else None
    pending = None
    if run.status.startswith("waiting"):
        try:
            pending = get_runner().pending_interrupt(run_id)
        except Exception:  # checkpoint store unavailable: still render the run
            pending = None
    return {
        "run": ser.workflow_run(run, db),
        "finding": ser.finding_row(finding) if finding else None,
        "asset": ser.asset(finding.asset) if finding else None,
        "correlation_candidates": finding.correlation_candidates if finding else [],
        "executions": [ser.agent_execution(e) for e in execs],
        "tool_calls": [ser.tool_call(t) for t in tools],
        "events": [ser.event(e) for e in events],
        "node_states": _node_states(db, run),
        "risk": ser.risk_assessment(risk),
        "plan": ser.plan(plan, db) if plan else None,
        "approval": approval,
        "pending_interrupt": pending,
        "topology": GRAPH_TOPOLOGY,
    }


@router.get("/api/workflows/{run_id}/events")
def poll_events(run_id: str, after: int = 0, _: Principal = Reader, db: Session = Depends(get_db)) -> dict:
    run = db.get(WorkflowRun, run_id)
    if run is None:
        raise HTTPException(404, "Workflow run not found")
    rows = db.scalars(
        select(WorkflowEvent)
        .where(WorkflowEvent.workflow_run_id == run_id, WorkflowEvent.id > after)
        .order_by(WorkflowEvent.id)
        .limit(500)
    )
    return {"status": run.status, "current_node": run.current_node, "events": [ser.event(e) for e in rows]}


@router.get("/api/workflows/{run_id}/stream")
async def stream_events(run_id: str, request: Request, _: Principal = Reader) -> StreamingResponse:
    """Server-Sent Events backed by the durable event table (survives refreshes and restarts)."""
    last = request.headers.get("last-event-id")
    start_after = int(last) if last and last.isdigit() else int(request.query_params.get("after", "0") or 0)

    def fetch(after: int) -> tuple[str | None, list[dict[str, Any]]]:
        db = SessionLocal()
        try:
            run = db.get(WorkflowRun, run_id)
            if run is None:
                return None, []
            rows = db.scalars(
                select(WorkflowEvent)
                .where(WorkflowEvent.workflow_run_id == run_id, WorkflowEvent.id > after)
                .order_by(WorkflowEvent.id)
                .limit(200)
            )
            return run.status, [ser.event(e) for e in rows]
        finally:
            db.close()

    async def gen():
        after = start_after
        idle = 0
        yield "retry: 3000\n\n"
        while not await request.is_disconnected():
            status, events = await run_in_threadpool(fetch, after)
            if status is None:
                yield 'event: error\ndata: {"error": "not found"}\n\n'
                return
            for e in events:
                after = e["id"]
                yield f"id: {e['id']}\nevent: workflow\ndata: {json.dumps(e)}\n\n"
            yield f"event: status\ndata: {json.dumps({'status': status})}\n\n" if events else ": keepalive\n\n"
            idle = 0 if events else idle + 1
            if status in WorkflowStatus.terminal() and not events:
                return
            await asyncio.sleep(0.7 if idle < 20 else 3)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


class ManualReviewBody(BaseModel):
    action: Literal["asset_resolved", "proceed", "dismiss"]
    asset_id: str | None = Field(default=None, max_length=32)
    note: str | None = Field(default=None, max_length=1000)


@router.post("/api/workflows/{run_id}/manual-review")
def manual_review(
    run_id: str,
    body: ManualReviewBody,
    principal: Principal = Depends(require(Permission.INVESTIGATE)),
    db: Session = Depends(get_db),
) -> dict:
    with domain_errors():
        workflow_ops.manual_review(db, run_id, principal, body.action, body.asset_id, body.note)
    return {"ok": True}


# ------------------------------------------------------------------ remediation plans
@router.get("/api/plans")
def list_plans(
    status: str | None = None, page: Page = Depends(page_params), _: Principal = Reader, db: Session = Depends(get_db)
) -> dict:
    q = select(RemediationPlan).where(RemediationPlan.status != PlanStatus.SUPERSEDED).order_by(RemediationPlan.created_at.desc())
    if status:
        q = q.where(RemediationPlan.status.in_(status.split(",")))
    return paginate(db, q, page, lambda p: ser.plan(p, db, full=False))


@router.get("/api/plans/{plan_id}")
def get_plan(plan_id: str, _: Principal = Reader, db: Session = Depends(get_db)) -> dict:
    plan = db.get(RemediationPlan, plan_id)
    if plan is None:
        raise HTTPException(404, "Plan not found")
    finding = db.get(Finding, plan.finding_id)
    approvals_ = [ser.approval(a, db) for a in plan.approvals]
    records = [ser.sn_record(r) for r in db.scalars(select(ServiceNowRecord).where(ServiceNowRecord.plan_id == plan.id))]
    risk = db.get(RiskAssessment, plan.risk_assessment_id) if plan.risk_assessment_id else None
    return {
        "plan": ser.plan(plan, db),
        "finding": ser.finding_row(finding) if finding else None,
        "vulnerability": ser.vulnerability(finding.vulnerability) if finding else None,
        "asset": ser.asset(finding.asset) if finding else None,
        "risk": ser.risk_assessment(risk),
        "approvals": approvals_,
        "servicenow_records": records,
    }


class PlanUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    summary: str | None = Field(default=None, max_length=2000)
    recommended_action: str | None = Field(default=None, max_length=1500)
    target_version: str | None = Field(default=None, max_length=64)
    prerequisites: list[str] | None = Field(default=None, max_length=12)
    implementation_steps: list[PlanStep] | None = Field(default=None, max_length=15)
    verification_steps: list[str] | None = Field(default=None, max_length=10)
    rollback_steps: list[str] | None = Field(default=None, max_length=10)
    testing_requirements: list[str] | None = Field(default=None, max_length=10)
    expected_impact: str | None = Field(default=None, max_length=1500)
    maintenance_window: str | None = Field(default=None, max_length=500)
    edit_reason: str = Field(min_length=3, max_length=500)


@router.patch("/api/plans/{plan_id}")
def update_plan(
    plan_id: str, body: PlanUpdate, principal: Principal = Depends(require(Permission.PLAN_EDIT)), db: Session = Depends(get_db)
) -> dict:
    plan = db.get(RemediationPlan, plan_id)
    if plan is None:
        raise HTTPException(404, "Plan not found")
    if plan.status in (PlanStatus.REJECTED, PlanStatus.SUPERSEDED):
        raise HTTPException(409, f"Plan is {plan.status}; start a new investigation instead")
    changes = body.model_dump(exclude_unset=True, exclude={"edit_reason"})
    if "implementation_steps" in changes:
        changes["implementation_steps"] = [s if isinstance(s, dict) else s.model_dump() for s in changes["implementation_steps"]]
    before_hash = approvals.compute_plan_hash(plan)
    before = {k: getattr(plan, k) for k in changes}
    for k, v in changes.items():
        setattr(plan, k, v)
    after_hash = approvals.compute_plan_hash(plan)
    if after_hash == before_hash:
        db.rollback()
        return {"plan": ser.plan(plan, db), "changed": False}
    with domain_errors():
        invalidated = approvals.invalidate_for_plan_change(db, plan, principal, body.edit_reason)
    plan.content_hash = after_hash
    plan.revision += 1
    plan.edited_by = principal.id
    plan.generated_by = f"{plan.generated_by.split(' + ')[0]} + analyst-edit"
    finding = db.get(Finding, plan.finding_id)
    assert finding is not None
    coverage = None
    if plan.risk_assessment_id and (ra := db.get(RiskAssessment, plan.risk_assessment_id)):
        coverage = ra.coverage
    result = validate_plan(plan, finding, coverage, get_risk_policy(db).min_coverage_for_auto_routing)
    plan.validation = result.model_dump(mode="json")
    plan.status = PlanStatus.DRAFT if result.route == "manual_review" else PlanStatus.ASSESSMENT_COMPLETE
    record_audit(
        db,
        actor=principal,
        action="plan_edited",
        target_type="remediation_plan",
        target_id=plan.id,
        previous_state={"hash": before_hash, **{k: str(v)[:300] for k, v in before.items()}},
        new_state={"hash": after_hash, "revision": plan.revision},
        details={"reason": body.edit_reason, "approvals_invalidated": invalidated, "validation": result.status},
    )
    db.commit()
    return {"plan": ser.plan(plan, db), "changed": True, "approvals_invalidated": invalidated}


class ApprovalRequestBody(BaseModel):
    comment: str | None = Field(default=None, max_length=2000)
    assigned_approver_id: str | None = Field(default=None, max_length=36)


@router.post("/api/plans/{plan_id}/request-approval")
def request_approval(
    plan_id: str,
    body: ApprovalRequestBody,
    principal: Principal = Depends(require(Permission.APPROVAL_REQUEST)),
    db: Session = Depends(get_db),
) -> dict:
    with domain_errors():
        req = workflow_ops.request_approval(db, plan_id, principal, body.comment, body.assigned_approver_id)
    return ser.approval(req, db)


@router.post("/api/plans/{plan_id}/refresh-status")
def refresh_plan_status(
    plan_id: str, principal: Principal = Depends(require(Permission.SERVICENOW_SYNC)), db: Session = Depends(get_db)
) -> dict:
    records = workflow_ops.refresh_servicenow_status(db, principal, plan_id)
    return {"records": [ser.sn_record(r) for r in records]}


@router.get("/api/plans/{plan_id}/export", response_class=PlainTextResponse)
def export_plan(plan_id: str, principal: Principal = Reader, db: Session = Depends(get_db)) -> PlainTextResponse:
    plan = db.get(RemediationPlan, plan_id)
    if plan is None:
        raise HTTPException(404, "Plan not found")
    p = ser.plan(plan, db)
    lines = [
        f"# {p['title']}",
        "",
        f"- Plan ID: {p['id']} (revision {p['revision']}, {p['status']})",
        f"- CVE: {p['cve_id']} | Asset: {p['hostname']} | Risk: {p['risk_score']} {p['risk_level']} {p['priority']}",
        f"- Generated by: {p['generated_by']} | Content hash: {p['content_hash']}",
        f"- Requires expert validation: {p['requires_expert_validation']}",
        "",
        "## Summary",
        p["summary"],
        "",
        "## Recommended action",
        p["recommended_action"],
        "",
        "## Prerequisites",
        *[f"- {x}" for x in p["prerequisites"]],
        "",
        "## Implementation steps",
        *[f"{i}. {s['step']} [{', '.join(s.get('evidence_refs', []))}]" for i, s in enumerate(p["implementation_steps"], 1)],
        "",
        "## Verification",
        *[f"- {x}" for x in p["verification_steps"]],
        "",
        "## Rollback (proposed, unverified)",
        *[f"- {x}" for x in p["rollback_steps"]],
        "",
        "## Testing",
        *[f"- {x}" for x in p["testing_requirements"]],
        "",
        "## Expected impact",
        p["expected_impact"],
        "",
        "## Maintenance window",
        p["maintenance_window"],
        "",
        "## Change impact",
        (p["change_impact"] or {}).get("summary", "n/a"),
        "",
        "## Evidence",
        *[f"- {e['id']} ({e.get('type')}): {e.get('title')} - source: {e.get('source')}" for e in p["evidence_refs"]],
        "",
        "## Validation",
        f"Status: {(p['validation'] or {}).get('status')}",
        *[f"- [{i['severity']}] {i['code']}: {i['message']}" for i in (p["validation"] or {}).get("issues", [])],
        "",
        "_Exported from AegisRemediate AI. Proposal only - no remediation was executed by the platform._",
    ]
    record_audit(db, actor=principal, action="plan_exported", target_type="remediation_plan", target_id=plan.id)
    db.commit()
    return PlainTextResponse("\n".join(lines), headers={"Content-Disposition": f"attachment; filename=plan-{plan.id[:8]}.md"})


# ------------------------------------------------------------------ approvals
@router.get("/api/approvals")
def list_approvals(
    state: str | None = None, page: Page = Depends(page_params), _: Principal = Reader, db: Session = Depends(get_db)
) -> dict:
    q = select(ApprovalRequest).order_by(ApprovalRequest.created_at.desc())
    if state:
        q = q.where(ApprovalRequest.state.in_(state.split(",")))

    def row(a: ApprovalRequest) -> dict[str, Any]:
        plan = db.get(RemediationPlan, a.plan_id)
        return ser.approval(a, db) | {"plan": ser.plan(plan, db, full=False) if plan else None}

    return paginate(db, q, page, row)


@router.get("/api/approvals/{approval_id}")
def get_approval(approval_id: str, _: Principal = Reader, db: Session = Depends(get_db)) -> dict:
    a = db.get(ApprovalRequest, approval_id)
    if a is None:
        raise HTTPException(404, "Approval request not found")
    plan = db.get(RemediationPlan, a.plan_id)
    return ser.approval(a, db) | {"plan": ser.plan(plan, db) if plan else None}


class DecisionBody(BaseModel):
    decision: Literal["approve", "reject", "request_changes"]
    comment: str | None = Field(default=None, max_length=2000)
    confirm: bool = Field(description="Explicit confirmation from the approver UI")


@router.post("/api/approvals/{approval_id}/decision")
def decide(
    approval_id: str, body: DecisionBody, principal: Principal = Depends(require(Permission.READ)), db: Session = Depends(get_db)
) -> dict:
    # Permission is enforced inside the approval engine so denied attempts are recorded in history.
    if not body.confirm:
        raise HTTPException(422, "Decision must be explicitly confirmed")
    with domain_errors():
        req = workflow_ops.decide_approval(db, approval_id, principal, body.decision, body.comment)
    return ser.approval(req, db)


@router.post("/api/approvals/{approval_id}/cancel")
def cancel(
    approval_id: str, principal: Principal = Depends(require(Permission.APPROVAL_REQUEST)), db: Session = Depends(get_db)
) -> dict:
    with domain_errors():
        req = approvals.cancel_request(db, approval_id, principal)
    db.commit()
    return ser.approval(req, db)


@router.post("/api/approvals/{approval_id}/retry-sync")
def retry_sync(
    approval_id: str, principal: Principal = Depends(require(Permission.SERVICENOW_SYNC)), db: Session = Depends(get_db)
) -> dict:
    with domain_errors():
        return workflow_ops.retry_sync(db, approval_id, principal)
