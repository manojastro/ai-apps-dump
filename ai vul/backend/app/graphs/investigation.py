"""LangGraph investigation workflow.

START -> ingest -> normalize -> correlate_asset -> enrich_threat -> calculate_risk
      -> plan_remediation -> analyze_change_impact -> validate_evidence
         -> (insufficient) manual_review --(asset resolved)--> correlate_asset
                                         --(proceed)--------> human_approval
                                         --(dismiss)--------> final_report
         -> human_approval  (interrupt until a human decides)
              -> rejected: record_rejection -> END
              -> approved: servicenow_write_gate -> sync_servicenow
                     -> failed: await_sync_retry (interrupt) -> servicenow_write_gate
                     -> synced: await_evidence (interrupt until new scan evidence)
                                -> verify_remediation -> verified: final_report -> END
                                                      -> otherwise: await_evidence

Every node persists its own effects; the graph state carries only identifiers and compact
summaries, checkpointed after each step so runs survive restarts and long approval delays.
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy, interrupt
from sqlalchemy import select

from app.agents.base import emit_event, execute_agent
from app.agents.change_risk import ChangeRiskAnalysisAgent
from app.agents.correlation import AssetCorrelationAgent
from app.agents.intel import ThreatIntelligenceAgent, VulnerabilityIntelligenceAgent
from app.agents.orchestration import RemediationVerificationAgent, ServiceNowOrchestrationAgent
from app.agents.planning import RemediationPlanningAgent
from app.agents.risk import RiskAssessmentAgent
from app.agents.validation import ValidationAgent
from app.approvals.write_gate import authorize_write
from app.core.db import session_scope
from app.core.types import utcnow
from app.integrations.servicenow.factory import write_allowlist
from app.llm.base import LLMProvider
from app.models.enums import ApprovalState, FindingStatus, PlanStatus, VerificationState, WorkflowStatus
from app.models.remediation import ApprovalRequest, RemediationPlan
from app.models.vulnerability import Finding
from app.models.workflow import WorkflowRun
from app.security.auth import SYSTEM_PRINCIPAL
from app.services.audit import record_audit


class InvestigationState(TypedDict, total=False):
    run_id: str
    finding_id: str
    started_by: str | None
    vuln_intel: dict[str, Any] | None
    asset_context: dict[str, Any] | None
    threat_intel: dict[str, Any] | None
    risk: dict[str, Any] | None
    plan_id: str | None
    change_impact: dict[str, Any] | None
    validation: dict[str, Any] | None
    manual_review: dict[str, Any] | None
    approval_request_id: str | None
    approval_decision: str | None
    gate: dict[str, Any] | None
    servicenow: dict[str, Any] | None
    verification: dict[str, Any] | None
    route: str | None
    report: dict[str, Any] | None


NODE_ORDER = [
    "ingest",
    "normalize",
    "correlate_asset",
    "enrich_threat",
    "calculate_risk",
    "plan_remediation",
    "analyze_change_impact",
    "validate_evidence",
    "manual_review",
    "human_approval",
    "record_rejection",
    "servicenow_write_gate",
    "sync_servicenow",
    "await_sync_retry",
    "await_evidence",
    "verify_remediation",
    "final_report",
]

AGENT_RETRY = RetryPolicy(max_attempts=3, initial_interval=0.5, backoff_factor=2.0, jitter=True)


def _set_status(run_id: str, status: str, node: str, reason: str | None = None, **extra: Any) -> None:
    with session_scope() as db:
        run = db.get(WorkflowRun, run_id)
        if run is None:
            return
        run.status, run.current_node, run.waiting_reason = status, node, reason
        for k, v in extra.items():
            setattr(run, k, v)
        if status in WorkflowStatus.terminal():
            run.completed_at = utcnow()
        emit_event(db, run_id, "status", reason or f"Workflow {status}", node, {"status": status})


def build_graph(provider: LLMProvider | None = None) -> StateGraph:
    def agent_node(agent_cls: type, key: str):
        agent = agent_cls()

        def _node(state: InvestigationState) -> dict[str, Any]:
            return {key: execute_agent(agent, state["run_id"], dict(state), provider)}

        _node.__name__ = agent.node
        return _node

    def ingest(state: InvestigationState) -> dict[str, Any]:
        with session_scope() as db:
            finding = db.get(Finding, state["finding_id"])
            if finding is None:
                raise ValueError("finding not found")
            emit_event(
                db,
                state["run_id"],
                "ingested",
                f"Finding loaded: {finding.vulnerability.cve_id} on "
                f"{finding.reported_asset_identifier} (scanner {finding.scanner})",
                "ingest",
                {"scanner_finding_id": finding.scanner_finding_id},
            )
            run = db.get(WorkflowRun, state["run_id"])
            if run:
                run.status, run.current_node = WorkflowStatus.RUNNING, "ingest"
        return {"route": None}

    def plan_node(state: InvestigationState) -> dict[str, Any]:
        out = execute_agent(RemediationPlanningAgent(), state["run_id"], dict(state), provider)
        with session_scope() as db:
            run = db.get(WorkflowRun, state["run_id"])
            if run:
                run.plan_id = out["plan_id"]
        return {"plan_id": out["plan_id"]}

    def validate_node(state: InvestigationState) -> dict[str, Any]:
        out = execute_agent(ValidationAgent(), state["run_id"], dict(state), provider)
        return {"validation": out, "route": out["route"]}

    def correlate_node(state: InvestigationState) -> dict[str, Any]:
        out = execute_agent(AssetCorrelationAgent(), state["run_id"], dict(state), provider)
        return {"asset_context": out, "route": "manual_review" if out["requires_human_review"] else None}

    def manual_review(state: InvestigationState) -> dict[str, Any]:
        issues = (state.get("validation") or {}).get("issues", [])
        reason = (
            "Asset match is ambiguous: an analyst must confirm the CMDB record"
            if (state.get("asset_context") or {}).get("requires_human_review") and not state.get("plan_id")
            else "Evidence insufficient: " + "; ".join(i["message"] for i in issues if i.get("blocking"))[:400]
        )
        _set_status(state["run_id"], WorkflowStatus.WAITING_MANUAL_REVIEW, "manual_review", reason)
        decision = interrupt(
            {"type": "manual_review", "reason": reason, "candidates": (state.get("asset_context") or {}).get("candidates", [])}
        )
        decision = decision if isinstance(decision, dict) else {"action": str(decision)}
        with session_scope() as db:
            emit_event(
                db,
                state["run_id"],
                "human_input",
                f"Manual review decision: {decision.get('action')}",
                "manual_review",
                {k: v for k, v in decision.items() if k != "actor_id"},
            )
        return {"manual_review": decision, "route": decision.get("action")}

    def route_after_correlate(state: InvestigationState) -> str:
        return "manual_review" if state.get("route") == "manual_review" else "enrich_threat"

    def route_after_validation(state: InvestigationState) -> str:
        return "manual_review" if state.get("route") == "manual_review" else "human_approval"

    def route_after_manual(state: InvestigationState) -> str:
        action = state.get("route")
        if action == "asset_resolved":
            return "correlate_asset"
        if action == "dismiss":
            return "final_report"
        if action == "proceed" and state.get("plan_id"):
            return "human_approval"
        if action == "proceed":
            return "enrich_threat"
        return "manual_review"

    def human_approval(state: InvestigationState) -> dict[str, Any]:
        _set_status(
            state["run_id"],
            WorkflowStatus.WAITING_APPROVAL,
            "human_approval",
            "Awaiting human approval (request it from the remediation plan)",
        )
        resume = interrupt({"type": "approval", "plan_id": state.get("plan_id")})
        approval_id = resume.get("approval_request_id") if isinstance(resume, dict) else None
        # Never trust the resume payload: re-read the decision from the database.
        with session_scope() as db:
            req = db.get(ApprovalRequest, approval_id) if approval_id else None
            if req is None or req.plan_id != state.get("plan_id"):
                req = db.scalar(
                    select(ApprovalRequest)
                    .where(ApprovalRequest.plan_id == state.get("plan_id"))
                    .order_by(ApprovalRequest.created_at.desc())
                )
            decision = req.state if req else None
            emit_event(
                db,
                state["run_id"],
                "human_input",
                f"Approval decision recorded: {decision}",
                "human_approval",
                {"approval_request_id": req.id if req else None},
            )
        return {"approval_request_id": req.id if req else None, "approval_decision": decision}

    def route_after_approval(state: InvestigationState) -> str:
        if state.get("approval_decision") == ApprovalState.APPROVED:
            return "servicenow_write_gate"
        if state.get("approval_decision") == ApprovalState.REJECTED:
            return "record_rejection"
        return "human_approval"  # changes requested / invalidated / spurious resume -> wait again

    def record_rejection(state: InvestigationState) -> dict[str, Any]:
        with session_scope() as db:
            req = db.get(ApprovalRequest, state.get("approval_request_id"))
            emit_event(
                db,
                state["run_id"],
                "rejected",
                "Plan rejected by approver; no ServiceNow write performed",
                "record_rejection",
                {"comment": req.decision_comment if req else None},
            )
            record_audit(
                db,
                actor=SYSTEM_PRINCIPAL,
                action="workflow_rejected",
                target_type="workflow_run",
                target_id=state["run_id"],
                details={"approval_request_id": state.get("approval_request_id")},
            )
        _set_status(state["run_id"], WorkflowStatus.REJECTED, "record_rejection", "Rejected by approver")
        return {"report": {"outcome": "rejected"}}

    def write_gate(state: InvestigationState) -> dict[str, Any]:
        with session_scope() as db:
            tables = write_allowlist()
            decision = authorize_write(db, state["approval_request_id"] or "", tables, SYSTEM_PRINCIPAL)
            emit_event(
                db,
                state["run_id"],
                "gate",
                "ServiceNow write gate " + ("PASSED" if decision.allowed else "DENIED"),
                "servicenow_write_gate",
                {"checks": decision.checks, "reasons": decision.reasons},
            )
        if not decision.allowed:
            _set_status(
                state["run_id"],
                WorkflowStatus.BLOCKED,
                "servicenow_write_gate",
                "Write gate denied: " + "; ".join(decision.reasons),
            )
        return {"gate": {"allowed": decision.allowed, "checks": decision.checks, "reasons": decision.reasons}}

    def route_after_gate(state: InvestigationState) -> str:
        return "sync_servicenow" if (state.get("gate") or {}).get("allowed") else END

    def sync_node(state: InvestigationState) -> dict[str, Any]:
        out = execute_agent(ServiceNowOrchestrationAgent(), state["run_id"], dict(state), provider)
        return {"servicenow": out}

    def route_after_sync(state: InvestigationState) -> str:
        status = (state.get("servicenow") or {}).get("status")
        if status == "synced":
            return "await_evidence"
        if status == "denied":
            return END
        return "await_sync_retry"

    def await_sync_retry(state: InvestigationState) -> dict[str, Any]:
        err = (state.get("servicenow") or {}).get("error")
        _set_status(
            state["run_id"],
            WorkflowStatus.WAITING_SYNC_RETRY,
            "await_sync_retry",
            f"ServiceNow synchronisation failed: {err}. Retry when the integration is healthy.",
        )
        interrupt({"type": "sync_retry", "error": err})
        return {"servicenow": None}

    def await_evidence(state: InvestigationState) -> dict[str, Any]:
        with session_scope() as db:
            finding = db.get(Finding, state["finding_id"])
            if finding and finding.status == FindingStatus.OPEN:
                finding.status = FindingStatus.IN_REMEDIATION
            if finding and finding.verification_state == VerificationState.NOT_STARTED:
                finding.verification_state = VerificationState.PENDING_RESCAN
        _set_status(
            state["run_id"],
            WorkflowStatus.WAITING_EVIDENCE,
            "await_evidence",
            "Remediation tracked in ServiceNow; awaiting new scan evidence for verification",
        )
        interrupt({"type": "evidence"})
        with session_scope() as db:
            finding = db.get(Finding, state["finding_id"])
            if finding:
                finding.verification_state = VerificationState.IN_PROGRESS
        return {}

    def verify_node(state: InvestigationState) -> dict[str, Any]:
        out = execute_agent(RemediationVerificationAgent(), state["run_id"], dict(state), provider)
        return {"verification": out}

    def route_after_verify(state: InvestigationState) -> str:
        return (
            "final_report"
            if (state.get("verification") or {}).get("verification_state") == VerificationState.VERIFIED_REMEDIATED
            else "await_evidence"
        )

    def final_report(state: InvestigationState) -> dict[str, Any]:
        dismissed = (state.get("manual_review") or {}).get("action") == "dismiss"
        with session_scope() as db:
            finding = db.get(Finding, state["finding_id"])
            plan = db.get(RemediationPlan, state["plan_id"]) if state.get("plan_id") else None
            if finding and not dismissed and finding.verification_state == VerificationState.VERIFIED_REMEDIATED:
                finding.status = FindingStatus.CLOSED
            report = {
                "outcome": "dismissed" if dismissed else "verified_remediated",
                "cve_id": finding.vulnerability.cve_id if finding else None,
                "asset": (state.get("asset_context") or {}).get("hostname"),
                "risk": {k: (state.get("risk") or {}).get(k) for k in ("risk_score", "risk_level", "priority")},
                "plan_id": plan.id if plan else None,
                "servicenow": (state.get("servicenow") or {}).get("records"),
                "verification": state.get("verification"),
                "closed_at": utcnow().isoformat(),
            }
            run = db.get(WorkflowRun, state["run_id"])
            if run:
                run.summary = report
            if plan and plan.status not in (PlanStatus.REJECTED,) and not dismissed:
                record_audit(
                    db,
                    actor=SYSTEM_PRINCIPAL,
                    action="finding_closed_with_evidence",
                    target_type="finding",
                    target_id=state["finding_id"],
                    details={"plan_id": plan.id},
                )
        _set_status(
            state["run_id"],
            WorkflowStatus.COMPLETED,
            "final_report",
            "Closed: remediation verified with scan evidence" if not dismissed else "Dismissed by analyst",
        )
        return {"report": report}

    g = StateGraph(InvestigationState)
    g.add_node("ingest", ingest)
    g.add_node("normalize", agent_node(VulnerabilityIntelligenceAgent, "vuln_intel"), retry_policy=AGENT_RETRY)
    g.add_node("correlate_asset", correlate_node, retry_policy=AGENT_RETRY)
    g.add_node("enrich_threat", agent_node(ThreatIntelligenceAgent, "threat_intel"), retry_policy=AGENT_RETRY)
    g.add_node("calculate_risk", agent_node(RiskAssessmentAgent, "risk"), retry_policy=AGENT_RETRY)
    g.add_node("plan_remediation", plan_node, retry_policy=AGENT_RETRY)
    g.add_node("analyze_change_impact", agent_node(ChangeRiskAnalysisAgent, "change_impact"), retry_policy=AGENT_RETRY)
    g.add_node("validate_evidence", validate_node)
    g.add_node("manual_review", manual_review)
    g.add_node("human_approval", human_approval)
    g.add_node("record_rejection", record_rejection)
    g.add_node("servicenow_write_gate", write_gate)
    g.add_node("sync_servicenow", sync_node)
    g.add_node("await_sync_retry", await_sync_retry)
    g.add_node("await_evidence", await_evidence)
    g.add_node("verify_remediation", verify_node, retry_policy=AGENT_RETRY)
    g.add_node("final_report", final_report)

    g.add_edge(START, "ingest")
    g.add_edge("ingest", "normalize")
    g.add_edge("normalize", "correlate_asset")
    g.add_conditional_edges("correlate_asset", route_after_correlate, ["manual_review", "enrich_threat"])
    g.add_edge("enrich_threat", "calculate_risk")
    g.add_edge("calculate_risk", "plan_remediation")
    g.add_edge("plan_remediation", "analyze_change_impact")
    g.add_edge("analyze_change_impact", "validate_evidence")
    g.add_conditional_edges("validate_evidence", route_after_validation, ["manual_review", "human_approval"])
    g.add_conditional_edges(
        "manual_review",
        route_after_manual,
        ["correlate_asset", "final_report", "human_approval", "enrich_threat", "manual_review"],
    )
    g.add_conditional_edges(
        "human_approval", route_after_approval, ["servicenow_write_gate", "record_rejection", "human_approval"]
    )
    g.add_edge("record_rejection", END)
    g.add_conditional_edges("servicenow_write_gate", route_after_gate, ["sync_servicenow", END])
    g.add_conditional_edges("sync_servicenow", route_after_sync, ["await_evidence", "await_sync_retry", END])
    g.add_edge("await_sync_retry", "servicenow_write_gate")
    g.add_edge("await_evidence", "verify_remediation")
    g.add_conditional_edges("verify_remediation", route_after_verify, ["final_report", "await_evidence"])
    g.add_edge("final_report", END)
    return g


GRAPH_TOPOLOGY = {
    "nodes": [
        {"id": "ingest", "label": "Ingest Finding", "agent": None, "kind": "system"},
        {"id": "normalize", "label": "Vulnerability Intelligence", "agent": VulnerabilityIntelligenceAgent.name, "kind": "agent"},
        {"id": "correlate_asset", "label": "Asset Correlation", "agent": AssetCorrelationAgent.name, "kind": "agent"},
        {"id": "enrich_threat", "label": "Threat Intelligence", "agent": ThreatIntelligenceAgent.name, "kind": "agent"},
        {"id": "calculate_risk", "label": "Risk Assessment", "agent": RiskAssessmentAgent.name, "kind": "agent"},
        {"id": "plan_remediation", "label": "Remediation Planning", "agent": RemediationPlanningAgent.name, "kind": "agent"},
        {"id": "analyze_change_impact", "label": "Change Risk Analysis", "agent": ChangeRiskAnalysisAgent.name, "kind": "agent"},
        {"id": "validate_evidence", "label": "Evidence Validation", "agent": ValidationAgent.name, "kind": "agent"},
        {"id": "manual_review", "label": "Manual Review", "agent": None, "kind": "human"},
        {"id": "human_approval", "label": "Human Approval Gate", "agent": None, "kind": "human"},
        {"id": "record_rejection", "label": "Record Rejection", "agent": None, "kind": "system"},
        {"id": "servicenow_write_gate", "label": "ServiceNow Write Gate", "agent": None, "kind": "gate"},
        {
            "id": "sync_servicenow",
            "label": "ServiceNow Orchestration",
            "agent": ServiceNowOrchestrationAgent.name,
            "kind": "agent",
        },
        {"id": "await_sync_retry", "label": "Await Sync Retry", "agent": None, "kind": "human"},
        {"id": "await_evidence", "label": "Track Remediation", "agent": None, "kind": "human"},
        {
            "id": "verify_remediation",
            "label": "Remediation Verification",
            "agent": RemediationVerificationAgent.name,
            "kind": "agent",
        },
        {"id": "final_report", "label": "Evidence-based Closure", "agent": None, "kind": "system"},
    ],
    "edges": [
        ["ingest", "normalize", ""],
        ["normalize", "correlate_asset", ""],
        ["correlate_asset", "enrich_threat", "matched"],
        ["correlate_asset", "manual_review", "ambiguous"],
        ["enrich_threat", "calculate_risk", ""],
        ["calculate_risk", "plan_remediation", ""],
        ["plan_remediation", "analyze_change_impact", ""],
        ["analyze_change_impact", "validate_evidence", ""],
        ["validate_evidence", "human_approval", "sufficient"],
        ["validate_evidence", "manual_review", "insufficient"],
        ["manual_review", "correlate_asset", "asset resolved"],
        ["manual_review", "human_approval", "proceed"],
        ["manual_review", "final_report", "dismiss"],
        ["human_approval", "servicenow_write_gate", "approved"],
        ["human_approval", "record_rejection", "rejected"],
        ["servicenow_write_gate", "sync_servicenow", "allowed"],
        ["sync_servicenow", "await_evidence", "synced"],
        ["sync_servicenow", "await_sync_retry", "failed"],
        ["await_sync_retry", "servicenow_write_gate", "retry"],
        ["await_evidence", "verify_remediation", "new evidence"],
        ["verify_remediation", "await_evidence", "not verified"],
        ["verify_remediation", "final_report", "verified"],
    ],
}
