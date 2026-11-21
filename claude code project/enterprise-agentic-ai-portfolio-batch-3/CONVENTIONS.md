# Batch 3 Portfolio — Shared Engineering Conventions

This document records the architectural contract that all five projects in this
portfolio follow. Each project is fully independent (own backend, frontend, DB,
Docker env, tests); what is shared is the **pattern**, never the code.

## Independence rule

Any project folder can be copied out alone (plus nothing else) and run:
`docker compose up --build` inside it. No cross-project imports, no shared
services, no shared databases.

## Stack standard

| Layer      | Choice                                                        |
| ---------- | ------------------------------------------------------------- |
| Language   | Python 3.11+                                                  |
| API        | FastAPI + Pydantic v2                                         |
| ORM        | SQLAlchemy 2.x (`Base.metadata.create_all()` at startup; schema migrations deliberately deferred for POC — recorded in each `LIMITATIONS.md`) |
| Databases  | SQLite file mode by default; PostgreSQL 16 via each project's `docker-compose.yml` |
| Graphs     | NetworkX in-process dependency-graph abstraction (Neo4j adapter interface documented, not required) |
| LLM        | Provider-neutral interface; OpenAI-compatible HTTP provider via `httpx`; deterministic Mock provider default |
| Tests      | pytest + FastAPI TestClient                                   |
| Metrics    | prometheus-client exposed at `/metrics`                       |
| Frontend   | Zero-build static SPA (vanilla ES modules + CSS) served by FastAPI at `/`. Deliberate tradeoff: guarantees `docker compose up --build` with no Node toolchain; React/Next migration path documented in each project's `LIMITATIONS.md`. |

## Port allocation

| Project | Backend/UI port | Postgres (internal) |
| ------- | --------------- | ------------------- |
| 11      | 8011            | 5432 in-network     |
| 12      | 8012            | 5432 in-network     |
| 13      | 8013            | 5432 in-network     |
| 14      | 8014            | 5432 in-network     |
| 15      | 8015            | 5432 in-network     |

## Configuration contract (no hard-coded vendors or keys)

```env
APP_NAME=…
DATABASE_URL=sqlite:///./data/<project>.db   # compose overrides with postgresql+psycopg://…
LLM_MODE=mock            # mock | live
LLM_BASE_URL=            # OpenAI-compatible endpoint when live
LLM_API_KEY=
LLM_MODEL=
CORS_ORIGINS=http://localhost:8011
LOG_LEVEL=INFO
```

Providers are resolved by a factory. No OpenAI/Anthropic/Gemini SDKs, no model
names, no keys in code. `GET /api/v1/meta` reports `llm_mode`, and every agent
decision records the mode it ran under; the UI shows a persistent **MOCK MODE**
badge whenever mock reasoning was used. Mock results are always labeled as such —
never presented as LLM output.

## Agent architecture contract

* **Deterministic core**: detectors, graph analysis, scoring, and validation are
  plain Python/algorithms. Facts about system state come only from tools,
  stores, or simulators — an LLM may never invent state.
* **LLM as reasoner**: the provider receives structured evidence/facts and must
  return structured output (analysis, plan critique, narrative). In mock mode
  this reasoning is produced deterministically from the same inputs.
* **Workflow engine**: framework-neutral stage machine persisting state
  transitions; stages map cleanly to LangGraph nodes (adapter documented).
* **States**: `DETECTED → INVESTIGATING → DIAGNOSED → PLANNED → VALIDATING →
  AWAITING_APPROVAL → APPROVED → EXECUTING → VERIFYING → COMPLETED`, plus
  `FAILED` / `ROLLED_BACK`.
* **Human approval** is enforced server-side: risky actions cannot execute
  without a persisted approval record.

## Tool safety contract

Agents never receive shell execution. Every tool is a registered object:

```
name · purpose · input schema · permission · risk level (low/med/high)
· timeout · handler · audit logging · output schema
```

The registry validates input against the schema, rejects unregistered tools,
enforces timeouts, writes an audit row per call (`tool_calls`), and returns a
structured result. Domain tools read/write simulator state, the database, and
the graph only.

## Common persistence model

Every project persists domain-appropriate versions of: events, assets,
incidents/investigations (+stage history), evidence, hypotheses,
decisions/recommendations, risk assessments, validations, approvals, actions,
outcomes, metric snapshots, evaluation runs, and the tool-call audit log.

Typed schemas (Pydantic v2) at minimum:

```python
class Evidence(BaseModel):
    source: str
    timestamp: datetime
    fact: str
    reliability: float
    raw_reference: str | None = None

class Decision(BaseModel):
    decision: str
    confidence: float
    evidence_ids: list[str]
    alternatives: list[str]
    risk_level: str
    requires_approval: bool
```

## API surface standard

```
GET  /health          liveness
GET  /readiness       db + seed state
GET  /metrics         Prometheus exposition
GET  /api/v1/meta     app identity, version, llm_mode
POST /api/v1/simulator/seed      (re)build synthetic estate
…domain routers under /api/v1/…
```

Frontend served at `/` from `frontend/`.

## Security baseline

Input validation on every endpoint (Pydantic), allow-listed tools, server-side
approval gates, audit logging of tool calls and approvals, secrets redacted from
logs, CORS restricted by env, safe error handlers (no stack traces to clients),
synthetic data only (never real personal data).

## Evaluation standard

Each project ships labeled scenarios with ground truth and a runner that scores
detection/recall/precision/action correctness against them, persisted as
evaluation runs and asserted by automated tests.
