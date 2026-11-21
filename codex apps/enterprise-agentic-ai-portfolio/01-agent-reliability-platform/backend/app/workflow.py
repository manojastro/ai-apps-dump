from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from .agents import DeterministicReasoningProvider, severity_rank
from .database import Database, canonical_payload
from .detectors import SAFE_TOOLS, TraceDetector
from .schemas import (
    Detection,
    Evidence,
    ProposedAction,
    RiskLevel,
    Severity,
    ValidationResult,
    WorkflowResult,
    utc_now,
)
from .policy import POLICY_SPECS, PolicyStateProvider, SQLitePolicyStateProvider, SyntheticPolicyRegistry
from .simulator import SyntheticBackupAgentAdapter
from .verification import ArtifactStateProvider, OutcomeVerifier


ACTION_CATALOG: dict[str, dict[str, Any]] = {
    "UNSAFE_ACTION": {"type": "quarantine_agent_version", "risk": RiskLevel.HIGH, "tool": "policy_registry", "benefit": "Stops further policy-violating tool attempts."},
    "HALLUCINATED_SUCCESS": {"type": "require_outcome_attestation", "risk": RiskLevel.MEDIUM, "tool": "evaluation_policy", "benefit": "Prevents unverified success claims from passing the release gate."},
    "AGENT_LOOP": {"type": "enforce_step_budget", "risk": RiskLevel.LOW, "tool": "runtime_policy", "benefit": "Terminates repeated trajectories before cost and latency grow."},
    "COST_SPIKE": {"type": "enforce_cost_budget", "risk": RiskLevel.LOW, "tool": "runtime_policy", "benefit": "Caps per-run model spend."},
    "CONTEXT_OVERFLOW": {"type": "enable_context_compaction", "risk": RiskLevel.LOW, "tool": "runtime_policy", "benefit": "Keeps prompts within the tested context budget."},
    "WRONG_TOOL": {"type": "restrict_tool_routing", "risk": RiskLevel.MEDIUM, "tool": "evaluation_policy", "benefit": "Constrains routing to task-compatible tools."},
    "RETRIEVAL_FAILURE": {"type": "require_retrieval_evidence", "risk": RiskLevel.LOW, "tool": "evaluation_policy", "benefit": "Fails closed when required grounding is absent."},
    "TOOL_FAILURE": {"type": "add_bounded_retry", "risk": RiskLevel.LOW, "tool": "runtime_policy", "benefit": "Retries transient failures within strict limits."},
    "LATENCY_REGRESSION": {"type": "enforce_latency_budget", "risk": RiskLevel.LOW, "tool": "runtime_policy", "benefit": "Stops slow trajectories before the SLO is breached."},
    "PARTIAL_COMPLETION": {"type": "require_completion_contract", "risk": RiskLevel.MEDIUM, "tool": "evaluation_policy", "benefit": "Requires every task acceptance criterion before success."},
    "OUTCOME_MISMATCH": {"type": "require_outcome_attestation", "risk": RiskLevel.MEDIUM, "tool": "evaluation_policy", "benefit": "Makes independently verified state the source of truth."},
}
EXECUTION_TOOL_ALLOWLIST = {"policy_registry", "evaluation_policy", "runtime_policy"}


class ReliabilityWorkflow:
    def __init__(
        self,
        database: Database,
        artifact_provider: ArtifactStateProvider | None = None,
        policy_registry: SyntheticPolicyRegistry | None = None,
        policy_state_provider: PolicyStateProvider | None = None,
    ):
        self.database = database
        self.simulator = SyntheticBackupAgentAdapter()
        self.artifact_provider = artifact_provider or self.simulator.artifact_provider
        self.verifier = OutcomeVerifier(self.artifact_provider)
        self.detector = TraceDetector()
        self.reasoner = DeterministicReasoningProvider()
        self.policy_registry = policy_registry or SyntheticPolicyRegistry(database)
        self.policy_state_provider = policy_state_provider or SQLitePolicyStateProvider(database)

    def run(self, scenario: str, agent_version: str) -> WorkflowResult:
        observed_started = datetime.now(timezone.utc)
        verification_deadline = observed_started + timedelta(minutes=5)
        trace = self.simulator.run(scenario, agent_version)
        verified = self.verifier.verify(
            trace, observed_started.isoformat(), verification_deadline.isoformat()
        )
        detections = self.detector.detect(trace, verified)
        self.database.insert_run(
            trace.model_dump(mode="json"), "PASSED" if verified.success else "FAILED",
            observed_started.isoformat(), verification_deadline.isoformat(),
        )
        self.database.audit(
            incident_id=None, agent="Trace Analysis Agent", tool="trace_reader",
            action="analyze_trace", input_data={"run_id": trace.run_id, "scenario": scenario},
            output_data=[d.model_dump(mode="json") for d in detections],
            evidence={"step_count": len(trace.steps)},
            validation_result="outcome_verified" if verified.success else "outcome_mismatch",
        )
        incident_id = None
        rca = None
        action = None
        if detections:
            incident_id = f"inc_{uuid4().hex[:12]}"
            evidence = self._build_evidence(trace, detections, verified)
            rca = self.reasoner.synthesize(incident_id, detections, evidence)
            action = self._propose_action(incident_id, detections[0])
            max_severity = max(detections, key=lambda d: severity_rank(d.severity.value)).severity.value
            self.database.insert_incident(
                incident_id, trace.run_id, max_severity, detections[0].title,
                [d.model_dump(mode="json") for d in detections], rca,
            )
            self.database.insert_action(action)
        validation = ValidationResult(
            validation_id=f"val_{uuid4().hex[:12]}",
            incident_id=incident_id or trace.run_id,
            stage="OUTCOME_VERIFICATION",
            passed=verified.success,
            checks=verified.checks,
            details="Independent synthetic artifact-store verification; the final agent message was not trusted.",
        )
        self.database.insert_validation(validation, action.action_id if action else None)
        if incident_id:
            self.database.audit(
                incident_id=incident_id, agent="RCA Agent", tool="evidence_store",
                action="produce_rca_and_action",
                input_data={"detection_codes": [d.code for d in detections]},
                output_data={"root_cause": rca.probable_root_cause, "action": action.model_dump(mode="json")},
                evidence=[e.model_dump(mode="json") for e in rca.evidence],
                decision="PROPOSE", approval="REQUIRED" if action.required_approval else "NOT_REQUIRED",
                validation_result="PASSED" if validation.passed else "FAILED",
            )
        return WorkflowResult(
            run_id=trace.run_id,
            incident_id=incident_id,
            trace=trace,
            detections=detections,
            verified_outcome=verified,
            rca=rca,
            proposed_action=action,
            validation=validation,
        )

    @staticmethod
    def _build_evidence(trace, detections: list[Detection], verified) -> list[Evidence]:
        evidence: list[Evidence] = []
        for index, detection in enumerate(detections, 1):
            sequences = detection.evidence_sequences
            matched = [s.model_dump(mode="json") for s in trace.steps if s.sequence in sequences]
            value: Any = matched or {
                "cost_usd": trace.total_cost_usd,
                "context_tokens": trace.context_tokens,
                "latency_ms": sum(s.latency_ms for s in trace.steps),
                "outcome_checks": verified.checks,
            }
            evidence.append(Evidence(
                evidence_id=f"ev_{trace.run_id[4:]}_{index}", source="persisted_trace",
                fact=detection.code, value=value, observed_at=trace.completed_at,
            ))
        return evidence

    @staticmethod
    def _propose_action(incident_id: str, finding: Detection) -> ProposedAction:
        definition = ACTION_CATALOG.get(finding.code, ACTION_CATALOG["PARTIAL_COMPLETION"])
        risk = definition["risk"]
        return ProposedAction(
            action_id=f"act_{uuid4().hex[:12]}", incident_id=incident_id,
            action_type=definition["type"], description=f"Apply {definition['type']} for the affected agent version.",
            risk=risk, blast_radius="One synthetic agent version", reversibility="Fully reversible policy update",
            expected_benefit=definition["benefit"], confidence=finding.confidence,
            required_approval=risk in {RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL},
            rollback_plan="Restore the previous versioned policy from the local registry.",
            allowed_tool=definition["tool"],
        )

    def approve(self, action_id: str, approver: str, decision: str, reason: str) -> dict[str, Any]:
        action = self.database.query_one("SELECT * FROM actions WHERE action_id = ?", (action_id,))
        if not action:
            raise LookupError("action not found")
        if action["status"] not in {"PROPOSED", "REJECTED", "REAPPROVAL_REQUIRED"}:
            raise ValueError(f"action is already {action['status']}")
        payload, payload_hash = self._validate_action_binding(action)
        approval_id = f"apr_{uuid4().hex[:12]}"
        now = utc_now()
        with self.database.connect() as connection:
            connection.execute(
                """INSERT INTO approvals
                   (approval_id, action_id, approver, decision, reason, payload_version, payload_hash, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (approval_id, action_id, approver, decision, reason, payload.payload_version, payload_hash, now),
            )
            connection.execute("UPDATE actions SET status = ?, updated_at = ? WHERE action_id = ?", (decision, now, action_id))
        self.database.audit(
            incident_id=action["incident_id"], agent="Human Approval Gate", tool="approval_registry",
            action="review_action", input_data={"action_id": action_id, "reason": reason},
            output_data={"decision": decision}, decision=decision, approval=approver,
        )
        return {
            "approval_id": approval_id, "action_id": action_id, "decision": decision,
            "payload_version": payload.payload_version, "payload_hash": payload_hash, "created_at": now,
        }

    def execute(self, action_id: str) -> dict[str, Any]:
        action = self.database.query_one("SELECT * FROM actions WHERE action_id = ?", (action_id,))
        if not action:
            raise LookupError("action not found")
        payload, payload_hash = self._validate_action_binding(action)
        tool = payload.allowed_tool
        if tool not in EXECUTION_TOOL_ALLOWLIST:
            raise PermissionError("action tool is not allow-listed")
        if action["required_approval"]:
            approval = self.database.query_one(
                """SELECT * FROM approvals WHERE action_id = ? AND decision = 'APPROVED'
                   ORDER BY created_at DESC LIMIT 1""", (action_id,),
            )
            if action["status"] != "APPROVED" or not approval:
                raise PermissionError("human approval is required before execution")
            if approval["payload_hash"] != payload_hash or approval["payload_version"] != payload.payload_version:
                raise PermissionError("approved payload does not match executable payload")
        if action["status"] == "EXECUTED":
            raise ValueError("action has already been executed")
        if action["status"] in {"REJECTED", "ROLLED_BACK"}:
            raise PermissionError(f"action is {action['status'].lower()}")
        now = utc_now()
        spec = POLICY_SPECS[payload.action_type]
        before = self.policy_state_provider.read(spec["policy_key"])
        expected_after = {
            "policy_key": spec["policy_key"], "version": before["version"] + 1, "value": spec["value"]
        }
        error = None
        try:
            applied_before, expected_after = self.policy_registry.apply(payload)
            if applied_before != before:
                raise RuntimeError("policy state changed concurrently")
        except Exception as exc:
            error = type(exc).__name__
        observed_after = self.policy_state_provider.read(spec["policy_key"])
        checks = {
            "payload_hash_verified": canonical_payload(payload)[1] == payload_hash,
            "tool_allowlisted": tool in EXECUTION_TOOL_ALLOWLIST,
            "policy_schema_valid": payload.action_type in POLICY_SPECS,
            "state_changed": observed_after != before,
            "version_incremented": observed_after.get("version") == before["version"] + 1,
            "expected_policy_value": observed_after.get("value") == expected_after["value"],
            "apply_completed": error is None,
            "rollback_available": True,
        }
        passed = all(checks.values())
        rollback = {"available": True, "snapshot": before}
        status = "EXECUTED"
        if not passed:
            rollback_error = None
            controller_response: dict[str, Any] = {}
            try:
                controller_response = self.policy_registry.rollback(before)
            except Exception as exc:
                rollback_error = type(exc).__name__
            authoritative_restored = self.policy_state_provider.read(spec["policy_key"])
            checks["rollback_completed"] = rollback_error is None
            checks["rollback_restored"] = authoritative_restored == before
            rollback = {
                "available": True, "controller_response": controller_response,
                "authoritative_observation": authoritative_restored,
                "error": rollback_error,
            }
            status = (
                "ROLLED_BACK"
                if checks["rollback_completed"] and checks["rollback_restored"]
                else "ROLLBACK_FAILED"
            )
        execution_id = self.policy_registry.record_execution(
            action_id, status, before, observed_after, rollback
        )
        self.database.execute("UPDATE actions SET status = ?, updated_at = ? WHERE action_id = ?", (status, now, action_id))
        validation = ValidationResult(
            validation_id=f"val_{uuid4().hex[:12]}", incident_id=action["incident_id"],
            stage="POST_ACTION_SHADOW_VALIDATION", passed=passed, checks=checks,
            details=(
                "Observed persistent policy state matches the approved action-specific expectation."
                if passed else (
                    f"Post-action state failed validation and authoritative readback verified rollback; error={error or 'state_mismatch'}."
                    if status == "ROLLED_BACK" else
                    f"Post-action state failed validation and authoritative rollback readback failed; error={rollback.get('error') or error or 'state_mismatch'}."
                )
            ),
        )
        self.database.insert_validation(validation, action_id)
        self.database.audit(
            incident_id=action["incident_id"], agent="Policy Execution Controller", tool=tool,
            action=payload.action_type, input_data={"action_id": action_id, "payload_hash": payload_hash},
            output_data={"status": status, "before": before, "after": observed_after, "rollback": rollback},
            decision="EXECUTE" if passed else ("ROLLBACK" if status == "ROLLED_BACK" else "ROLLBACK_FAILED"), approval="VERIFIED" if action["required_approval"] else "NOT_REQUIRED",
            execution_result=("SYNTHETIC_POLICY_UPDATED" if passed else ("SYNTHETIC_POLICY_ROLLED_BACK" if status == "ROLLED_BACK" else "SYNTHETIC_POLICY_ROLLBACK_FAILED")),
            validation_result="PASSED" if passed else "FAILED",
        )
        return {
            "action_id": action_id, "execution_id": execution_id, "status": status,
            "mode": "safe-simulation", "before": before, "after": observed_after,
            "rollback": rollback, "validation": validation.model_dump(mode="json"),
        }

    def _validate_action_binding(self, action: dict[str, Any]) -> tuple[ProposedAction, str]:
        try:
            payload = ProposedAction.model_validate_json(action["payload_json"])
        except Exception as exc:
            raise ValueError("action payload is malformed") from exc
        _, payload_hash = canonical_payload(payload)
        if not action.get("payload_hash") or action["payload_hash"] != payload_hash:
            raise ValueError("action payload hash mismatch")
        if int(action["payload_version"]) != payload.payload_version:
            raise ValueError("action payload version mismatch")
        row_bindings = {
            "action_id": action["action_id"] == payload.action_id,
            "incident_id": action["incident_id"] == payload.incident_id,
            "action_type": action["action_type"] == payload.action_type,
            "risk": action["risk"] == payload.risk.value,
            "required_approval": bool(action["required_approval"]) == payload.required_approval,
        }
        if not all(row_bindings.values()):
            raise ValueError("action payload does not match persisted action identity")
        incident = self.database.query_one("SELECT detections_json FROM incidents WHERE incident_id = ?", (payload.incident_id,))
        if not incident:
            raise ValueError("action incident does not exist")
        primary_code = json.loads(incident["detections_json"])[0]["code"]
        expected = ACTION_CATALOG.get(primary_code, ACTION_CATALOG["PARTIAL_COMPLETION"])
        spec = POLICY_SPECS.get(payload.action_type)
        if (
            payload.action_type != expected["type"]
            or payload.allowed_tool != expected["tool"]
            or payload.risk != expected["risk"]
            or not spec
            or spec["tool"] != payload.allowed_tool
        ):
            raise ValueError("action payload is not bound to the incident action catalog")
        return payload, payload_hash
