from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from .database import Repository
from .detector import DeterministicReasoner, ReasoningProvider
from .models import ApprovalRequest, IncidentStatus, ValidationResult
from .simulator import SCENARIOS, StreamingAdapter, SyntheticKafkaAdapter


class WorkflowConflict(RuntimeError):
    pass


class IncidentNotFound(KeyError):
    pass


class ReliabilityWorkflow:
    def __init__(self, repository: Repository, adapter: StreamingAdapter | None = None,
                 reasoner: ReasoningProvider | None = None):
        self.repository = repository
        self.adapter = adapter or SyntheticKafkaAdapter()
        self.reasoner = reasoner or DeterministicReasoner()

    def investigate(self, scenario: str) -> dict[str, Any]:
        if scenario not in SCENARIOS:
            raise KeyError(scenario)
        incident_id = f"inc-{uuid4().hex[:12]}"
        snapshot = self.adapter.collect(scenario)
        diagnosis = self.reasoner.diagnose(incident_id, scenario, snapshot)
        ground_truth = SCENARIOS[scenario].root_cause
        failure_started_at = (
            datetime.now(timezone.utc) - timedelta(seconds=float(snapshot.get("failure_age_seconds", 0)))
        ).isoformat()
        self.repository.create_incident({
            "incident_id": incident_id,
            "scenario": scenario,
            "status": IncidentStatus.awaiting_approval.value,
            "ground_truth": ground_truth,
            "predicted_root_cause": diagnosis.result.probable_root_cause,
            "confidence": diagnosis.result.confidence,
            "diagnosis_ms": diagnosis.duration_ms,
            "failure_started_at": failure_started_at,
            "snapshot": snapshot,
            "rca": diagnosis.result.model_dump(mode="json"),
        })
        self.repository.audit(
            incident_id, "monitoring-agent", "SyntheticKafkaAdapter.collect", "collect_evidence",
            {"scenario": scenario}, {"evidence_count": len(diagnosis.result.evidence)}, "incident_detected",
        )
        self.repository.audit(
            incident_id, "rca-agent", "DeterministicReasoner.diagnose", "produce_rca",
            {"evidence_ids": [e.evidence_id for e in diagnosis.result.evidence]},
            {"root_cause": diagnosis.result.probable_root_cause, "confidence": diagnosis.result.confidence},
            "request_approval",
        )
        return self.get(incident_id)

    def approve(self, incident_id: str, request: ApprovalRequest) -> dict[str, Any]:
        incident = self._required(incident_id)
        if incident["status"] != IncidentStatus.awaiting_approval.value:
            raise WorkflowConflict(f"incident is {incident['status']}, not awaiting approval")
        status = IncidentStatus.approved if request.approved else IncidentStatus.rejected
        try:
            self.repository.record_approval_and_transition(
                incident_id, request.approved, request.approved_by, request.reason,
                IncidentStatus.awaiting_approval.value, status.value,
            )
        except RuntimeError as exc:
            raise WorkflowConflict(str(exc)) from exc
        self.repository.audit(
            incident_id, request.approved_by, "approval-api", "approve_action",
            {"reason": request.reason}, {"approved": request.approved}, status.value,
        )
        return self.get(incident_id)

    def execute_and_validate(self, incident_id: str) -> dict[str, Any]:
        incident = self._required(incident_id)
        retryable_states = (
            IncidentStatus.approved.value,
            IncidentStatus.execution_failed.value,
            IncidentStatus.validation_failed.value,
        )
        if incident["status"] not in retryable_states:
            raise WorkflowConflict("execution requires an explicit approval")
        action = incident["rca"]["recommended_actions"][0]
        allow_list = {
            "restart_broker", "refresh_connector_secret", "rollback_schema", "quarantine_event",
            "stop_duplicate_producer", "deploy_partition_key_v2", "scale_consumer", "collect_more_evidence",
        }
        if action["action_type"] not in allow_list:
            self.repository.audit(
                incident_id, "execution-policy", "action-allow-list", "block_action",
                {"action_type": action["action_type"]}, {"allowed": False}, "BLOCKED",
            )
            raise WorkflowConflict("action is outside the execution allow-list")
        try:
            self.repository.transition_status(incident_id, retryable_states, IncidentStatus.executing.value)
        except RuntimeError as exc:
            raise WorkflowConflict(str(exc)) from exc

        try:
            execution = self.adapter.execute(
                incident_id, incident["scenario"], action["action_type"], action["parameters"]
            )
        except Exception as exc:
            execution = {
                "success": False, "action_type": action["action_type"], "mode": "synthetic",
                "error_type": type(exc).__name__, "rollback_plan": action["rollback_plan"],
                "message": "Adapter execution failed; incident is retryable",
            }
        execution["mode"] = "synthetic"
        execution["action_type"] = action["action_type"]
        execution["rollback_plan"] = action["rollback_plan"]
        if not execution.get("success"):
            self.repository.record_execution_and_transition(
                incident_id, action["action_id"], execution,
                IncidentStatus.executing.value, IncidentStatus.execution_failed.value,
            )
            self.repository.audit(
                incident_id, "remediation-agent", "SyntheticKafkaAdapter.execute", "execute_action",
                {"action_type": action["action_type"]},
                {"success": False, "error_type": execution.get("error_type"),
                 "rollback_plan": action["rollback_plan"]}, IncidentStatus.execution_failed.value,
            )
            return self.get(incident_id)

        self.repository.record_execution_and_transition(
            incident_id, action["action_id"], execution,
            IncidentStatus.executing.value, IncidentStatus.remediated.value,
        )
        before = incident["snapshot"]
        try:
            after = self.adapter.collect_after(incident_id, incident["scenario"])
            checks = self._checks(incident["scenario"], after)
            passed = all(checks.values())
            summary = ("Streaming health and event-integrity guardrails passed"
                       if passed else "At least one post-remediation guardrail failed")
        except Exception as exc:
            after = {}
            checks = {"adapter_available": False}
            passed = False
            summary = f"Post-action state collection failed ({type(exc).__name__}); incident is retryable"
        validation = ValidationResult(
            incident_id=incident_id, passed=passed, checks=checks,
            before=self._numeric_or_text(before), after=self._numeric_or_text(after), summary=summary,
        )
        final_status = IncidentStatus.validated if passed else IncidentStatus.validation_failed
        self.repository.record_validation_and_transition(
            incident_id, passed, validation.model_dump(mode="json"),
            IncidentStatus.remediated.value, final_status.value,
        )
        self.repository.audit(
            incident_id, "validation-agent", "SyntheticKafkaAdapter.collect_after", "verify_outcome",
            {"before": self._numeric_or_text(before)}, {"after": self._numeric_or_text(after), "checks": checks},
            final_status.value,
        )
        return self.get(incident_id)

    @staticmethod
    def _numeric_or_text(values: dict[str, Any]) -> dict[str, float | int | str]:
        return {key: value for key, value in values.items() if isinstance(value, (int, float, str))}

    @staticmethod
    def _checks(scenario: str, after: dict[str, Any]) -> dict[str, bool]:
        common_lag = after.get("consumer_lag", 0) < 500
        if scenario == "consumer_slowdown":
            return {"lag_recovered": common_lag, "egress_matches_ingress": after["egress_per_second"] >= 900}
        if scenario == "malformed_message":
            return {"lag_recovered": common_lag, "no_deserialization_errors": after["deserialization_errors"] == 0,
                    "poison_event_quarantined": after["dlq_count"] == 1}
        if scenario == "bad_schema":
            return {"lag_recovered": common_lag, "schema_compatible": after["schema_compatibility"] == 1.0,
                    "no_deserialization_errors": after["deserialization_errors"] == 0}
        if scenario == "duplicate_producer":
            return {"duplicates_within_slo": after["duplicate_ratio"] <= 0.001,
                    "single_producer": after["active_producer_count"] == 1,
                    "idempotence_enabled": bool(after["idempotence_enabled"])}
        if scenario == "broker_outage":
            return {"brokers_online": after["offline_brokers"] == 0,
                    "replicas_in_sync": after["under_replicated_partitions"] == 0,
                    "no_offline_partitions": after["offline_partitions"] == 0}
        if scenario == "partition_imbalance":
            return {"lag_recovered": common_lag, "balanced_rate": after["max_to_mean_rate_ratio"] < 1.5}
        if scenario == "connector_failure":
            return {"connector_running": after["connector_state"] == "RUNNING",
                    "tasks_healthy": after["task_failures"] == 0, "lag_recovered": common_lag}
        raise KeyError(scenario)

    def get(self, incident_id: str) -> dict[str, Any]:
        return self._required(incident_id)

    def _required(self, incident_id: str) -> dict[str, Any]:
        incident = self.repository.incident(incident_id)
        if not incident:
            raise IncidentNotFound(incident_id)
        return incident
