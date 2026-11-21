# StreamSentinel — Kafka Streaming Reliability Agent

StreamSentinel is a local-first POC that turns a streaming failure into a traceable chain of observed state, deterministic detection, evidence-bound root-cause analysis, bounded remediation, explicit approval, and independent outcome validation. It defaults to a synthetic Kafka adapter, so the full workflow runs without a cluster, credentials, or an LLM.

## Problem

Consumer lag is a symptom, not a diagnosis. Scaling consumers may help a capacity problem, do nothing for a hot partition, and amplify poison-message retries. Operational dashboards also rarely prove that a remediation restored both throughput and event integrity.

## Solution

The current slice supports seven ground-truth scenarios: consumer slowdown, malformed message, incompatible schema, duplicate producer, broker outage, partition imbalance, and connector authentication failure. Each produces a realistic metric/topology/log snapshot. A deterministic reasoner classifies the cause, cites evidence IDs, and proposes one allow-listed action with risk, blast radius, reversibility, expected benefit, approval requirement, and rollback plan.

The action cannot execute until a human records approval. Execution mutates incident-specific simulator state only when the action matches the diagnosed scenario; an unrelated allow-listed action leaves the failure in place and records `EXECUTION_FAILED`. A validation agent independently recollects state and checks scenario-specific health and integrity guardrails. Adapter failures are persisted in retryable failure states. Incidents, evaluations, approvals, executions, validations, and append-only audit events are persisted in project-local SQLite.

## Quick start

### Docker

```bash
docker compose up --build
```

Open <http://localhost:8104>. API docs are at <http://localhost:8104/docs>.

### Python 3.11+

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = "$PWD\backend"
uvicorn app.main:app --host 127.0.0.1 --port 8104
```

Run all automated tests:

```powershell
.\scripts\run_tests.ps1
```

Run the complete seven-scenario CLI demonstration:

```powershell
$env:PYTHONPATH = "$PWD\backend"
python scripts\demo.py
```

## Demo workflow

1. Select **Malformed message** in the dashboard.
2. Inspect the repeated event ID, retry count, and single-partition lag evidence.
3. Review the proposed DLQ quarantine, affected partition, risk, and rollback plan.
4. Approve it. Notice that approval and execution are separate operations.
5. Execute in the simulator and inspect the independent validation checks.
6. Repeat with **Partition imbalance** to see why adding consumers is not the recommended fix.
7. Open `/api/v1/evaluations/summary` to inspect measured RCA accuracy and diagnosis latency.

## Architecture and agents

The API is FastAPI with Pydantic v2 decision contracts. SQLite uses the standard library, avoiding a mandatory external database for the POC. `StreamingAdapter` and `ReasoningProvider` protocols isolate synthetic infrastructure and deterministic reasoning from future Kafka/OpenAI-compatible implementations.

The vertical slice uses three bounded logical agents:

| Agent | Responsibility | Inputs | Outputs | Tools | Permission boundary | Failure behavior |
|---|---|---|---|---|---|---|
| Monitoring | Collect incident context | Scenario trigger | Snapshot and incident | Read-only synthetic adapter | Cannot remediate | Rejects unknown scenario |
| RCA | Classify and propose | Persisted snapshot | Typed RCA, evidence, action | Deterministic rules | Cannot execute | Emits low-confidence unknown cause |
| Validation | Verify real outcome | Before/after state | Typed guardrail result | Read-only validation adapter | Cannot approve | Persists retryable `VALIDATION_FAILED` |

See [ARCHITECTURE.md](ARCHITECTURE.md) for diagrams and state transitions.

## API

- `GET /health`, `GET /ready`, `GET /metrics`
- `GET /api/v1/scenarios`
- `POST /api/v1/scenarios/{scenario}/inject`
- `GET /api/v1/incidents` and `GET /api/v1/incidents/{id}`
- `POST /api/v1/incidents/{id}/approval`
- `POST /api/v1/incidents/{id}/execute`
- `GET /api/v1/evaluations/summary`
- `GET /api/v1/activity`

The generated OpenAPI document is the authoritative field-level contract.

## Evaluation and metrics

Every investigation stores the true cause, predicted cause, confidence, diagnosis duration, simulated failure start, detection time, and validated-remediation time. The summary computes deterministic RCA accuracy, lag-detection rate, MTTD, and MTTR. Prometheus-text metrics expose these measures alongside incident, validation, and request metrics. See [EVALUATION.md](EVALUATION.md).

## Security and human control

- Default execution is synthetic and allow-listed; there is no shell tool.
- All actions require explicit approval, even low-risk actions.
- Rejections are terminal for that incident.
- Optional role-separated API-key authentication is enabled with `AUTH_MODE=api_key` plus distinct `API_KEY`, `APPROVER_API_KEY`, and `EXECUTOR_API_KEY` values.
- The dashboard accepts the three secure-mode keys in an in-memory-only panel and sends each key only for its corresponding viewer, approval, or execution operation.
- CORS is explicit, input bodies are typed and bounded, and API keys are never persisted.
- The immutable-style activity log records decision inputs and outputs separately from mutable incident state.

See [SECURITY.md](SECURITY.md) for trust boundaries and production gaps.

## Technology stack

Python 3.11, FastAPI, Pydantic v2, standard-library SQLite, Uvicorn, and a dependency-free responsive dashboard. Docker Compose provides one-command startup. Mock mode is visible in both health output and the UI.

## Failure simulation

Use the dashboard, call the injection endpoint, or run `scripts/demo.py`. Every scenario has a stored ground truth and deterministic post-action state. This makes failure tests repeatable; it does not claim to model every Kafka timing or rebalance behavior.

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [SECURITY.md](SECURITY.md)
- [EVALUATION.md](EVALUATION.md)
- [LIMITATIONS.md](LIMITATIONS.md)
- [DEMO.md](DEMO.md)

## Screenshots

Start the service, open the dashboard at 1440×900, inject `malformed_message`, and capture one screenshot before approval and one after validation. Keeping screenshots generated from a live run prevents stale or fabricated evidence in the repository.

## Interview talking points

- Why root cause is represented as a typed, evidence-linked decision rather than narrative text.
- Why the synthetic adapter is more useful than mocks hidden inside tests: it supports an observable end-to-end demo and a future real-adapter seam.
- How separate approval, execution, and validation records make hallucinated remediation success visible.
- How ground-truth fault injection turns RCA quality into a measurable classification metric.
- Which controls must change before connecting the execution adapter to production Kafka.

## Future improvements

Add a read-only Kafka Admin/metrics adapter, OpenTelemetry spans, time-series MTTD/MTTR, real replay validation, schema-registry integration, and an OpenAI-compatible evidence-synthesis provider behind the existing protocol. Production execution should require workload identity, dual approval for high-risk changes, and policy-as-code.
