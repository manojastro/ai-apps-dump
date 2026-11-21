# Learning notes

Per phase: the concepts used, why, and five interview questions with short answers.

---

## Phase 0 — Scaffold, tooling, compose

**Concepts:** `uv` lockfiles and extras, ruff/mypy, Docker Compose profiles, pydantic-settings, structured JSON logs.
**Why:** reproducible installs (`uv.lock`), heavy services opt-in (profiles keep the default under 6 GB), one config object read from env.

1. *Why Compose profiles?* — They let one file describe core, Airflow and Neo4j stacks while `docker compose --profile core up` starts only what's needed, keeping RAM low.
2. *Why put Postgres and Kafka clients in extras?* — The default install stays permissively licensed and light; production images add `[postgres]`, `[kafka]`.
3. *What does `uv.lock` give you that `requirements.txt` doesn't?* — A cross-platform resolution with hashes for every transitive dependency, including extras, so CI and Docker build the same thing.
4. *Why JSON logs?* — Machine-parseable fields (`run_id`, `node`, `duration_ms`) let Log Analytics or any log tool filter one run without regex.
5. *How do you keep secrets out of the repo?* — `.env` is git-ignored, `.env.example` has only names, cloud uses Key Vault references and managed identity.

## Phase 1 — The synthetic pipeline

**Concepts:** Avro records/enums/unions/logical types, medallion layering (raw → stg → mart), schema-driven ingestion, seeded data generation, data tests (not-null, unique, accepted values, row counts, reconciliation).
**Why:** a realistic but fully synthetic target with enough joins, filters and aggregates to make lineage interesting.

1. *Why load raw tables from the Avro schema rather than inferring types?* — The schema is the contract; a schema change then shows up in the warehouse exactly as it would in production.
2. *What is a reconciliation test?* — It compares a total across layers (staging revenue vs mart revenue) within a tolerance, catching silent row loss or double counting.
3. *Why a fixed random seed?* — Deterministic data makes tests and eval reproducible; the oracle and the agent see identical rows.
4. *Why keep task callables free of Airflow imports?* — The same functions run in Airflow and in the local runner/sandbox, and lineage parsing never imports Airflow.
5. *What's `timestamp-millis`?* — An Avro logical type on `long`; DuckDB converts it with `epoch_ms()`.

## Phase 2 — Schema diff and classification

**Concepts:** Avro schema resolution rules (promotions, aliases, defaults), backward vs forward compatibility, rename detection with evidence.
**Why:** this is pure logic; it must be deterministic and fully tested.

1. *Backward vs forward compatibility?* — Backward: the new schema can read old data (consumers upgrade first). Forward: the old schema can read new data (producers upgrade first).
2. *Is int → long safe?* — Yes, it's a lossless Avro promotion. int → string is not a promotion and is breaking.
3. *How do you detect a rename?* — An Avro alias is strong evidence; otherwise a removed and an added field with the same type, similar name and position score above a threshold, and the evidence is recorded.
4. *Why can a registry-compatible change still break pipelines?* — SQL reads fields by name; an aliased rename is BACKWARD-compatible in the registry but `select amount` still fails.
5. *Why is adding an enum symbol "potentially breaking"?* — Old readers can't decode it, accepted-values tests fail, and filters like `status <> 'CANCELLED'` now include it.

## Phase 3 — Lineage graph

**Concepts:** property graphs, column-level lineage with sqlglot, static AST parsing, BFS with path tracking, versioned persistence.
**Why:** impact analysis is graph traversal; it must be explainable (paths) and reproducible (versions).

1. *Why not only table-level lineage?* — It over-reports: renaming `amount` doesn't affect `Orders by Status`; column-level lineage separates them.
2. *What does sqlglot lineage miss?* — Columns used in JOIN/WHERE/GROUP BY; I add those as `via=join|filter|group` edges.
3. *Why parse DAGs with `ast` instead of importing them?* — Importing executes code and needs Airflow; static parsing is safe and fast, and treats files as data.
4. *How are paths chosen?* — BFS keeps, per node, the path with the "best" edge kinds (value before join/filter), then the shortest.
5. *Why version the graph?* — A run records which graph it used, so results can be reproduced after the pipeline changes.

## Phase 4 — LangGraph agent (analysis)

**Concepts:** `StateGraph`, TypedDict state with reducers, conditional edges, `Send` fan-out, map-reduce.
**Why:** each step is small and testable; fan-out parallelises per-asset assessment.

1. *What does `Send` do?* — From a conditional edge it schedules a node once per payload in the same superstep; results merge through the state reducer (`operator.add` on `assessments`).
2. *Why a reducer on `assessments`?* — Parallel branches write the same key; without a reducer the writes conflict.
3. *Where is the LLM used in analysis?* — Only for the explanation and rename suggestions, which code re-checks.
4. *What makes a verdict "breaking"?* — The SQL building the asset will error, or a data test will fail.
5. *How do you avoid the LLM hallucinating impact?* — Impact is computed from the graph; the LLM never decides which assets are affected.

## Phase 5 — Fix loop and sandbox

**Concepts:** plan → act → verify loops, bounded retries, sandboxed execution, unified diffs, oracles.
**Why:** a fix is only useful if it is verified under the *new* schema.

1. *Why run a baseline before the patch?* — It proves the break is real and shows what the fix changes.
2. *How do you generate test data under the new schema?* — Generate with the old schema, then evolve each record by the diff (renames carry values, int→string becomes `str(int)`, new enum values in 5% of rows).
3. *Why let the LLM return whole files?* — Model-written hunks are often malformed; code computes the diff.
4. *How is the loop bounded?* — `retry_count` with a max of 3 attempts, then escalation; failures are fed back to `plan_fix`.
5. *When should the agent not write a patch?* — When information is lost (a dropped revenue field): it recommends pinning the old schema version and escalates.

## Phase 6 — Human approval, checkpointing, PR

**Concepts:** `interrupt()` / `Command(resume=...)`, durable checkpointers (SQLite/Postgres), idempotency keys, git branches.
**Why:** writes must be gated by a human, and a pause must survive restarts.

1. *What happens to code before `interrupt()` on resume?* — The node re-runs from the start, so that code must be side-effect free.
2. *How does a run survive an API restart?* — State is checkpointed per step under `thread_id=run_id`; a new process resumes it with `Command(resume=...)` (tested).
3. *How is idempotency guaranteed?* — A unique key of topic + canonical schema in the runs table; the poller also tracks the last version per subject.
4. *Why a local branch by default?* — No credentials needed, nothing leaves the machine, and a draft PR is opt-in.
5. *What goes into the approval record?* — Decision, reviewer, comment and timestamp, stored in state and in the report.

## Phase 7 — API and UI

**Concepts:** FastAPI lifespan, background execution, 202 Accepted, 409 for invalid state transitions, Streamlit reruns.
**Why:** a clickable demo and a clean integration surface.

1. *Why 202 for `POST /changes`?* — The run continues asynchronously; the client polls `/runs/{id}`.
2. *Why 409 on approve?* — Approving a run that isn't awaiting approval is a state conflict, not bad input.
3. *How is the UI decoupled?* — It only calls the API, so it can run as a separate container.
4. *How would you secure it?* — Optional `X-API-Key` now; Entra ID on the Container Apps ingress for real users and reviewer identity.
5. *Why bind Streamlit to localhost?* — By default it listens on all interfaces; locally that exposes the approval buttons on the network.

## Phase 8 — Evaluation

**Concepts:** golden sets, precision/recall on sets, label leakage, independent oracles, latency percentiles.
**Why:** numbers in the README must come from runs, and must say what they do and don't measure.

1. *Why is 100% label accuracy not impressive here?* — The same person wrote the rules and the labels; it measures consistency, not generalisation.
2. *What's the oracle?* — Running the unchanged pipeline on the new schema in DuckDB and comparing actual failed builds/tests with predictions; it found a real gap (test recall 29.7%) that led to build-impact analysis.
3. *Why micro-averaged precision/recall?* — Scenarios differ hugely in size; micro-averaging weights each asset equally.
4. *What does the fake-LLM eval tell you?* — That routing, sandbox, retries and guardrails work, not that a real model writes good fixes.
5. *What would make the eval stronger?* — Labels by someone else, real pipelines, and a real-LLM run with cost tracking.

## Phase 9 — Observability and guardrails

**Concepts:** OpenTelemetry spans, JSON logs, prompt-injection defence-in-depth, allow-listed write paths, budgets.
**Why:** an agent that writes code needs traceability and hard limits.

1. *What's your prompt-injection defence?* — Docs are data (wrapped in `<untrusted_data>`), verdicts and routing don't use the LLM, patches are checked for paths/secrets/echoed instructions, and a human approves.
2. *Why scan schema docs at all if they're ignored?* — To flag suspicious producers in the report.
3. *How are budgets enforced?* — Each LLM call checks cost/token totals before and after; exceeding routes to escalation.
4. *Which patch paths are allowed?* — `sql/`, `dags/`, `tests/` of the pipeline, with `.sql/.py/.yaml` only, no `..`, absolute or Windows paths.
5. *How do you trace one run?* — Every log line and span carries `run_id`; spans are named `node.<name>`.

## Phase 10 — Real LLM providers

Status: provider code is written (Azure OpenAI with key or managed identity, OpenAI, Anthropic with server-side refusal fallbacks) but **not run**; running the eval with a real model needs the owner's approval and keys.

1. *Why a provider interface?* — Swap Azure OpenAI / OpenAI / Anthropic / fake without touching nodes.
2. *Why JSON-object outputs?* — Nodes parse plans and file edits deterministically; invalid JSON becomes an `LLMError` and the run escalates.
3. *How is cost estimated?* — Token usage × a price table; unknown Azure deployments use a conservative price.
4. *Why managed identity for Azure OpenAI?* — No keys to rotate or leak.
5. *How do you handle transient errors?* — SDK retries plus tenacity backoff for 429/5xx/connection errors.

## Phase 11 — Deployment (prepared, not executed)

**Concepts:** multi-stage Docker builds, Bicep, Container Apps, Key Vault references, user-assigned identity, OIDC to Azure from GitHub.
**Why:** a credible path to production without running anything.

1. *Why a user-assigned identity?* — It exists before the apps, so role assignments (AcrPull, Key Vault) are in place at first start.
2. *How does the app get the DB password?* — Key Vault secret reference resolved by Container Apps with the identity; it's never in an env file.
3. *Why is the worker fixed at one replica?* — A single poller avoids duplicate polling (idempotency would catch duplicates anyway).
4. *Why `workflow_dispatch` + environment approval?* — No accidental deploys; a human approves each one.
5. *What's missing for production?* — VNet integration, private Postgres, Entra auth on ingress, OTLP to App Insights.

## Phase 12 — Polish

**Concepts:** honest status tables, reproducible numbers, ADRs.

1. *What does `tested` mean in the status table?* — Covered by automated tests that passed in this repo, on this machine.
2. *Why list limitations?* — Interviewers trust a project more when its edges are explicit.
3. *Where do README numbers come from?* — Only from `eval/results/summary.md`, with the command and date.
4. *How do you demo it in 2 minutes?* — The rename scenario: submit → impact graph → patch → approve → branch + report.
5. *What would you build next?* — Real-LLM eval, Azure Schema Registry adapter, dbt manifest extractor, Postgres integration test in CI.
