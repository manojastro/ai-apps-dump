from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.catalog import get_runbook, get_scenario
from app.repository import Repository, new_id, utcnow
from app.schemas import IncidentStatus, WorkflowState
from services.policy import PolicyEngine
from services.tools.sandbox import Sandbox

from .model import DiagnosticModel


class RemediationWorkflow:
    """Auditable LangGraph workflow with policy and execution outside the model."""

    NODE_ORDER = [
        "ingest_incident", "collect_evidence", "retrieve_runbooks", "generate_candidate_hypotheses",
        "choose_remediation_candidate", "validate_parameters", "classify_risk", "policy_engine",
        "approval_checkpoint", "execute_allowlisted_tool", "verify", "rollback", "close_or_escalate",
    ]

    def __init__(self, repository: Repository, policy: PolicyEngine, sandbox: Sandbox, model: DiagnosticModel):
        self.repository = repository
        self.policy = policy
        self.sandbox = sandbox
        self.model = model
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(WorkflowState)
        graph.add_node("ingest_incident", self._ingest)
        graph.add_node("collect_evidence", self._collect)
        graph.add_node("retrieve_runbooks", self._retrieve)
        graph.add_node("generate_candidate_hypotheses", self._hypotheses)
        graph.add_node("choose_remediation_candidate", self._choose)
        graph.add_node("validate_parameters", self._validate)
        graph.add_node("classify_risk", self._classify)
        graph.add_node("policy_engine", self._policy)
        graph.add_node("approval_checkpoint", self._approval)
        graph.add_node("execute_allowlisted_tool", self._execute)
        graph.add_node("verify", self._verify)
        graph.add_node("rollback", self._rollback)
        graph.add_node("close_or_escalate", self._close)
        graph.add_edge(START, "ingest_incident")
        for left, right in zip(self.NODE_ORDER[0:7], self.NODE_ORDER[1:8]):
            graph.add_edge(left, right)
        graph.add_conditional_edges("policy_engine", self._after_policy,
                                    {"approval": "approval_checkpoint", "execute": "execute_allowlisted_tool", "close": "close_or_escalate"})
        graph.add_conditional_edges("approval_checkpoint", self._after_approval,
                                    {"execute": "execute_allowlisted_tool", "close": "close_or_escalate", "wait": END})
        graph.add_conditional_edges("execute_allowlisted_tool", self._after_execute,
                                    {"verify": "verify", "close": "close_or_escalate"})
        graph.add_conditional_edges("verify", lambda state: "close" if state["verification"]["healthy"] else "rollback",
                                    {"close": "close_or_escalate", "rollback": "rollback"})
        graph.add_edge("rollback", "close_or_escalate")
        graph.add_edge("close_or_escalate", END)
        return graph.compile()

    def run(self, incident_id: str) -> dict[str, Any]:
        incident = self.repository.get_incident(incident_id)
        if incident["status"] in {"RESOLVED", "ROLLED_BACK", "BLOCKED", "REJECTED", "ESCALATED"}:
            return incident.get("snapshot", {})
        initial: WorkflowState = {"incident_id": incident_id, "trace": []}
        result = self.graph.invoke(initial, {"recursion_limit": 30})
        risk = (result.get("policy") or {}).get("risk_tier")
        self.repository.update_incident(incident_id, status=result["status"], risk_tier=risk, snapshot=result)
        return result

    @staticmethod
    def _trace(state: WorkflowState, node: str) -> list[str]:
        return [*state.get("trace", []), node]

    def _ingest(self, state: WorkflowState) -> dict[str, Any]:
        incident = self.repository.get_incident(state["incident_id"])
        scenario = get_scenario(incident["scenario"]).model_dump(mode="json")
        return {"scenario": scenario, "status": IncidentStatus.DETECTED.value, "trace": self._trace(state, "ingest_incident")}

    def _collect(self, state: WorkflowState) -> dict[str, Any]:
        existing = self.repository.all("SELECT * FROM evidence WHERE incident_id=:id ORDER BY collected_at", {"id": state["incident_id"]})
        if existing:
            evidence = [{k: item[k] for k in ("kind", "summary", "source_ref")} for item in existing]
        else:
            evidence = self.sandbox.collect(state["scenario"])
            for item in evidence:
                self.repository.execute("""INSERT INTO evidence (id,incident_id,kind,summary,source_ref,collected_at)
                    VALUES (:id,:incident,:kind,:summary,:source_ref,:now)""",
                    {"id": new_id("ev"), "incident": state["incident_id"], **item, "now": utcnow()})
        self.repository.audit(state["incident_id"], "evidence.collected", "diagnostic-reader", {"references": [e["source_ref"] for e in evidence]})
        return {"evidence": evidence, "trace": self._trace(state, "collect_evidence")}

    def _retrieve(self, state: WorkflowState) -> dict[str, Any]:
        runbook = get_runbook(state["scenario"]["runbook_id"])
        runbook["approved"] = True
        self.repository.audit(state["incident_id"], "runbook.retrieved", "agent", {"runbook_id": runbook["id"], "version": runbook["version"]})
        return {"runbook": runbook, "trace": self._trace(state, "retrieve_runbooks")}

    def _hypotheses(self, state: WorkflowState) -> dict[str, Any]:
        started = time.perf_counter()
        hypotheses = self.model.hypothesize(state["scenario"], state["evidence"], state["runbook"])
        for item in hypotheses:
            self.repository.execute("""INSERT INTO hypotheses (id,incident_id,statement,confidence,evidence_refs)
                VALUES (:id,:incident,:statement,:confidence,:refs)""",
                {"id": new_id("hyp"), "incident": state["incident_id"], **{k: item[k] for k in ("statement", "confidence")},
                 "refs": json.dumps(item["evidence_refs"])})
        self.repository.execute("""INSERT INTO model_usage
            (id,incident_id,provider,model,input_tokens,output_tokens,cost_usd,latency_ms,created_at)
            VALUES (:id,:incident,:provider,:model,:input_tokens,:output_tokens,0,:latency,:now)""",
            {"id": new_id("usage"), "incident": state["incident_id"], "provider": self.model.provider,
             "model": self.model.model, "input_tokens": len(json.dumps(state["evidence"])) // 4,
             "output_tokens": len(json.dumps(hypotheses)) // 4,
             "latency": (time.perf_counter() - started) * 1000, "now": utcnow()})
        return {"hypotheses": hypotheses, "trace": self._trace(state, "generate_candidate_hypotheses")}

    def _choose(self, state: WorkflowState) -> dict[str, Any]:
        scenario = state["scenario"]
        plan = {
            "id": new_id("plan"), "action": scenario["action"], "namespace": self.sandbox.namespace,
            "resource_kind": scenario["resource_kind"], "resource": scenario["resource"],
            "parameters": scenario["parameters"], "recovery_criterion": scenario["recovery_criterion"],
            "justification_refs": [state["hypotheses"][0]["evidence_refs"], f"runbook://{state['runbook']['id']}@{state['runbook']['version']}"],
            "rollback": {"strategy": "restore captured original state", "automatic": True},
        }
        self.repository.execute("""INSERT INTO remediation_plans
            (id,incident_id,action,parameters_json,rollback_json,created_at)
            VALUES (:id,:incident,:action,:params,:rollback,:now)""",
            {"id": plan["id"], "incident": state["incident_id"], "action": plan["action"],
             "params": json.dumps(plan["parameters"]), "rollback": json.dumps(plan["rollback"]), "now": utcnow()})
        return {"plan": plan, "trace": self._trace(state, "choose_remediation_candidate")}

    def _validate(self, state: WorkflowState) -> dict[str, Any]:
        plan = state["plan"]
        valid = bool(plan["resource"] and isinstance(plan["parameters"], dict) and plan["namespace"] == self.sandbox.namespace)
        plan = {**plan, "preflight": {"valid": valid, "checks": ["typed parameters", "sandbox namespace", "named resource"]}}
        return {"plan": plan, "trace": self._trace(state, "validate_parameters")}

    def _classify(self, state: WorkflowState) -> dict[str, Any]:
        decision = self.policy.evaluate(state["plan"])
        plan = {**state["plan"], "candidate_risk": decision.risk_tier.value}
        return {"plan": plan, "trace": self._trace(state, "classify_risk")}

    def _policy(self, state: WorkflowState) -> dict[str, Any]:
        decision = self.policy.evaluate(state["plan"]).model_dump(mode="json")
        self.repository.execute("""INSERT INTO policy_decisions
            (id,incident_id,allowed,risk_tier,reasons_json,approval_required,created_at)
            VALUES (:id,:incident,:allowed,:risk,:reasons,:approval,:now)""",
            {"id": new_id("pol"), "incident": state["incident_id"], "allowed": int(decision["allowed"]),
             "risk": decision["risk_tier"], "reasons": json.dumps(decision["reasons"]),
             "approval": int(decision["approval_required"]), "now": utcnow()})
        self.repository.audit(state["incident_id"], "policy.evaluated", "policy-engine", decision)
        if not decision["allowed"]:
            return {"policy": decision, "status": IncidentStatus.BLOCKED.value, "outcome": "escalated_external_change", "trace": self._trace(state, "policy_engine")}
        return {"policy": decision, "trace": self._trace(state, "policy_engine")}

    @staticmethod
    def _after_policy(state: WorkflowState) -> str:
        if not state["policy"]["allowed"]:
            return "close"
        return "approval" if state["policy"]["approval_required"] else "execute"

    def _approval(self, state: WorkflowState) -> dict[str, Any]:
        approval = self.repository.approval(state["incident_id"])
        if not approval:
            self.repository.audit(state["incident_id"], "approval.requested", "agent", {"risk_tier": state["policy"]["risk_tier"]})
            return {"approval": None, "status": IncidentStatus.PENDING_APPROVAL.value, "outcome": "waiting_for_operator", "trace": self._trace(state, "approval_checkpoint")}
        if approval["decision"] == "REJECTED":
            return {"approval": approval, "status": IncidentStatus.REJECTED.value, "outcome": "operator_rejected", "trace": self._trace(state, "approval_checkpoint")}
        return {"approval": approval, "status": IncidentStatus.EXECUTING.value, "trace": self._trace(state, "approval_checkpoint")}

    @staticmethod
    def _after_approval(state: WorkflowState) -> str:
        if state["approval"] is None:
            return "wait"
        return "execute" if state["approval"]["decision"] == "APPROVED" else "close"

    def _execute(self, state: WorkflowState) -> dict[str, Any]:
        plan, incident_id = state["plan"], state["incident_id"]
        key = f"{incident_id}:{plan['action']}:{plan['resource']}"
        existing = self.repository.latest_execution(key)
        if existing:
            return {"execution": existing, "status": IncidentStatus.EXECUTING.value, "trace": self._trace(state, "execute_allowlisted_tool")}
        repeated = self.repository.recent_matching_execution(plan["action"], plan["resource"], self.policy.cooldown_seconds)
        if repeated:
            self.repository.audit(incident_id, "execution.blocked_cooldown", "executor", {"previous_execution": repeated["id"]})
            return {"execution": None, "status": IncidentStatus.BLOCKED.value, "outcome": "cooldown_blocked", "trace": self._trace(state, "execute_allowlisted_tool")}
        original = self.sandbox.snapshot(plan)
        started = time.perf_counter()
        result = self.sandbox.execute(plan)
        execution = {"id": new_id("exe"), "incident_id": incident_id, "idempotency_key": key,
                     "action": plan["action"], "resource": plan["resource"], "status": "SUCCEEDED",
                     "original_state": original, "result": result,
                     "duration_ms": (time.perf_counter() - started) * 1000, "created_at": utcnow()}
        self.repository.execute("""INSERT INTO executions
            (id,incident_id,idempotency_key,action,resource,status,original_state_json,result_json,duration_ms,created_at)
            VALUES (:id,:incident_id,:idempotency_key,:action,:resource,:status,:original,:result,:duration_ms,:created_at)""",
            {**{k: execution[k] for k in ("id", "incident_id", "idempotency_key", "action", "resource", "status", "duration_ms", "created_at")},
             "original": json.dumps(original), "result": json.dumps(result)})
        self.repository.audit(incident_id, "execution.completed", "scoped-executor", {"execution_id": execution["id"], "action": plan["action"]})
        return {"execution": execution, "status": IncidentStatus.EXECUTING.value, "trace": self._trace(state, "execute_allowlisted_tool")}

    @staticmethod
    def _after_execute(state: WorkflowState) -> str:
        return "close" if state["status"] == IncidentStatus.BLOCKED.value else "verify"

    def _verify(self, state: WorkflowState) -> dict[str, Any]:
        incident = self.repository.get_incident(state["incident_id"])
        verification = self.sandbox.verify(state["plan"], bool(incident["force_verification_failure"]))
        self.repository.execute("""INSERT INTO verification_results (id,incident_id,healthy,checks_json,created_at)
            VALUES (:id,:incident,:healthy,:checks,:now)""",
            {"id": new_id("ver"), "incident": state["incident_id"], "healthy": int(verification["healthy"]),
             "checks": json.dumps(verification["checks"]), "now": utcnow()})
        status = IncidentStatus.RESOLVED.value if verification["healthy"] else IncidentStatus.EXECUTING.value
        outcome = "verified_recovery" if verification["healthy"] else "verification_failed"
        return {"verification": verification, "status": status, "outcome": outcome, "trace": self._trace(state, "verify")}

    def _rollback(self, state: WorkflowState) -> dict[str, Any]:
        execution = state["execution"]
        result = self.sandbox.rollback(state["plan"], execution["original_state"])
        rollback = {"id": new_id("rbk"), "incident_id": state["incident_id"], "execution_id": execution["id"],
                    "original_state": execution["original_state"], "status": "SUCCEEDED" if result["restored"] else "FAILED",
                    "result": result, "created_at": utcnow()}
        self.repository.execute("""INSERT INTO rollback_records
            (id,incident_id,execution_id,original_state_json,status,result_json,created_at)
            VALUES (:id,:incident_id,:execution_id,:original,:status,:result,:created_at)""",
            {**{k: rollback[k] for k in ("id", "incident_id", "execution_id", "status", "created_at")},
             "original": json.dumps(rollback["original_state"]), "result": json.dumps(result)})
        self.repository.audit(state["incident_id"], "rollback.completed", "scoped-executor", {"status": rollback["status"]})
        status = IncidentStatus.ROLLED_BACK.value if result["restored"] else IncidentStatus.ESCALATED.value
        outcome = "automatic_rollback_succeeded" if result["restored"] else "rollback_failed_escalated"
        return {"rollback": rollback, "status": status, "outcome": outcome, "trace": self._trace(state, "rollback")}

    def _close(self, state: WorkflowState) -> dict[str, Any]:
        self.repository.audit(state["incident_id"], "incident.closed", "agent", {"status": state["status"], "outcome": state.get("outcome")})
        return {"trace": self._trace(state, "close_or_escalate")}
