# Evaluation

## Dataset

The seven simulator scenarios form a deterministic labeled dataset. Each label is a technical cause, not the visible symptom:

| Scenario | Ground-truth cause | Key discriminating evidence |
|---|---|---|
| Consumer slowdown | `consumer_capacity_exhaustion` | ingress > egress, large lag, unhealthy instance |
| Malformed message | `poison_message_deserialization_failure` | repeated event ID and single-partition retries |
| Bad schema | `schema_contract_incompatibility` | schema-version mismatch and broad deserialization errors |
| Duplicate producer | `duplicate_producer_instance` | duplicate ratio, two producer IDs, idempotence off |
| Broker outage | `broker_unavailability` | offline broker and under-replicated partitions |
| Partition imbalance | `hot_key_partition_imbalance` | skewed partition rate/lag and low key cardinality |
| Connector failure | `sink_connector_authentication_failure` | failed connector auth while brokers are healthy |

## Measures

- **RCA accuracy** = exact predicted-cause matches / investigations.
- **Mean confidence** = average stored confidence. It is an asserted calibration input, not proof of calibration.
- **Diagnosis duration** = wall-clock time inside the deterministic reasoning provider.
- **Validation success** = remediations whose scenario-specific health and integrity checks all pass.
- **Approval bypass prevention** is tested by attempting execution in `AWAITING_APPROVAL` and `REJECTED` states.
- **Consumer-lag detection rate** = labeled snapshots over 500 records of lag that receive a classified root cause.
- **MTTD** = simulated failure-start timestamp through persisted incident detection.
- **MTTR** = simulated failure-start timestamp through successful independent validation.
- **Wrong-action prevention** is tested by substituting an unrelated but allow-listed remediation and requiring `EXECUTION_FAILED` with no validation.
- **Failure recovery** is tested with a transient after-state adapter failure that must persist `VALIDATION_FAILED` and succeed on retry.

Run `scripts/run_tests.ps1` for unit, workflow, API, failure, and validation tests. Run `scripts/demo.py` to append a complete benchmark to the local database. Query `/api/v1/evaluations/summary` or `/metrics` for results.

## Interpretation

Perfect accuracy on seven authored fixtures proves rule/fixture agreement, not general Kafka RCA performance. A real evaluation should use held-out incident replays, ambiguous multi-fault cases, noisy/missing telemetry, blinded labels, time-to-detection, top-k cause accuracy, precision/recall per fault class, and post-change SLO regression windows.
