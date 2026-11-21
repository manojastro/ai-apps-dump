from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ScenarioDefinition:
    name: str
    description: str
    root_cause: str
    snapshot: dict[str, Any]
    healthy_after: dict[str, Any]


SCENARIOS: dict[str, ScenarioDefinition] = {
    "consumer_slowdown": ScenarioDefinition(
        name="consumer_slowdown",
        description="Checkout consumer processing capacity falls below ingress rate.",
        root_cause="consumer_capacity_exhaustion",
        snapshot={
            "topic": "orders.v1", "consumer_group": "checkout", "consumer_lag": 12_500,
            "baseline_lag": 180, "ingress_per_second": 920, "egress_per_second": 140,
            "deserialization_errors": 0, "consumer_instances": 2, "healthy_instances": 1,
            "failure_age_seconds": 45,
        },
        healthy_after={"consumer_lag": 210, "egress_per_second": 940, "healthy_instances": 4},
    ),
    "malformed_message": ScenarioDefinition(
        name="malformed_message",
        description="A poison event is retried indefinitely on one partition.",
        root_cause="poison_message_deserialization_failure",
        snapshot={
            "topic": "payments.v2", "consumer_group": "ledger", "consumer_lag": 4_200,
            "baseline_lag": 70, "deserialization_errors": 48, "repeated_event_id": "evt-poison-42",
            "affected_partition": 3, "partitions_with_lag": [3], "schema_compatibility": 1.0,
            "failure_age_seconds": 18,
        },
        healthy_after={"consumer_lag": 65, "deserialization_errors": 0, "dlq_count": 1},
    ),
    "bad_schema": ScenarioDefinition(
        name="bad_schema",
        description="Producer deploy emits schema version 8 incompatible with registered version 7.",
        root_cause="schema_contract_incompatibility",
        snapshot={
            "topic": "customer.events", "consumer_group": "crm-indexer", "consumer_lag": 7_800,
            "schema_compatibility": 0.22, "producer_schema_version": 8, "registered_schema_version": 7,
            "deserialization_errors": 630, "affected_partitions": [0, 1, 2, 3], "failure_age_seconds": 12,
        },
        healthy_after={"consumer_lag": 95, "schema_compatibility": 1.0, "deserialization_errors": 0},
    ),
    "duplicate_producer": ScenarioDefinition(
        name="duplicate_producer",
        description="A second producer deployment reuses business event IDs.",
        root_cause="duplicate_producer_instance",
        snapshot={
            "topic": "shipment.events", "duplicate_ratio": 0.31, "baseline_duplicate_ratio": 0.001,
            "active_producer_ids": ["shipper-a", "shipper-a-copy"], "consumer_lag": 110,
            "idempotence_enabled": False, "failure_age_seconds": 60,
        },
        healthy_after={"duplicate_ratio": 0.001, "active_producer_count": 1, "idempotence_enabled": True},
    ),
    "broker_outage": ScenarioDefinition(
        name="broker_outage",
        description="Broker 2 is unavailable and replicas for two partitions are under-replicated.",
        root_cause="broker_unavailability",
        snapshot={
            "topic": "telemetry.raw", "offline_brokers": [2], "under_replicated_partitions": 8,
            "offline_partitions": 2, "in_sync_replica_ratio": 0.66, "producer_error_rate": 0.44,
            "failure_age_seconds": 8,
        },
        healthy_after={"offline_brokers": 0, "under_replicated_partitions": 0, "offline_partitions": 0,
                         "in_sync_replica_ratio": 1.0, "producer_error_rate": 0.0},
    ),
    "partition_imbalance": ScenarioDefinition(
        name="partition_imbalance",
        description="A hot key directs most traffic to one partition.",
        root_cause="hot_key_partition_imbalance",
        snapshot={
            "topic": "clickstream", "partition_rates": [85, 91, 88, 1_420],
            "partition_lag": [20, 22, 18, 9_800], "consumer_lag": 9_860,
            "max_to_mean_rate_ratio": 3.37, "key_cardinality": 4, "failure_age_seconds": 75,
        },
        healthy_after={"max_to_mean_rate_ratio": 1.12, "consumer_lag": 105, "key_cardinality": 200},
    ),
    "connector_failure": ScenarioDefinition(
        name="connector_failure",
        description="Warehouse sink connector loses database authentication.",
        root_cause="sink_connector_authentication_failure",
        snapshot={
            "topic": "analytics.enriched", "connector": "warehouse-sink", "connector_state": "FAILED",
            "connector_error": "authentication rejected", "task_failures": 4, "consumer_lag": 18_000,
            "broker_health": "HEALTHY", "failure_age_seconds": 25,
        },
        healthy_after={"connector_state": "RUNNING", "task_failures": 0, "consumer_lag": 160},
    ),
}


class StreamingAdapter(Protocol):
    def collect(self, scenario: str) -> dict[str, Any]: ...
    def execute(self, incident_id: str, scenario: str, action_type: str,
                parameters: dict[str, Any]) -> dict[str, Any]: ...
    def collect_after(self, incident_id: str, scenario: str) -> dict[str, Any]: ...


class SyntheticKafkaAdapter:
    """Credential-free adapter. It never connects to or changes a real Kafka cluster."""

    EXPECTED_ACTIONS = {
        "consumer_slowdown": "scale_consumer",
        "malformed_message": "quarantine_event",
        "bad_schema": "rollback_schema",
        "duplicate_producer": "stop_duplicate_producer",
        "broker_outage": "restart_broker",
        "partition_imbalance": "deploy_partition_key_v2",
        "connector_failure": "refresh_connector_secret",
    }
    EXPECTED_PARAMETERS = {
        "consumer_slowdown": {"consumer_group": "checkout", "replicas": 4},
        "malformed_message": {"event_id": "evt-poison-42", "partition": 3},
        "bad_schema": {"target_schema_version": 7},
        "duplicate_producer": {"producer_id": "shipper-a-copy", "enable_idempotence": True},
        "broker_outage": {"broker_id": 2},
        "partition_imbalance": {"strategy": "account_id_plus_session_bucket"},
        "connector_failure": {"connector": "warehouse-sink"},
    }

    def __init__(self) -> None:
        self._incident_state: dict[str, dict[str, Any]] = {}

    def collect(self, scenario: str) -> dict[str, Any]:
        if scenario not in SCENARIOS:
            raise KeyError(scenario)
        return deepcopy(SCENARIOS[scenario].snapshot)

    def execute(self, incident_id: str, scenario: str, action_type: str,
                parameters: dict[str, Any]) -> dict[str, Any]:
        if scenario not in SCENARIOS:
            raise KeyError(scenario)
        expected = self.EXPECTED_ACTIONS[scenario]
        expected_parameters = self.EXPECTED_PARAMETERS[scenario]
        if action_type != expected or parameters != expected_parameters:
            self._incident_state[incident_id] = deepcopy(SCENARIOS[scenario].snapshot)
            return {
                "success": False,
                "expected_action": expected,
                "received_action": action_type,
                "parameters_match": parameters == expected_parameters,
                "message": "Action or parameters did not address the diagnosed root cause; state was unchanged",
            }
        self._incident_state[incident_id] = deepcopy(SCENARIOS[scenario].healthy_after)
        return {
            "success": True,
            "expected_action": expected,
            "received_action": action_type,
            "parameters": deepcopy(parameters),
            "message": "Exact scenario remediation applied to isolated simulator state",
        }

    def collect_after(self, incident_id: str, scenario: str) -> dict[str, Any]:
        if scenario not in SCENARIOS:
            raise KeyError(scenario)
        if incident_id not in self._incident_state:
            raise RuntimeError("no simulator execution state exists for this incident")
        return deepcopy(self._incident_state[incident_id])
