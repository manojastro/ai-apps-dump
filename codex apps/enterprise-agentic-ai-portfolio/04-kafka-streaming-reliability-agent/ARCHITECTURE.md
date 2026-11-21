# Architecture

## System architecture

```mermaid
flowchart LR
    UI[Domain dashboard] --> API[FastAPI /api/v1]
    CLI[Demo script] --> WF[Reliability workflow]
    API --> WF
    WF --> ADAPTER[StreamingAdapter]
    ADAPTER --> SYN[Synthetic Kafka simulator]
    WF --> RCA[Deterministic reasoner]
    RCA --> EVID[Evidence + typed RCA]
    WF --> DB[(Project-local SQLite)]
    API --> METRICS[Prometheus text metrics]
    FUTURE[Real Kafka adapter] -. protocol seam .-> ADAPTER
    LLM[OpenAI-compatible provider] -. provider seam .-> RCA
```

## Agent investigation workflow

```mermaid
stateDiagram-v2
    [*] --> Snapshot: inject ground-truth scenario
    Snapshot --> Detection: collect metrics/logs/topology
    Detection --> RCA: deterministic rules
    RCA --> AwaitingApproval: evidence-linked action
    AwaitingApproval --> Rejected: operator rejects
    AwaitingApproval --> Approved: operator approves
    Approved --> Executing: exact action + parameters
    Executing --> ExecutionFailed: adapter/action failure
    ExecutionFailed --> Executing: operator retries
    Executing --> Remediated: simulator state changed
    Remediated --> Validated: all guardrails pass
    Remediated --> ValidationFailed: collection/check fails
    ValidationFailed --> Executing: operator retries
```

## Validation workflow

```mermaid
flowchart TD
    A[Proposed action] --> B{Explicit approval?}
    B -- No --> C[409; no execution]
    B -- Yes --> D{Action allow-listed?}
    D -- No --> E[Block and audit]
    D -- Yes --> F[Execute in synthetic adapter]
    F --> G[Collect independent after-state]
    G --> H[Evaluate health + integrity checks]
    H -- Pass --> I[Persist validation; mark VALIDATED]
    H -- Fail --> J[Persist retryable VALIDATION_FAILED]
```

## Persistence

`incidents` stores the current state plus immutable investigation inputs and RCA JSON. `approvals`, `executions`, `validations`, `evaluations`, and `audit_log` are insert-only during normal operation. This is immutable-style rather than cryptographically immutable. A production version should use database roles, append-only event storage, retention controls, and tamper-evident hashes.

## Substitution boundaries

- `StreamingAdapter`: replace `SyntheticKafkaAdapter` with a read-only Kafka Admin/Prometheus collector, and introduce a separate, more restricted execution adapter.
- `ReasoningProvider`: replace or augment `DeterministicReasoner` with structured OpenAI-compatible evidence synthesis. Deterministic detectors should remain authoritative for threshold rules.
- `Repository`: retain the workflow interface while moving from SQLite to PostgreSQL/Alembic.
