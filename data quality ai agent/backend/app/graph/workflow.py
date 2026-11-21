from typing import Any

from langgraph.graph import END, START, StateGraph

from app.adapters.local import LocalSimulatorAdapter
from app.graph.nodes.gates import GateNodes
from app.graph.nodes.investigation import InvestigationNodes
from app.graph.nodes.remediation import RemediationNodes
from app.graph.runtime import Runtime, no_events
from app.graph.state import RecoveryState
from app.llm.providers import DeterministicProvider
from app.models.domain import Incident, Risk, Status
from app.rag.local import LocalKnowledge
from app.security.policy import BRANCHES
from app.validators.engine import all_passed
from app.verifier.independent import IndependentVerifier


def initial_state(
    incident: Incident, max_attempts: int = 3, force_first_fail: bool = False
) -> RecoveryState:
    return {
        "incident_id": incident.id,
        "incident": incident,
        "evidence": [],
        "evidence_round": 0,
        "attempt_history": [],
        "attempt_number": 0,
        "max_attempts": incident.max_attempts or max_attempts,
        "force_first_fail": force_first_fail
        if incident.demo_force_first_fix_fail is None
        else incident.demo_force_first_fix_fail,
        "validation_feedback": [],
        "approval_status": "NOT_REQUIRED",
        "final_status": Status.RUNNING,
        "latency_metrics": [],
        "audit_events": [],
        "cost_metrics": {
            "llm_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0,
        },
    }


def after_validation(state: RecoveryState) -> str:
    if all_passed(state["validation_results"]):
        return "independent_verifier"
    return "remediation_planner" if state["attempt_number"] < state["max_attempts"] else "failed"


def confidence_route(state: RecoveryState) -> str:
    if state["confidence"] >= 0.75:
        return "remediation_planner"
    return "more_evidence" if state["evidence_round"] < 1 else "insufficient_evidence"


def verification_route(state: RecoveryState) -> str:
    verdict = state["verification_result"].decision
    if verdict == "REJECT":
        return "rejected"
    if verdict == "NEEDS_HUMAN" or state["risk_level"] in (Risk.MEDIUM, Risk.HIGH):
        return "human_approval"
    return "artifact"


def build_graph(
    checkpointer: Any,
    adapter=None,
    provider=None,
    verifier=None,
    knowledge=None,
    event=no_events,
    runtime: Runtime | None = None,
):
    local = adapter or LocalSimulatorAdapter()
    runtime = runtime or Runtime(
        local,
        local,
        local,
        knowledge or LocalKnowledge(),
        provider or DeterministicProvider(),
        verifier or IndependentVerifier(),
        event,
    )
    investigation, remediation, gates = (
        InvestigationNodes(runtime),
        RemediationNodes(runtime),
        GateNodes(runtime),
    )
    graph = StateGraph(RecoveryState)
    nodes = {
        "incident_intake": investigation.intake,
        "context_retrieval": investigation.context,
        "evidence_aggregator": investigation.aggregate,
        "root_cause_synthesis": investigation.diagnose,
        "more_evidence": investigation.more_evidence,
        "remediation_planner": remediation.plan,
        "risk_gate": remediation.risk,
        "sandbox_apply": remediation.sandbox,
        "pipeline_replay": remediation.replay,
        "deterministic_validation": remediation.validate,
        "independent_verifier": gates.verify,
        "human_approval": gates.approval,
        "insufficient_evidence": gates.insufficient,
        "artifact": gates.artifact,
        "failed": gates.failed,
        "rejected": gates.rejected,
    }
    for branch in BRANCHES:
        nodes[f"{branch}_investigator"] = investigation.branch(branch)
    for name, action in nodes.items():
        graph.add_node(name, runtime.node(name, action))
    graph.add_edge(START, "incident_intake")
    graph.add_edge("incident_intake", "context_retrieval")
    branches = [f"{branch}_investigator" for branch in BRANCHES]
    for branch in branches:
        graph.add_edge("context_retrieval", branch)
        graph.add_edge("more_evidence", branch)
    graph.add_edge(branches, "evidence_aggregator")
    graph.add_edge("evidence_aggregator", "root_cause_synthesis")
    graph.add_conditional_edges(
        "root_cause_synthesis",
        confidence_route,
        ["remediation_planner", "more_evidence", "insufficient_evidence"],
    )
    graph.add_edge("remediation_planner", "risk_gate")
    graph.add_conditional_edges(
        "risk_gate",
        lambda s: "failed" if s["risk_level"] == Risk.CRITICAL else "sandbox_apply",
        ["failed", "sandbox_apply"],
    )
    graph.add_edge("sandbox_apply", "pipeline_replay")
    graph.add_edge("pipeline_replay", "deterministic_validation")
    graph.add_conditional_edges(
        "deterministic_validation",
        after_validation,
        ["independent_verifier", "remediation_planner", "failed"],
    )
    graph.add_conditional_edges(
        "independent_verifier", verification_route, ["human_approval", "artifact", "rejected"]
    )
    graph.add_conditional_edges(
        "human_approval",
        lambda s: "artifact" if s["approval_status"] == "APPROVED" else "rejected",
        ["artifact", "rejected"],
    )
    for node in ("artifact", "failed", "rejected", "insufficient_evidence"):
        graph.add_edge(node, END)
    return graph.compile(checkpointer=checkpointer)
