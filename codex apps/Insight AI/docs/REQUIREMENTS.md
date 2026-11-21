Build a complete, runnable application called **ProductionLens — Agentic Production Investigation & Evaluation Platform**.

You are the lead full-stack engineer, AI engineer, and reliability engineer responsible for implementation. Build working software, test it, and document the measured results.

The application has two connected modules:

1. **Production Investigation & RCA:** An agent investigates application incidents using metrics, traces, logs, and deployment history.
2. **Agent Evaluation & Release Assurance:** A platform tests that investigation agent, compares versions, detects regressions, and produces release decisions.

The intended users are application engineers, SREs, platform engineers, and AI engineering teams.

This is an enterprise-oriented portfolio project demonstrating genuine tool-using agents, reliable backend engineering, meaningful integrations, and reproducible evaluation.

## 1. Working instructions

* Inspect the current repository, environment, and applicable repository instructions before changing files.
* Reuse suitable existing code and preserve unrelated changes.
* Create an implementation plan and then execute it.
* Make routine technical decisions independently and document assumptions.
* Complete the authorized implementation instead of stopping after scaffolding, planning, or UI mockups.
* Work incrementally through the milestones below.
* Check current official documentation for dependencies and APIs when implementing them. Pin compatible versions and commit lockfiles.
* Do not invent API capabilities, tool responses, benchmark results, successful tests, or deployments.
* Missing credentials must not block local development. Complete deterministic replay mode and clearly identify which live integrations remain unverified.
* Maintain `docs/BUILD_STATUS.md` with completed work, validation evidence, remaining tasks, and exact continuation instructions.
* Never put secrets in source control, frontend bundles, screenshots, reports, or application logs.
* Do not merge, push, publish, provision paid resources, or modify external production systems without applicable authorization.
* Do not implement the separate database tuning, FinOps, or identity security projects in this build.

## 2. Required product outcomes

A user must be able to:

1. Start the application locally.
2. Open a dashboard and inspect integration health.
3. Generate traffic through an instrumented demo application.
4. Activate a controlled demo fault.
5. Receive or manually create an incident.
6. Start an investigation.
7. Watch the agent gather evidence and update hypotheses.
8. Inspect a diagnosis with source references and uncertainty.
9. Review a proposed demo recovery action.
10. Approve or reject that exact action.
11. Verify recovery using fresh telemetry.
12. Run a benchmark suite against the investigation agent.
13. Compare baseline and candidate versions.
14. Inspect failed cases and intermediate tool calls.
15. See a release decision derived from explicit policy.
16. Export an incident report and evaluation report.

Every displayed result must originate from application state, real telemetry, or explicitly labeled replay fixtures.

## 3. Architecture and stack

Use this stack unless the existing repository provides a compelling reason to adapt:

* Frontend: React, TypeScript, Vite, Tailwind CSS.
* Components: accessible reusable components with consistent design tokens.
* Charts: a maintained React chart library.
* Backend: Python, FastAPI, Pydantic.
* Agent orchestration: LangGraph with durable PostgreSQL-backed checkpoints.
* Persistence: PostgreSQL, SQLAlchemy, Alembic.
* Background work: Redis with a maintained Python worker framework.
* Telemetry: OpenTelemetry Collector, Prometheus, Jaeger.
* Demo logs: structured JSON, ingested into a bounded searchable store.
* Evaluation: Pytest, custom deterministic assertions, and Promptfoo where appropriate.
* Browser validation: Playwright.
* Packaging: Docker Compose.
* CI: GitHub Actions.

Use a monorepo with clear boundaries:

* `apps/web`
* `services/api`
* `services/worker`
* `packages/agent`
* `packages/connectors`
* `packages/evaluation`
* `demo`
* `infra`
* `tests`
* `docs`

Adapt this layout if required by Python packaging conventions.

Architecture responsibilities:

* API authenticates users and validates requests.
* Worker owns long-running investigations and evaluations.
* Agent selects investigative tools.
* Connector layer normalizes external evidence.
* Policy layer independently validates proposed actions.
* Restricted executor performs approved demo actions.
* Evaluation harness owns expected outcomes and scoring.
* PostgreSQL remains the authoritative record of run state.
* Redis transports work; losing a queue message must not silently lose the persisted job.

Do not run long investigations inside HTTP request handlers.

## 4. Operating modes

Implement two explicit modes.

### Replay mode

* Runs without an LLM API key or cloud account.
* Uses versioned telemetry fixtures and a deterministic scripted agent.
* Exercises UI, persistence, orchestration contracts, approvals, and evaluation plumbing.
* Clearly displays “Replay — scripted behavior.”
* Never presents replay success as evidence of real LLM reasoning.

### Live agent mode

* Uses the local instrumented demo environment and a configured LLM provider.
* Performs real tool calls against telemetry sources.
* Persists actual model usage and observed outcomes.
* Fails visibly if a provider is unavailable.
* Never silently substitutes replay responses.

Persist mode on every incident, investigation, experiment, and report.

## 5. Instrumented demo application

Build a small checkout system with:

* Checkout API.
* Payment service.
* Inventory service.
* Dedicated demo database, isolated from the platform database.
* Repeatable traffic generator.

Generate traces across service boundaries and propagate trace context.

Emit:

* Request count.
* Error count and rate.
* Request-duration histograms.
* Dependency duration and failures.
* Database pool usage and wait time.
* CPU utilization through an appropriate runtime or container metrics source.
* Structured logs containing timestamp, service, severity, trace ID, and span ID.

Record deployment and configuration events separately from diagnostic labels.

Implement four bounded faults:

1. Payment dependency delay causing checkout timeouts.
2. A deployment/configuration regression causing application errors.
3. Demo database connection pool exhaustion.
4. CPU saturation within a resource-limited demo container.

Each fault must have:

* A bounded duration or automatic reset.
* A scenario identifier available to the test controller.
* Reproducible setup and cleanup.
* Expected telemetry symptoms.
* A recovery action.
* Ground-truth metadata accessible only to the evaluation controller.

The investigation agent must not access fault-control APIs, hidden labels, scenario answers, or files containing expected diagnoses.

Normal deployment history may reveal a change, but must not include an annotation naming the hidden root cause.

Faults must affect only demo services. Never expose the Docker socket to the agent.

Implement a demo alert rule or equivalent deterministic detector, plus manual incident creation.

## 6. Integration contracts

Implement typed connector interfaces with both replay and live adapters.

Required integrations:

* Prometheus metrics queries.
* Jaeger trace search and retrieval.
* Structured log search.
* Local deployment/configuration history.
* Optional authenticated GitHub read adapter for commits and deployment records.
* Configurable model provider.

Every connector must expose:

* Health status.
* Authentication requirements.
* Timeout and retry policy.
* Response-size limits.
* Data freshness.
* Normalized errors.
* Source metadata and timestamps.

Normalize evidence into a common schema:

* Evidence ID.
* Run ID.
* Source type.
* Source record ID or validated source URL.
* Observation time and collection time.
* Service and environment.
* Relevant query parameters.
* Bounded raw payload or artifact reference.
* Human-readable summary.
* Content hash.
* Freshness and truncation indicators.

Implement tools such as:

* `query_metrics`
* `search_traces`
* `get_trace`
* `search_logs`
* `get_deployments`
* `compare_config`
* `get_service_dependencies`
* `search_runbooks`

Use typed, restricted parameters.

Prefer structured metric operations with validated query templates. If accepting generated PromQL, enforce query scope, time-range, cardinality, timeout, and output limits.

Do not provide arbitrary shell execution, arbitrary SQL, unrestricted HTTP fetching, or production mutation tools.

## 7. Model provider configuration

Implement:

* An OpenAI-compatible adapter using a configurable base URL, API key, and model identifier.
* A separate Anthropic adapter if feasible with the selected SDKs.
* Explicit capability checks for structured output and tool use.
* A connection test.
* Request timeout and bounded retries.
* Usage tracking.
* Clear provider errors.

Do not assume every provider is compatible because it accepts an API key.

Allow a user to configure credentials through backend environment variables. Optionally support authenticated administrator configuration with encrypted persistence and a server-held encryption key.

The browser must never receive saved secrets.

For custom endpoints:

* Require server-side administrator configuration.
* Validate destinations and redirects.
* Allow local development endpoints only through an explicit development allowlist.
* Block metadata endpoints and unauthorized internal destinations.

Store pricing as a dated configuration. Mark cost as unknown if reliable pricing or usage data is unavailable. Do not invent a dollar estimate.

## 8. Investigation agent

Implement one stateful investigation agent with clearly separated orchestration nodes and tools.

The model must dynamically choose follow-up investigation steps based on observations. Do not hardcode the fault-to-answer mapping into live mode.

Suggested lifecycle:

* Queued.
* Collecting initial context.
* Investigating.
* Preparing findings.
* Awaiting action review.
* Executing approved demo action.
* Verifying recovery.
* Completed.
* Inconclusive.
* Failed.
* Cancelled.
* Budget exceeded.

Persist:

* Incident description.
* Service and time window.
* Observations.
* Hypotheses.
* Supporting and contradicting evidence IDs.
* Tool execution history.
* Missing information.
* Remaining budget.
* Proposed action.
* Final report.

Investigation behavior:

1. Validate the incident scope and time window.
2. Establish a comparable healthy baseline.
3. Gather initial symptoms.
4. Identify affected dependencies.
5. Produce plausible hypotheses.
6. Choose the next tool based on unresolved questions.
7. Revise or reject hypotheses when evidence contradicts them.
8. Stop when evidence is sufficient, investigation is blocked, or a limit is reached.

Every tool execution must record its inputs, outputs, duration, status, and evidence references.

Show concise action rationales and evidence summaries. Do not request or expose private chain-of-thought.

## 9. Diagnosis requirements

A diagnosis must contain:

* Incident summary.
* Affected services and customer operation.
* Observed symptoms.
* Timeline.
* Most supported explanation.
* Alternative explanations considered.
* Evidence supporting and contradicting each hypothesis.
* Missing information.
* Proposed next step.
* Recovery proposal if appropriate.
* Verification plan.

Separate:

* Direct observations.
* Inferences.
* Unverified possibilities.

Use confidence labels such as supported, tentative, and inconclusive. Do not display uncalibrated numerical confidence as a probability.

A second LLM agreeing is not independent evidence.

Independent evidence means distinct relevant observations, such as a trace showing payment timeouts and a metric showing payment latency increasing during the same interval.

Validate that every cited evidence ID exists and belongs to the authorized run.

Do not label a cause confirmed merely because a deployment happened near the incident.

## 10. Durable execution and budgets

Implement configurable limits for:

* Model calls.
* Tool calls.
* Elapsed runtime.
* Input and output tokens.
* Estimated cost when known.
* Consecutive failures.
* Evidence volume.

Reserve budget before calls when possible and reconcile afterward.

Use bounded retries with backoff and jitter.

Handle:

* Worker restart.
* Duplicate job delivery.
* Expired worker lease.
* Provider timeout.
* Partial connector failure.
* User cancellation.
* Approval timeout.
* Budget exhaustion.

Persist checkpoints and reconcile unfinished jobs on startup.

A resumed run must not accidentally repeat an external mutation. Use action IDs, idempotency keys, transactional state transitions, and executor-side deduplication.

If completion of an action is uncertain, reconcile observed state before retrying.

## 11. Recovery approval and executor

Limit recovery to allowlisted demo operations, such as disabling a known demo fault or restoring a demo configuration.

The approval screen must show:

* Proposed action.
* Target.
* Exact parameters.
* Supporting evidence.
* Expected effect.
* Risk.
* Preconditions.
* Rollback or reset procedure.
* Expiry.

Bind approval to a hash of the exact action and parameters.

Changing the action invalidates approval.

Check permissions and current preconditions again at execution time.

Store reviewer identity and decision.

Rejected or expired approvals must never execute.

After execution, retrieve fresh telemetry under comparable traffic and check:

* Error-rate improvement.
* Latency improvement.
* Sufficient sample count.
* Whether the relevant symptom actually disappeared.

Report “recovery not verified” when evidence is insufficient.

A successful API response from the executor is not proof of recovery.

## 12. Evaluation platform

Treat the investigation agent as the first system under test, using a versioned evaluation contract that can later support other agents.

Define an agent version using:

* Git commit.
* Prompt hash.
* Tool-schema hash.
* Model identifier.
* Generation settings.
* Runtime configuration.
* Dependency-lock hash.

A run must preserve the exact version metadata it used.

Support:

* Full benchmark execution.
* Individual scenario execution.
* Baseline-versus-candidate comparison.
* Repeated trials.
* Failure inspection.
* Report export.
* Explicit release policy.

Keep the evaluation harness independent of the agent.

The agent cannot change expected answers, thresholds, grading rules, or historical results.

## 13. Benchmark design

Create at least 48 meaningful versioned scenarios:

* 16 diagnosis cases across the four fault families.
* 8 healthy, benign-change, or misleading-correlation cases.
* 8 missing, stale, truncated, or contradictory evidence cases.
* 6 connector timeout or malformed-response cases.
* 6 authorization, prompt-injection, or evidence-integrity cases.
* 4 restart, duplicate-execution, cancellation, or budget cases.

These must vary meaningfully rather than repeat identical inputs.

Each scenario needs:

* Stable ID and version.
* Agent-visible input.
* Agent-visible tool fixtures.
* Hidden expected outcome.
* Permitted and prohibited actions.
* Relevant evidence IDs.
* Deterministic assertions.
* Difficulty and category.
* Fixture provenance.
* Review status.

Keep expected labels outside the agent-visible process boundary or tool-accessible storage.

Mark generated cases as unreviewed until reviewed. Do not claim human review occurred automatically.

Separate development scenarios from held-out scenarios. Do not tune prompts using held-out expected answers.

Maintain an explicit distinction between:

* Deterministic plumbing tests.
* Real-model evaluations using replayed telemetry.
* End-to-end evaluations using live demo telemetry.

## 14. Evaluation methods and baselines

Compare:

1. A fixed diagnostic script.
2. A single LLM call using a fixed evidence packet.
3. The iterative investigation agent.

Use the same incident snapshots and document the information and budget available to each method.

Use deterministic checks for:

* Required schema fields.
* Valid evidence references.
* Expected diagnosis category.
* Appropriate abstention.
* Allowed tools and parameters.
* Cross-run access prevention.
* Approval enforcement.
* Mutation count.
* Budget compliance.
* Recovery state.

A judge model may supplement semantic evaluation, but its scores must remain separately visible.

Do not equate a valid citation with a supported claim. A claim can reference a real record that does not support it.

Report separate metrics for:

* Diagnosis accuracy.
* Appropriate abstention.
* Evidence-reference validity.
* Claim support from reviewed or explicitly labeled judge assessment.
* Prohibited-action attempts.
* Actual prohibited effects.
* Tool success.
* Time to supported diagnosis.
* Token usage.
* Cost when known.
* Recovery verification.
* Repeat-trial consistency.

Calculate metrics in code. Show counts and denominators.

Do not report simulated business savings as measured enterprise impact.

## 15. Release policy and evaluation agent

Create a versioned release-policy file.

Example initial policy:

* All deterministic authorization and approval checks must pass.
* No prohibited side effect may occur in the evaluated suite.
* Required tests must execute successfully.
* Candidate diagnosis quality must meet a declared minimum and allowed regression tolerance.
* Latency and cost must remain within configured limits.
* Missing critical evaluations produce “insufficient evidence,” not a pass.

Thresholds must be visible and editable by an authorized maintainer. Choose initial values, document them as project policy, and do not claim they are industry standards.

Release outcomes:

* Pass.
* Fail.
* Insufficient evidence.

Passing a finite suite does not prove universal safety.

Add a bounded evaluation-assistant workflow that:

1. Reads a candidate version diff.
2. Identifies affected tools, prompts, and behaviors.
3. Selects additional relevant tests.
4. Investigates failed traces.
5. Proposes a minimized reproducer.
6. Suggests a regression test and possible fix.

The fixed mandatory suite must still run.

Generated tests require review before becoming part of the protected benchmark.

The evaluation assistant cannot approve its own fixes or alter release thresholds.

## 16. Frontend experience

Create a polished engineering application with a dark theme, slate surfaces, clear typography, and restrained cyan, emerald, and amber accents.

Required pages:

### Overview

Active incidents, integration health, investigation outcomes, evaluation status, and available usage data.

### Incidents

Search and filter by service, severity, time, status, and operating mode.

### Investigation workspace

Incident summary, timeline, service dependencies, hypothesis table, evidence viewer, tool activity, and missing evidence.

### Action review

Exact proposal, preconditions, approval/rejection, execution status, and recovery measurements.

### Demo lab

Traffic controls, fault selection, reset, and clear separation from agent-accessible tools.

### Evaluations

Suite selector, version selector, progress, case outcomes, and cancellation.

### Version comparison

Quality, latency, usage, failures, release decision, and paired case comparison.

### Failure replay

Inputs, tool calls, relevant outputs, assertions, and proposed reproducer.

### Integrations and settings

Connection tests, masked credentials, model configuration, budgets, and policy visibility.

Implement loading, empty, partial-data, stale-data, disconnected, and error states.

Use server-sent events or an equivalent mechanism for progress. Support reconnecting without losing the run.

Every meaningful button must work. Unavailable features must explain why they are unavailable.

## 17. Persistence and API

Create migrations for entities including:

* Users and roles.
* Services.
* Incidents.
* Investigation runs.
* Run events.
* Evidence.
* Hypotheses.
* Tool executions.
* Deployment events.
* Action proposals.
* Approvals.
* Action executions.
* Agent versions.
* Evaluation suites.
* Evaluation cases.
* Evaluation runs.
* Case results.
* Release decisions.
* Audit events.

Use foreign keys, relevant indexes, timestamps, and uniqueness constraints.

Suggested API groups:

* `/api/incidents`
* `/api/investigations`
* `/api/investigations/{id}/events`
* `/api/investigations/{id}/evidence`
* `/api/investigations/{id}/cancel`
* `/api/actions/{id}/approve`
* `/api/actions/{id}/reject`
* `/api/evaluations`
* `/api/evaluations/{id}/results`
* `/api/versions/compare`
* `/api/integrations`
* `/api/demo`
* `/health/live`
* `/health/ready`

Version contracts and generate OpenAPI documentation.

Return stable error codes and correlation IDs.

Enforce object-level authorization on every read and write.

## 18. Access control and operational boundaries

Implement viewer, investigator, reviewer, and administrator roles.

Use a maintained authentication/session approach. Generate a unique local administrator credential at setup; do not ship a universal default password.

For the initial deployment, support a single organization with explicit role permissions. Document that full multi-tenant isolation is outside this release.

Add:

* Authentication rate limits.
* Secure session handling.
* CSRF protection where applicable.
* Secret redaction.
* Request and payload limits.
* Restricted connector destinations.
* Audit records for configuration and action changes.
* Retention settings for logs and evidence.

Treat logs, runbooks, trace attributes, and commit messages as untrusted content. Instructions inside them cannot alter system policy or tool permissions.

Label audit storage accurately. Ordinary database records are not tamper-proof.

## 19. Testing and CI

Implement meaningful tests for:

* Connector normalization and failure handling.
* Evidence scoping.
* Agent state transitions.
* Diagnosis schema validation.
* Budget enforcement.
* Worker restart and job reconciliation.
* Approval binding and expiry.
* Duplicate-action prevention.
* Evaluation label isolation.
* Release-policy calculation.
* Authentication and permissions.

Browser tests must cover:

1. Replay incident through completed report.
2. Evidence inspection.
3. Rejected action remaining unexecuted.
4. Approved demo action with verification.
5. Evaluation run and version comparison.
6. Missing-provider error state.

Use deterministic CI tests by default.

Real-provider evaluations must require explicit configuration, use protected secrets, and have bounded spending. Do not expose credentials to untrusted pull requests.

Integrate GitHub Actions to run validation and produce machine-readable and human-readable reports.

A skipped live-model test must be reported as skipped, never passed.

## 20. Deployment and developer experience

Provide:

* `.env.example` with descriptions and no secrets.
* Dockerfiles with suitable non-root processes.
* Docker Compose health checks.
* Persistent volumes.
* Database migration commands.
* Demo seed and reset commands.
* Backup and restore instructions.
* Resource limits for fault containers.
* Clean shutdown behavior.
* Troubleshooting documentation.

Document tested commands equivalent to:

* `make bootstrap`
* `make up`
* `make seed`
* `make demo`
* `make test`
* `make eval-replay`
* `make eval-live`
* `make down`

Implement only commands that actually work.

Document Linux and Windows-through-WSL2 setup if supported and tested; otherwise clearly state the tested environment.

Prepare a deployment guide for one Linux VM, including TLS, secrets, persistent storage, backups, and health monitoring.

Do not describe deployment as completed unless it was actually performed and verified.

## 21. Implementation milestones

### Milestone 1 — Foundation

Repository structure, application shell, database, authentication, configuration, and health checks.

### Milestone 2 — Demo and telemetry

Instrumented services, load generator, four faults, telemetry queries, and reset behavior.

### Milestone 3 — Replay investigation

End-to-end incident lifecycle, evidence, hypotheses, persistence, and dashboard.

### Milestone 4 — Live investigation

Real model adapter, dynamic tool selection, evidence-backed findings, budgets, and durable execution.

### Milestone 5 — Controlled recovery

Approval binding, restricted executor, deduplication, and telemetry verification.

### Milestone 6 — Evaluation platform

48 scenarios, baselines, independent scoring, comparison UI, release policy, and evaluation assistant.

### Milestone 7 — Verification and packaging

Browser checks, CI, security boundaries, documentation, benchmark exports, and demo script.

At each milestone:

* Run relevant checks.
* Fix failures.
* Record evidence and limitations.
* Continue to the next milestone when sufficiently verified.

If the session ends, leave precise continuation instructions and preserve completed work.

## 22. Required documentation

Deliver:

* `README.md`
* `docs/ARCHITECTURE.md`
* `docs/BUILD_STATUS.md`
* `docs/AGENT_DESIGN.md`
* `docs/INTEGRATIONS.md`
* `docs/EVALUATION_METHODOLOGY.md`
* `docs/THREAT_MODEL.md`
* `docs/DEPLOYMENT.md`
* `docs/DEMO_SCRIPT.md`
* `docs/KNOWN_LIMITATIONS.md`
* `docs/PORTFOLIO_EVIDENCE.md`

Include architecture diagrams, API contracts, setup instructions, trade-offs, and limitations.

Portfolio evidence must include:

* A five-minute demonstration script.
* One successful diagnosis.
* One appropriate inconclusive result.
* One prevented unauthorized or duplicate action.
* One candidate regression caught by evaluation.
* Measured results with commands, dates, configuration, and sample counts.

Draft résumé bullet templates using placeholders for unavailable measurements. Never fabricate impact numbers.

## 23. Definition of done

The build is complete when:

* A clean checkout starts using documented commands.
* Replay mode works without provider credentials.
* All four faults generate the intended telemetry.
* The agent cannot access hidden ground truth.
* Configured live mode performs genuine model and tool calls.
* Diagnoses reference accessible evidence.
* Insufficient evidence leads to an honest inconclusive result.
* Worker restarts preserve progress.
* Rejected, expired, or altered actions cannot execute.
* Duplicate delivery cannot duplicate a demo mutation.
* Recovery is checked against fresh telemetry.
* The evaluation suite has at least 48 distinct scenarios.
* Baselines and candidate versions can be compared.
* Release decisions come from independent policy.
* UI workflows have been exercised in a browser.
* Reports distinguish replay, real-model, and live-environment results.
* Documentation matches implemented behavior.
* No secrets are committed.

If credentials or environment restrictions prevent an item, complete all independent work and identify the precise unverified item with a reproducible verification procedure.

## 24. Final delivery report

When implementation is finished, report:

1. What was built.
2. How to start it.
3. How to run the demonstration.
4. Which integrations are live, replayed, or unverified.
5. Validation performed and observed results.
6. Benchmark outcomes and sample sizes.
7. Known limitations.
8. Required user configuration.
9. Repository and artifact locations.

Begin by inspecting the repository and environment, create the implementation plan, and then implement ProductionLens through these milestones.
