from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Protocol
from uuid import uuid4

from .models import ActionProposal, Evidence, Hypothesis, RCAResult, RiskLevel


@dataclass(frozen=True)
class Diagnosis:
    result: RCAResult
    duration_ms: float


class ReasoningProvider(Protocol):
    def diagnose(self, incident_id: str, scenario: str, snapshot: dict[str, Any]) -> Diagnosis: ...


class DeterministicReasoner:
    """Evidence-bound fallback reasoner used when no LLM is configured."""

    def _evidence(self, source: str, claim: str, value: Any, kind: str = "metric") -> Evidence:
        return Evidence(
            evidence_id=f"ev-{uuid4().hex[:10]}", kind=kind, source=source, claim=claim, value=value
        )

    def diagnose(self, incident_id: str, scenario: str, snapshot: dict[str, Any]) -> Diagnosis:
        started = perf_counter()
        evidence: list[Evidence]
        root_cause: str
        confidence: float
        action: ActionProposal

        if snapshot.get("offline_brokers"):
            evidence = [
                self._evidence("kafka-admin", "offline broker IDs", snapshot["offline_brokers"], "topology"),
                self._evidence("kafka-admin", "under-replicated partitions", snapshot["under_replicated_partitions"]),
                self._evidence("producer-metrics", "producer error rate", snapshot["producer_error_rate"]),
            ]
            root_cause, confidence = "broker_unavailability", 0.99
            action = self._action("restart_broker", "Restart isolated broker 2, then wait for ISR recovery", RiskLevel.high,
                                  "one synthetic broker", "stop if replicas do not rejoin", {"broker_id": 2})
        elif snapshot.get("connector_state") == "FAILED" and "authentication" in snapshot.get("connector_error", ""):
            evidence = [
                self._evidence("connect-api", "connector state", snapshot["connector_state"], "state"),
                self._evidence("connect-log", "connector error category", snapshot["connector_error"], "log"),
                self._evidence("broker-health", "broker health excludes cluster fault", snapshot["broker_health"], "topology"),
            ]
            root_cause, confidence = "sink_connector_authentication_failure", 0.98
            action = self._action("refresh_connector_secret", "Refresh the simulated connector credential and restart its tasks",
                                  RiskLevel.medium, "warehouse sink connector", "restore prior credential reference",
                                  {"connector": snapshot["connector"]})
        elif snapshot.get("schema_compatibility", 1.0) < 0.5 and snapshot.get("affected_partitions"):
            evidence = [
                self._evidence("schema-registry", "compatibility score", snapshot["schema_compatibility"]),
                self._evidence("producer-metrics", "producer schema version", snapshot["producer_schema_version"], "configuration"),
                self._evidence("consumer-log", "deserialization errors", snapshot["deserialization_errors"], "log"),
            ]
            root_cause, confidence = "schema_contract_incompatibility", 0.99
            action = self._action("rollback_schema", "Quarantine v8 events and restore the v7 producer contract", RiskLevel.high,
                                  "all consumers of customer.events", "redeploy producer v8 after compatibility fix",
                                  {"target_schema_version": snapshot["registered_schema_version"]})
        elif snapshot.get("repeated_event_id") and snapshot.get("deserialization_errors", 0) > 0:
            evidence = [
                self._evidence("consumer-log", "repeated failing event", snapshot["repeated_event_id"], "event"),
                self._evidence("consumer-log", "deserialization retry count", snapshot["deserialization_errors"], "log"),
                self._evidence("consumer-metrics", "partitions accumulating lag", snapshot["partitions_with_lag"], "topology"),
            ]
            root_cause, confidence = "poison_message_deserialization_failure", 0.99
            action = self._action("quarantine_event", "Move the allow-listed event to the simulated DLQ and resume partition 3",
                                  RiskLevel.medium, "one event on partition 3", "replay the event after correction",
                                  {"event_id": snapshot["repeated_event_id"], "partition": snapshot["affected_partition"]})
        elif snapshot.get("duplicate_ratio", 0) > 0.05 and len(snapshot.get("active_producer_ids", [])) > 1:
            evidence = [
                self._evidence("event-integrity", "duplicate event ratio", snapshot["duplicate_ratio"]),
                self._evidence("producer-inventory", "active producer IDs", snapshot["active_producer_ids"], "topology"),
                self._evidence("producer-config", "idempotence enabled", snapshot["idempotence_enabled"], "configuration"),
            ]
            root_cause, confidence = "duplicate_producer_instance", 0.97
            action = self._action("stop_duplicate_producer", "Stop the copied deployment and enable idempotent production",
                                  RiskLevel.medium, "duplicate synthetic producer", "restart copied deployment if traffic drops",
                                  {"producer_id": snapshot["active_producer_ids"][1], "enable_idempotence": True})
        elif snapshot.get("max_to_mean_rate_ratio", 0) > 2.0:
            evidence = [
                self._evidence("partition-metrics", "partition ingress rates", snapshot["partition_rates"]),
                self._evidence("partition-metrics", "partition lag", snapshot["partition_lag"]),
                self._evidence("event-profile", "message-key cardinality", snapshot["key_cardinality"]),
            ]
            root_cause, confidence = "hot_key_partition_imbalance", 0.96
            action = self._action("deploy_partition_key_v2", "Shadow-test and enable a higher-cardinality partition key",
                                  RiskLevel.high, "clickstream producer and ordering semantics", "restore prior partitioner",
                                  {"strategy": "account_id_plus_session_bucket"})
        elif (snapshot.get("ingress_per_second", 0) > snapshot.get("egress_per_second", 0)
              and snapshot.get("consumer_lag", 0) > snapshot.get("baseline_lag", 0) * 10):
            evidence = [
                self._evidence("consumer-metrics", "consumer lag", snapshot["consumer_lag"]),
                self._evidence("consumer-metrics", "ingress versus egress per second",
                               {"ingress": snapshot["ingress_per_second"], "egress": snapshot["egress_per_second"]}),
                self._evidence("orchestrator", "healthy consumer instances", snapshot["healthy_instances"], "topology"),
            ]
            root_cause, confidence = "consumer_capacity_exhaustion", 0.96
            action = self._action("scale_consumer", "Scale checkout consumers from 2 to 4 within the partition limit",
                                  RiskLevel.low, "checkout consumer group", "scale back to two replicas",
                                  {"consumer_group": snapshot["consumer_group"], "replicas": 4})
        else:
            evidence = [self._evidence("monitor", "unclassified snapshot", snapshot, "snapshot")]
            root_cause, confidence = "unknown_streaming_failure", 0.25
            action = self._action("collect_more_evidence", "Collect broker and client diagnostics", RiskLevel.info,
                                  "read-only", "not applicable", {})

        action.action_id = f"act-{uuid4().hex[:10]}"
        hypothesis = Hypothesis(
            cause=root_cause,
            confidence=confidence,
            supporting_evidence_ids=[item.evidence_id for item in evidence],
        )
        result = RCAResult(
            incident_id=incident_id, scenario=scenario, probable_root_cause=root_cause,
            confidence=confidence, hypotheses=[hypothesis], evidence=evidence, recommended_actions=[action],
        )
        return Diagnosis(result=result, duration_ms=round((perf_counter() - started) * 1000, 3))

    @staticmethod
    def _action(action_type: str, summary: str, risk: RiskLevel, blast_radius: str,
                rollback_plan: str, parameters: dict[str, Any]) -> ActionProposal:
        return ActionProposal(
            action_id="pending", action_type=action_type, summary=summary, parameters=parameters,
            risk=risk, blast_radius=blast_radius, reversibility="Reversible in the synthetic adapter",
            expected_benefit="Restore healthy flow while preserving event integrity", confidence=0.95,
            required_approval=True, rollback_plan=rollback_plan,
        )
