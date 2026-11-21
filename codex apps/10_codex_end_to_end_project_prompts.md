# 10 End-to-End Codex Build Prompts

These prompts are designed to be pasted **one at a time into Codex in a fresh project repository**.

Each prompt is standalone and tells Codex to plan, build, test, debug, document, containerize, seed demo data, and leave a locally runnable application. The scope is a **production-style POC**: real architecture, real tests, real observability, safe mock/sandbox integrations when external credentials are unavailable.

---

# 1. P3 — Service Desk Deflection Agent

## CODEX MASTER PROMPT

You are the principal engineer responsible for delivering a complete, locally runnable, production-style POC called **Service Desk Deflection Agent**.

Do not stop at architecture, pseudocode, scaffolding, TODOs, or a partially working UI. Work autonomously through planning, implementation, integration, testing, debugging, documentation, and final verification. If something is ambiguous, make a sensible engineering decision, document the assumption, and continue. Do not wait for clarification unless progress is technically impossible.

## Business objective

Build an AI-powered enterprise IT support application that can receive employee support requests, understand intent, retrieve approved support knowledge, safely execute approved IT support actions, resolve common L1 requests, and escalate unresolved requests into an ITSM ticket with a complete diagnostic summary.

The system must demonstrate measurable **ticket deflection**, not just chatbot responses.

A request counts as strictly deflected only when:
1. No human agent is involved.
2. The requested problem is resolved.
3. The ticket is not reopened within the configurable replay window, default 72 hours.

## Primary user journeys

Implement these end-to-end journeys:

1. Employee opens the web support chat.
2. Employee describes a problem in natural language.
3. Agent classifies intent.
4. Agent retrieves relevant approved SOP/runbook content.
5. Agent determines whether an action tool is required.
6. Agent asks for confirmation before state-changing actions.
7. Tool is executed through a permission-aware tool layer.
8. Agent verifies the outcome.
9. If resolved, interaction is marked resolved/deflected.
10. If confidence is low, policy blocks the action, or resolution fails, create/escalate an ITSM ticket containing:
   - user issue
   - detected intent
   - troubleshooting already performed
   - retrieved knowledge references
   - tool calls and results
   - confidence
   - recommended next action
11. Operations dashboard updates metrics.

Support at minimum:
- password reset simulation
- account unlock simulation
- VPN troubleshooting
- MFA troubleshooting
- software access request
- Wi-Fi/network troubleshooting
- known outage lookup
- knowledge-only questions
- unsupported/unknown issue escalation

## Required architecture

Build a clean monorepo with:

- `apps/web` — React or Next.js frontend
- `apps/api` — FastAPI backend
- `services/agent` — LangGraph-based orchestration
- `services/tools` — IT support action adapters
- `services/retrieval` — hybrid RAG
- `packages/shared` — shared schemas/types
- `infra` — Docker Compose and local infrastructure
- `tests` — unit, integration, end-to-end, evaluation
- `docs` — architecture, threat model, demo guide, API docs

Use:
- Python 3.12+
- FastAPI
- LangGraph
- PostgreSQL
- Qdrant
- Redis only if useful
- React/Next.js + TypeScript
- Docker Compose
- pytest
- Playwright for critical UI E2E tests
- provider abstraction for LLMs
- OpenAI-compatible model configuration through environment variables
- deterministic mock LLM mode for automated tests

Do not hardcode secrets.

## RAG requirements

Create a seed knowledge base containing realistic but synthetic IT SOPs for the supported intents.

Implement:
- document ingestion
- chunking
- metadata
- vector retrieval
- keyword/BM25-style retrieval or equivalent
- hybrid ranking
- source citations
- retrieval confidence
- tenant/role metadata ready for future authorization

The model must not invent support procedures when no evidence exists. Low-evidence queries must escalate.

## Agent design

Implement an explicit LangGraph state machine with nodes such as:

- normalize request
- classify intent
- retrieve knowledge
- plan resolution
- policy check
- request confirmation if required
- execute tool
- verify result
- calculate confidence
- resolve or escalate
- persist session outcome

Use typed structured outputs with Pydantic.

Prevent infinite loops using maximum step counts.

All tool calls must be auditable.

## Tool layer

Create safe local implementations for:
- reset password
- unlock account
- check outage
- check account state
- check VPN profile
- submit software access request
- create ITSM ticket

Use a mock directory/user database for local demo.

Also create adapter interfaces so Jira Service Management or ServiceNow can be added through environment configuration.

If real credentials are absent, the complete demo must still function using the mock ITSM adapter.

## Dashboard

Create a polished operations dashboard showing:
- total conversations
- strict deflection rate
- loose automation rate
- escalation rate
- reopen rate
- resolution by intent
- average resolution time
- cost per conversation
- cost per resolved request
- tool success/failure
- confidence distribution
- top unresolved intents
- daily trend
- latest escalated tickets

Create a conversation-detail page showing the full decision trace without exposing hidden model reasoning. Show only safe operational traces: states, tool calls, evidence, decisions, confidence, timing, and outcome.

## Data model

At minimum:
- users
- support_sessions
- messages
- intents
- knowledge_documents
- retrieval_evidence
- tool_executions
- resolutions
- escalations
- tickets
- reopen_events
- model_usage
- audit_events

Use migrations.

## Security

Implement:
- basic local authentication with seeded demo roles
- RBAC: employee, support_agent, admin
- authorization on all state-changing APIs
- input validation
- output encoding
- secrets only in environment variables
- structured audit logging
- rate limiting
- prompt-injection defenses around retrieved content
- allowlisted tools
- confirmation for state-changing operations
- no model-generated arbitrary shell commands

Create `docs/THREAT_MODEL.md`.

## Observability

Add:
- structured logs
- request IDs
- agent run IDs
- tool call duration
- model latency
- retrieval latency
- token/cost tracking
- Prometheus-compatible metrics endpoint if practical
- health and readiness endpoints

## Evaluation

Create a replay dataset with at least 100 synthetic support requests spanning common, edge, ambiguous, adversarial, and unanswerable cases.

Measure:
- intent accuracy
- retrieval relevance
- groundedness/faithfulness
- strict deflection
- escalation precision
- unsafe action attempts blocked
- tool execution success
- reopen simulation
- average cost
- p50/p95 latency

Provide a command such as:

`make eval`

Generate JSON plus a human-readable Markdown/HTML report.

## Testing

Required:
- unit tests
- backend API tests
- agent state-machine tests
- retrieval tests
- policy tests
- tool tests
- DB tests
- at least 3 critical Playwright E2E flows
- failure-path tests
- deterministic CI mode without a paid LLM

The repository is not complete until the core test suite passes.

## Demo data

Seed:
- 25+ synthetic users
- common IT issues
- IT knowledge articles
- mock account states
- mock VPN states
- mock outages
- historical support sessions
- tickets and reopen events

Include demo users and passwords only for local development and document them clearly.

## Developer experience

Provide:
- `.env.example`
- one-command local startup: preferably `docker compose up --build`
- `Makefile` or task runner with:
  - `make setup`
  - `make dev`
  - `make test`
  - `make eval`
  - `make seed`
  - `make lint`
- database migrations
- API docs
- sample curl commands

## Documentation

Create:
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/AGENT_FLOW.md`
- `docs/THREAT_MODEL.md`
- `docs/EVALUATION.md`
- `docs/DEMO_SCRIPT.md`
- `docs/PRODUCTION_GAPS.md`

README must include architecture diagram using Mermaid.

## Final acceptance criteria

Do not declare completion until:

- application starts locally from documented commands
- employee can complete a full support conversation
- at least one safe action executes successfully
- at least one failed/low-confidence request escalates to ITSM
- ticket contains diagnostic context
- dashboard updates
- knowledge citations are visible
- audit trail is visible
- seed data works
- core tests pass
- evaluation command works
- Docker configuration works
- no secrets are committed
- no critical TODO placeholders remain in the primary flow

## Execution workflow

1. Inspect existing repository.
2. Create `PLAN.md` with milestones.
3. Create `TASKS.md` and maintain checkboxes as work progresses.
4. Implement vertical slices instead of disconnected layers.
5. Run tests after each major slice.
6. Fix failures immediately.
7. Perform a final clean-room startup using only README instructions.
8. Run the main demo journey.
9. Run test and evaluation suites.
10. Write `FINAL_STATUS.md` containing:
   - completed capabilities
   - commands run
   - test results
   - evaluation results
   - known limitations
   - exact next production hardening steps

Start now and continue until the application satisfies the acceptance criteria.

---

# 2. P5 — Self-Healing Remediation Agent

## CODEX MASTER PROMPT

Act as a senior AI platform/AIOps engineer. Build a complete production-style POC named **Self-Healing Remediation Agent**.

The application must detect operational problems in a safe Kubernetes sandbox, diagnose them using telemetry and approved runbooks, create a remediation plan, validate that plan against policy, assign a risk tier, request human approval when required, execute only allowlisted actions, verify recovery, and roll back automatically if verification fails.

Do not create an unrestricted autonomous shell agent. All remediation must be constrained to explicit safe tools and a dedicated sandbox namespace.

Work autonomously through implementation, testing, debugging, documentation, Docker/local Kubernetes setup, and final verification. Do not stop at scaffolding.

## Core workflow

Implement:

**Detect → Retrieve runbook → Diagnose → Plan → Policy validation → Sandbox/pre-flight validation → Risk classification → Approval if required → Execute → Health verification → Rollback if needed → Audit**

Risk tiers:

### LOW
Examples:
- restart one unhealthy pod
- scale a demo deployment within configured min/max
- clear a synthetic application cache
- re-run a failed demo job

May auto-execute if policy allows.

### MEDIUM
Examples:
- rollback a deployment to previous revision
- change replica count beyond normal threshold
- modify a demo feature flag

Must require approval by default.

### HIGH
Examples:
- destructive data action
- namespace-wide action
- security-sensitive configuration change
- action outside allowlist

Must never auto-execute. For the POC, HIGH actions should normally be blocked and shown as requiring an external change process.

## Environment

Use a local safe cluster:
- kind, k3d, or minikube
- dedicated namespace such as `selfheal-demo`
- intentionally breakable sample applications
- Prometheus metrics
- Kubernetes events/logs
- synthetic incident generator

Provide scripts to create and destroy the sandbox.

## Stack

- FastAPI
- Python
- LangGraph
- PostgreSQL
- Prometheus
- Kubernetes Python client
- React/Next.js
- Docker
- pytest
- optional local vector store/Qdrant for runbooks
- provider-agnostic LLM adapter
- deterministic test model

## Required demo incidents

Create repeatable incident scenarios:
1. CrashLoopBackOff
2. unhealthy pod requiring restart
3. excessive latency
4. replica shortage
5. bad deployment requiring rollback
6. failing scheduled job
7. incident that must be escalated because no safe remediation exists

Each scenario must have:
- detection signal
- expected diagnosis
- applicable runbook
- allowed/blocked actions
- health probe
- expected recovery criterion

## Agent

Use explicit graph nodes:
- ingest incident
- collect evidence
- retrieve runbooks
- generate candidate hypotheses
- choose remediation candidate
- validate parameters
- classify risk
- policy engine
- approval checkpoint
- execute allowlisted tool
- verify
- rollback
- close/escalate

Every factual claim used to justify remediation must link to collected telemetry or an approved runbook.

The model must never produce raw commands for direct execution.

## Policy engine

Implement deterministic policy outside the LLM.

Policies must cover:
- allowed namespace
- allowed resources
- allowed actions
- risk tier
- max scaling limit
- required approvals
- maintenance-window configuration
- action cooldown
- repeated-action prevention

Keep policy configurable through YAML or database configuration.

## Approval workflow

Create UI/API where an operator can:
- inspect incident
- review evidence
- view proposed change
- see risk classification
- see rollback plan
- approve
- reject
- add comment

Persist approval state so browser refresh/process restart does not lose the decision.

Measure approval rate by risk tier.

## Rollback

Before any reversible state-changing action:
- record original state
- generate rollback record
- persist it
- execute action
- run health checks

If verification fails:
- run rollback automatically when safe
- record rollback result
- escalate if rollback fails

## Dashboard

Show:
- active incidents
- detected vs resolved
- auto-resolution rate
- verified recovery rate
- MTTR
- approval rate by tier
- actions blocked by policy
- rollback rate
- failed recovery rate
- top incident types
- historical timeline

Incident detail must show evidence, runbook, hypothesis, plan, policy decision, approval, action, verification, and rollback.

## Data model

Include:
- incidents
- signals
- evidence
- runbooks
- hypotheses
- remediation_plans
- policy_decisions
- approvals
- executions
- verification_results
- rollback_records
- audit_events
- model_usage

## Safety requirements

- sandbox namespace only by default
- explicit allowlist
- no arbitrary shell execution
- no secret values sent to model
- read-only cluster service account for diagnosis
- separate narrowly scoped execution credential
- destructive operations disabled in demo
- high-risk actions blocked
- rate limiting/cooldowns
- full audit trail
- CSRF/auth protection for approvals
- secure secret loading

Create threat model.

## Evaluation

Create benchmark runner for all demo incident classes and failure injection.

Measure:
- diagnosis accuracy
- correct runbook selection
- risk-classification accuracy
- unsafe actions blocked
- successful verified recovery
- rollback success
- MTTR
- approval rate by tier
- duplicate action rate
- cost per incident

Include at least 50 replay cases.

## Testing

Test:
- policies
- risk classifier
- evidence collection
- graph paths
- approval persistence
- execution tool constraints
- rollback
- idempotency
- API
- dashboard critical E2E flow
- injected failures

## Deliverables

Include:
- Docker Compose for app dependencies
- cluster bootstrap scripts
- demo workload manifests
- incident injection scripts
- `.env.example`
- Makefile
- README
- Mermaid architecture
- demo script
- evaluation report
- threat model
- production-hardening notes

## Acceptance test

A reviewer must be able to:
1. create the local demo cluster
2. inject a known fault
3. see the incident detected
4. see evidence and diagnosis
5. see a risk-tiered remediation
6. approve when required
7. watch safe execution
8. see health verification
9. observe automatic rollback in a forced-failure scenario
10. inspect complete audit history

Finish only after the full path works and core automated tests pass.

Maintain `PLAN.md`, `TASKS.md`, and `FINAL_STATUS.md`. Start implementation now.

---

# 3. P4 — Multi-Agent Incident RCA

## CODEX MASTER PROMPT

Build a complete, locally runnable production-style POC named **Multi-Agent Incident RCA**.

The system must investigate operational incidents by coordinating specialized evidence-collection agents, correlate information across telemetry sources, rank root-cause hypotheses, run a critic pass against the leading hypothesis, and generate a source-cited incident RCA/postmortem draft.

The project must prove that the agents use tools and evidence rather than model memory.

Do not stop at an agent diagram. Deliver the full web application, APIs, data stores, mock telemetry environment, evaluation suite, tests, and Docker setup.

## Core architecture

Use a supervisor-worker pattern.

Workers:
1. Metrics Investigator
2. Logs Investigator
3. Deployment/Change Investigator
4. Ticket/Incident History Investigator

Then:
5. Correlation Agent
6. Hypothesis Ranker
7. Critic/Devil's Advocate
8. RCA Composer

Every evidence item must receive an immutable source/evidence ID.

No generated factual statement is allowed into the final RCA unless it references one or more evidence IDs.

## Technology

Use:
- FastAPI
- Python
- LangGraph
- Prometheus
- Neo4j
- PostgreSQL
- optional Loki or a lightweight log store
- React/Next.js
- Docker Compose
- OpenTelemetry where useful
- pytest
- Playwright
- LLM provider adapter with deterministic test mode

## Demo observability environment

Create 3–5 synthetic microservices with:
- HTTP endpoints
- Prometheus metrics
- structured logs
- dependency relationships
- deployment/change events
- generated incidents

Create at least these scenarios:
- bad deployment causing elevated 5xx
- downstream dependency latency
- database connection exhaustion
- CPU/memory saturation
- configuration change causing authentication failures
- misleading correlated signal where the obvious hypothesis is wrong

Seed historical tickets that provide useful or misleading evidence.

## Incident workflow

1. Incident is created from alert or manually.
2. Supervisor creates investigation plan.
3. Workers run concurrently where practical.
4. Each worker calls only its designated tools.
5. Evidence is normalized and persisted.
6. Neo4j stores service/dependency/change relationships.
7. Correlation layer constructs a timeline.
8. Candidate hypotheses are generated.
9. Each hypothesis includes supporting and contradicting evidence.
10. Hypotheses receive confidence scores.
11. Critic explicitly searches for evidence that disproves the leading hypothesis.
12. Final RCA is drafted with citations.

## RCA output

Generate:
- executive summary
- customer/user impact
- detection
- timeline
- root cause
- contributing factors
- supporting evidence
- rejected hypotheses
- remediation already performed
- corrective actions
- prevention recommendations
- confidence and unresolved questions

Do not expose hidden chain-of-thought. Show concise decision rationale and evidence references only.

## UI

Pages:
- incident list
- active investigation view
- evidence explorer
- service dependency graph
- timeline
- hypothesis comparison
- final RCA viewer/editor
- evaluation dashboard

Use a polished, enterprise operations design.

## Metrics

Measure:
- root-cause category accuracy
- exact root-cause accuracy where applicable
- evidence citation coverage
- unsupported-claim rate
- investigation duration
- token/cost usage
- worker latency
- critic overturn rate
- accuracy by incident category

## Evaluation dataset

Create at least 60 deterministic incident replay cases.

Each case must have ground truth:
- root-cause category
- root-cause service/component
- relevant evidence
- distractor evidence
- expected timeline facts

Evaluation must fail unsupported claims.

Provide:
`make eval`

Produce machine-readable and human-readable reports.

## Security

- read-only telemetry tool adapters
- RBAC
- audit logs
- no arbitrary shell execution
- sanitized log retrieval
- redact configured secret patterns before LLM calls
- strict tool schemas
- prompt-injection resistance for ticket/log content

## Tests

Include:
- worker unit tests
- graph routing tests
- correlation tests
- evidence citation enforcement tests
- Neo4j integration tests
- API tests
- incident replay tests
- failure/time-out worker tests
- at least 3 Playwright E2E flows

## Developer experience

Provide:
- one-command Docker startup
- deterministic seed data
- incident generator
- `.env.example`
- Makefile
- migrations
- README
- Mermaid architecture
- API docs
- demo script

## Acceptance criteria

Do not stop until a reviewer can:
- start the environment
- inject an incident
- watch workers collect evidence
- inspect timeline and dependency graph
- see multiple ranked hypotheses
- see the critic challenge the leader
- generate an evidence-cited RCA
- run the evaluation suite
- confirm all final factual claims have evidence IDs

Maintain `PLAN.md`, `TASKS.md`, and `FINAL_STATUS.md`. Build, test, debug, and verify the entire application.

---

# 4. P12 — Agent Evaluation + CI Regression Harness

## CODEX MASTER PROMPT

Build a complete reusable product named **Agent Evaluation + CI Regression Harness** for testing RAG systems and AI agents before deployment.

This must not be a notebook-only benchmark. Build a real developer platform with CLI, REST API, web dashboard, dataset management, experiment runs, baseline comparison, CI quality gates, cost/latency tracking, and deterministic tests.

The core value is making AI quality measurable and preventing regressions on every pull request.

## Required capabilities

### Dataset management
Support golden test cases containing:
- user input
- expected answer or expected properties
- expected sources
- tags
- difficulty
- category
- answerability
- allowed tools
- forbidden tools
- metadata

Seed a 200-question demo dataset:
- 60% common
- 25% edge
- 15% unanswerable

### Target adapters
Support evaluating:
- HTTP API target
- Python callable/plugin target
- RAG response schema
- agent response schema with tool-call trace

Create a demo agent application in `examples/` so the harness can be tested end to end.

### Metrics
Implement or integrate:
- context precision
- context recall
- faithfulness/groundedness
- answer relevance
- answer correctness where ground truth exists
- citation correctness
- tool-selection accuracy
- task success
- unanswerable handling
- latency p50/p95
- token usage
- cost per request

Use Ragas where appropriate but do not make the architecture dependent on one library.

### Judge model
- abstract judge provider
- pin judge model/config in run metadata
- support deterministic rule-based metrics
- support mock judge for CI
- never silently change judge configuration

### Baselines
Allow an experiment to be marked as baseline.

Compare candidate vs baseline.

CI must fail when:
- any configured critical metric falls below absolute threshold
- regression exceeds configured relative threshold, default 3%
- p95 latency exceeds threshold
- cost exceeds threshold
- unsafe/forbidden tool call occurs

### Statistical reporting
Where practical:
- confidence intervals/bootstrap comparisons
- per-category metrics
- aggregate metrics
- sample-level failures
- changed cases between runs

## Stack

- Python
- FastAPI
- PostgreSQL
- React/Next.js
- background worker if useful
- Ragas
- pytest
- GitHub Actions
- Docker Compose

## CLI

Build commands such as:
- `evalharness dataset import`
- `evalharness run`
- `evalharness compare`
- `evalharness report`
- `evalharness gate`

Configuration should support YAML.

## Dashboard

Pages:
- projects
- datasets
- test cases
- experiment runs
- baseline comparison
- metric trends
- failure explorer
- category breakdown
- cost/latency
- CI status

A developer must be able to click a failed case and see:
- input
- expected
- actual
- retrieved contexts
- citations
- tool trace
- metric scores
- judge metadata

## GitHub Actions

Provide a reusable example workflow that:
1. starts the demo target
2. runs evaluation
3. compares to baseline
4. applies quality gates
5. writes Markdown summary to job output
6. emits machine-readable artifact
7. exits non-zero on unacceptable regression

Do not require paid API access for the default CI demonstration.

## Persistence schema

Include:
- projects
- datasets
- test_cases
- experiments
- runs
- samples
- metric_results
- baselines
- judge_configs
- cost_records
- gate_configs
- gate_results

## API

Provide documented CRUD/run/compare endpoints.

## Testing

Test:
- metric implementations
- dataset parsing
- baseline comparison
- regression math
- gate behavior
- unanswerable cases
- cost calculations
- mock judge
- API
- CLI
- GitHub Actions compatible deterministic mode
- dashboard E2E

## Documentation

Create:
- README
- architecture
- metric definitions
- dataset schema
- target adapter guide
- CI guide
- judge-model policy
- example reports
- production gaps

## Acceptance criteria

A reviewer must be able to:
1. start locally
2. view a seeded project and 200-question dataset
3. run an evaluation against the included demo agent
4. mark a run as baseline
5. intentionally introduce a bad demo configuration
6. rerun
7. see metric regression
8. see failed cases
9. run the CI gate and receive a failing exit code
10. restore good configuration and see the gate pass

Keep `PLAN.md`, `TASKS.md`, and `FINAL_STATUS.md`. Do not stop at scaffolding; finish the entire workflow.

---

# 5. P13 — AI Gateway: Routing, Cache, Cost Governance

## CODEX MASTER PROMPT

Build a complete **multi-tenant AI Gateway** that exposes an OpenAI-compatible API in front of multiple model providers and demonstrates enterprise-grade routing, caching, reliability, usage governance, and cost control.

The product must be locally runnable even with zero external LLM API keys by using a deterministic mock provider.

Do not stop at a proxy. Deliver the control plane, data plane, policies, dashboard, observability, tests, and failure simulation.

## Core request path

Implement:

**Authenticate → identify tenant/team → rate limit → budget check → exact cache → semantic cache → route model tier → provider call → fallback/circuit breaker → usage ledger → response**

## Stack

- Python
- FastAPI
- LiteLLM where beneficial
- PostgreSQL
- Redis
- Prometheus
- React/Next.js
- Docker Compose
- pytest
- provider adapter architecture

## API compatibility

Implement a practical subset of OpenAI-compatible endpoints sufficient for:
- chat completions
- models
- embeddings if required for semantic cache

Streaming support is desirable for chat requests.

Preserve relevant response metadata and add gateway headers/request IDs.

## Multi-tenancy

Entities:
- organizations
- teams
- users/API keys
- budgets
- routing policies
- providers
- models

API keys must be hashed at rest.

Every request must map to a tenant/team.

## Routing

Support policies based on:
- requested model alias
- task tier
- estimated prompt size
- latency target
- remaining budget
- provider health

Create model aliases such as:
- `fast`
- `balanced`
- `quality`

Implement weighted/fallback routing.

## Exact cache

Cache identical safe requests.

Cache key must include:
- tenant ID
- normalized request
- model/routing policy version
- relevant generation parameters

## Semantic cache

Implement embeddings-based semantic cache.

Default similarity threshold must be conservative, approximately 0.97, configurable.

Tenant identity MUST be part of semantic cache isolation.

Never return a cached result across tenants.

Provide a test that explicitly proves cross-tenant cache leakage cannot occur.

## Budget governance

Support:
- monthly team budget
- per-request maximum
- warning threshold
- hard stop threshold
- cheap-tier fallback option
- usage ledger
- cost attribution

Dashboard must show spend by team, model, provider, and day.

## Reliability

Implement:
- provider health state
- timeout
- retries with sensible bounds
- circuit breaker
- fallback provider
- synthetic provider failure injector
- idempotent request tracking where relevant

## Security

- API-key authentication
- admin auth
- RBAC
- secret encryption/configuration through environment
- request size limits
- rate limiting
- audit trail
- configurable prompt/response logging policy
- PII-safe logging mode
- tenant-safe caches
- no secret values in logs

## Dashboard

Pages:
- overview
- requests
- teams
- budgets
- providers
- models
- routing policies
- cache analytics
- costs
- latency
- circuit-breaker events
- audit

Metrics:
- requests
- success rate
- p50/p95
- cost per 1,000 requests
- exact-cache hit rate
- semantic-cache hit rate
- provider share
- cheap-tier share
- fallback rate
- blocked budget requests

## Observability

Export:
- Prometheus metrics
- structured logs
- correlation IDs
- model/provider latency
- cache outcomes
- budget decisions
- fallback/circuit-breaker events

## Seed/demo

Include:
- three tenants
- multiple teams
- sample budgets
- mock providers: cheap/fast/quality
- deterministic latency/cost characteristics
- failure injection
- demo request generator

## Evaluation/benchmark

Provide script comparing configurations:
1. no cache
2. exact cache
3. semantic cache
4. tier routing
5. routing + cache

Report:
- cost per 1,000 requests
- hit rates
- latency
- quality proxy on seeded benchmark
- fallback behavior

## Testing

Test:
- auth
- rate limiting
- budget enforcement
- routing
- exact cache
- semantic cache
- tenant isolation
- circuit breaker
- fallback
- usage calculations
- streaming where implemented
- API compatibility
- dashboard E2E

## Developer deliverables

Provide:
- one-command Docker startup
- migrations
- `.env.example`
- Makefile
- load generator
- README
- architecture diagram
- API examples
- threat model
- benchmark report
- production gaps

## Acceptance criteria

A reviewer can:
- create/use tenant API key
- send an OpenAI-compatible request
- see it routed
- demonstrate exact cache
- demonstrate semantic cache
- prove tenant isolation
- exhaust a demo budget and see enforcement
- force provider failure and see circuit-breaker/fallback
- inspect usage/cost dashboard
- run benchmark and tests

Maintain `PLAN.md`, `TASKS.md`, and `FINAL_STATUS.md`. Continue until all primary acceptance criteria work.

---

# 6. P2 — Governed MCP Gateway + Server Registry

## CODEX MASTER PROMPT

Build a complete enterprise-style **Governed MCP Gateway + Server Registry**.

The application must demonstrate how many small domain-specific MCP servers can be discovered and used through a central governed layer that controls identity, authorization, tool visibility, argument-level policy, approvals, and audit.

The focus is not merely "make an MCP server." The focus is **governed enterprise MCP architecture**.

Do not stop with three sample servers. Deliver the registry, gateway, UI, auth, policy engine, audit trail, approval workflow, test clients, threat model, and end-to-end demo.

## Architecture

Create:

### MCP Server A — ITSM
Tools:
- search tickets
- read ticket
- create ticket
- update ticket

Writes require policy evaluation and approval where configured.

### MCP Server B — Analytics
Tools:
- list approved datasets
- describe dataset
- execute read-only analytics query against seeded demo database

No mutation tools.

### MCP Server C — Knowledge
Tools:
- search approved knowledge
- fetch document metadata/content

Read-only.

### Central components

1. Server Registry
2. Gateway / policy enforcement point
3. Identity/RBAC layer
4. Argument policy engine
5. Approval service
6. Append-only audit service
7. Admin UI

## Technology

Choose Python or TypeScript based on best MCP SDK support in the environment.

Use:
- official-compatible MCP SDK
- JWT authentication
- optional OIDC-ready adapter
- PostgreSQL
- FastAPI/Node API as appropriate
- React/Next.js admin UI
- Docker Compose
- pytest/vitest
- Playwright

## Registry

Store:
- server ID
- name
- owner/team
- environment
- endpoint/transport
- tool inventory
- tool classifications
- risk level
- health
- allowed roles
- data classification
- version
- last scan

Gateway must query registry before exposing tools.

## Identity and permissions

Seed roles:
- employee
- analyst
- support_engineer
- manager
- platform_admin

Tool visibility must differ by role.

Example:
- employee cannot see ticket mutation tools
- analyst can use analytics read tools
- support engineer can request ITSM writes
- admin can manage registry/policies

## Argument-level policy

Do not only authorize tool name.

Validate tool arguments, for example:
- a user may update only tickets in allowed business unit
- analytics queries must be read-only
- query row limit
- forbidden tables
- ticket priority escalation may require approval
- sensitive document category blocked

Implement deterministic policy outside the LLM.

## Write approval

For protected tools:
1. client requests tool call
2. gateway validates
3. gateway creates pending approval
4. approver reviews arguments and requesting identity
5. approval/rejection recorded
6. approved tool call is executed
7. result and audit event persisted

## Audit

Append-only logical audit log containing:
- actor
- token/session
- server
- tool
- normalized arguments or protected hash where needed
- policy decision
- approval
- execution status
- timestamp
- correlation ID

Provide searchable UI.

## Security/threat model

Create a detailed MCP-specific threat model covering:
- malicious tool descriptions
- prompt injection through tool data
- confused deputy
- argument tampering
- over-broad permissions
- token theft
- cross-tenant leakage
- untrusted server registration
- tool substitution
- replay
- excessive write scope
- audit tampering

Implement practical mitigations.

## UI

Admin dashboard:
- registered servers
- health
- tools
- roles
- policies
- pending approvals
- audit events
- tool invocation analytics
- denied calls
- latency

Provide role simulator to demonstrate which tools each role can discover.

## Test client

Build a simple MCP client/demo agent that:
- authenticates as different users
- discovers allowed tools
- invokes read tools
- attempts a forbidden call
- requests a protected write
- completes approval flow

## Tests

Test:
- registry
- tool discovery filtering
- JWT
- RBAC
- argument policies
- SQL read-only enforcement
- approval state machine
- audit events
- untrusted server rejection
- cross-role isolation
- end-to-end client flow

## Deliverables

- monorepo
- Docker Compose
- migrations
- seed scripts
- `.env.example`
- Makefile
- demo client
- README
- Mermaid architecture
- threat model
- policy documentation
- demo script
- API documentation

## Acceptance criteria

A reviewer can:
1. start all services
2. log in as multiple roles
3. see different MCP tools
4. successfully invoke allowed reads
5. have a forbidden call blocked
6. submit a write requiring approval
7. approve it as manager
8. see execution occur
9. inspect immutable audit history
10. run automated tests

Maintain `PLAN.md`, `TASKS.md`, and `FINAL_STATUS.md`. Build the complete application.

---

# 7. P18 — Durable Agent Runtime with Temporal

## CODEX MASTER PROMPT

Build a complete **Durable Agent Runtime** that demonstrates how a long-running AI agent survives worker crashes, process restarts, transient tool failures, and human approval delays without duplicating side effects.

Use Temporal as the durable workflow engine.

The project must prove durability with failure injection, not just show Temporal configuration.

## Core concept

Build a sample long-running operations workflow:

**Receive case → gather evidence → retrieve context → agent proposes action → approval checkpoint → perform action → verify → finalize**

The domain can be a synthetic IT operations/change workflow so it is easy to demo safely.

## Durability requirements

Implement:
- Temporal workflow/activity split
- deterministic workflows
- external side effects only in activities
- idempotency keys derived from `(workflow_id, step_id)`
- activity retry policies
- timeouts
- human approval through Temporal signal/update mechanism
- cancellation
- resume after worker restart
- workflow versioning strategy
- durable result/event history

Do not call nondeterministic APIs directly from workflow code.

No wall clock, random values, or direct network calls inside deterministic workflow logic unless using Temporal-safe mechanisms.

## Agent integration

Use LangGraph or a lightweight explicit state machine inside appropriate activities.

Persist compact, safe state rather than hidden chain-of-thought.

Agent capabilities:
- classify case
- retrieve supporting data
- propose plan
- generate structured action request
- summarize final result

## Side-effect service

Create a safe mock external system representing state-changing work, such as:
- create change record
- update service configuration flag
- restart synthetic service
- mark remediation complete

Every operation must require an idempotency key.

The service must record how many times each side effect actually occurred.

## Failure injection

Build commands/UI controls to:
- kill agent worker mid-run
- kill Temporal worker mid-run
- force tool timeout
- force transient tool error
- delay approval
- reject approval
- duplicate signal attempt
- restart application services

The workflow must recover correctly.

## Stack

- Temporal
- Python
- FastAPI
- PostgreSQL for application metadata
- React/Next.js
- Docker Compose
- LangGraph if useful
- pytest
- Temporal test utilities

## UI

Show:
- workflows
- current stage
- status
- pending approvals
- event timeline
- retries
- activity attempts
- side-effect IDs
- final outcome

Provide buttons for safe failure injection.

Do not expose raw hidden model reasoning.

## Benchmark

Create an automated resilience benchmark that runs many workflows with injected failures.

Target:
- 100% recoverable-workflow completion for supported injected transient failures
- zero duplicate committed side effects
- report retry overhead
- report total duration
- report idle cost estimate
- report failure/recovery counts

Make benchmark size configurable and support 200 injected-failure runs.

## Replay safety

Create automated tests that:
- replay workflow histories
- verify deterministic behavior
- verify versioned workflow changes do not break existing histories where supported

Document workflow evolution rules.

## Data model

Application DB can store:
- case metadata
- user-facing workflow mappings
- approvals
- model usage
- benchmark runs
- audit events

Temporal remains the authoritative durable execution history.

## Security

- RBAC for approvals
- auth on workflow actions
- no unrestricted shell tools
- allowlisted side effects
- no secrets in workflow history
- redaction where needed
- audit of approval identity

## Documentation

Create:
- README
- Temporal architecture
- workflow determinism guide
- idempotency design
- failure-injection guide
- benchmark guide
- production deployment gaps

## Acceptance criteria

Reviewer can:
1. start stack
2. launch workflow
3. kill a worker during execution
4. restart worker
5. see workflow continue
6. pause at approval
7. approve from UI
8. force transient side-effect failure
9. observe retry
10. inspect side-effect service and confirm action occurred once
11. run resilience benchmark
12. run replay tests

Maintain `PLAN.md`, `TASKS.md`, and `FINAL_STATUS.md`. Do not stop until crash recovery and zero-duplicate behavior are demonstrated.

---

# 8. P6 — Security Alert Triage + Detection Rule Drafting

## CODEX MASTER PROMPT

Build a complete defensive cybersecurity application named **Security Alert Triage + Detection Rule Drafting**.

The system must ingest security alerts, enrich them using deterministic sources, map relevant behavior to MITRE ATT&CK through a verified lookup service, prioritize alerts, assemble evidence, and draft defensive detection rules for analyst review.

This is a blue-team application. Do not implement offensive payloads, exploitation, credential theft, persistence mechanisms, or autonomous attack actions.

The model must reason over verified evidence; it must not invent ATT&CK technique IDs from memory.

## Stack

- Python
- FastAPI
- LangGraph
- Elasticsearch or OpenSearch
- PostgreSQL
- React/Next.js
- Docker Compose
- a deterministic MITRE ATT&CK lookup service exposed as MCP or typed tool
- pytest
- Playwright

## Alert inputs

Support seeded/synthetic examples from:
- Windows authentication events
- cloud sign-in events
- web/application alerts
- endpoint alerts
- network IDS-style alerts

Create a normalized alert schema.

Do not require real production logs.

## Workflow

1. ingest alert
2. normalize
3. deduplicate/correlate
4. enrich:
   - asset context
   - user context
   - known IP/domain reputation from mock/local data
   - recent related events
5. deterministic ATT&CK lookup
6. severity/risk score
7. agent creates concise investigation summary
8. agent proposes likely benign/malicious/needs-review classification
9. draft detection rule
10. analyst review/approve/edit/reject
11. store feedback for metrics

## MITRE service

Maintain a curated local ATT&CK dataset.

Expose deterministic queries:
- search technique
- technique by ID
- tactics
- mitigations/detection references where present

The LLM must use returned IDs only.

Add validation that rejects unknown technique IDs.

## Detection rule drafting

Draft defensive rules in one or more formats:
- Sigma
- KQL-like
- Elasticsearch query/EQL style

Rules must remain drafts until human approval.

Implement syntax/schema validation where practical.

Never auto-deploy detection rules.

## UI

Pages:
- alert queue
- alert detail
- evidence/enrichment
- ATT&CK mapping
- draft rule
- analyst review
- metrics
- scenario evaluation

Show why a severity/mapping was chosen using evidence references, not hidden reasoning.

## Evaluation dataset

Create named synthetic scenarios including:
- repeated failed logins
- impossible travel style sign-in anomaly
- benign admin activity
- service account noise
- suspicious PowerShell-like command alert metadata without executing anything
- web scanning noise
- known test events
- true-positive and false-positive cases

Measure:
- ATT&CK mapping accuracy
- severity accuracy
- classification precision/recall
- false-positive rate on benign cases
- rule acceptance rate
- rule syntax validity
- unsupported claim rate

## Security

- read-only analytical tools
- role separation: analyst/admin
- no offensive tool execution
- strict input schemas
- log sanitization
- secret redaction
- prompt-injection defense for untrusted alert fields
- audit log
- rate limiting
- model output validation

## Tests

Test:
- normalization
- enrichment
- ATT&CK ID validation
- triage graph
- severity rules
- rule parser/validator
- analyst workflow
- API
- scenario evaluation
- prompt-injection resilience
- dashboard E2E

## Deliverables

- Docker Compose
- seeded security dataset
- MITRE lookup service
- `.env.example`
- migrations
- Makefile
- README
- architecture
- threat model
- evaluation report
- demo script

## Acceptance criteria

Reviewer can:
- ingest/choose a seeded alert
- see normalized data
- see enrichment
- see verified ATT&CK mapping
- inspect triage result
- generate a draft defensive rule
- edit/approve/reject it
- run scenario evaluation
- confirm invalid ATT&CK IDs are blocked
- inspect audit logs

Maintain `PLAN.md`, `TASKS.md`, and `FINAL_STATUS.md`. Finish the whole defensive application and its tests.

---

# 9. P14 — Voice L1 Support Agent

## CODEX MASTER PROMPT

Build a complete real-time **Voice L1 Support Agent** for enterprise IT helpdesk.

The application must provide a browser-based voice conversation, streaming speech-to-text, IT support intent handling, deterministic identity verification before sensitive actions, runbook retrieval, safe ITSM/action-tool integration, streaming text-to-speech, interruption/barge-in handling, and ticket escalation.

The goal is a credible low-latency support demo, not a prerecorded voice chatbot.

## Architecture

Browser microphone
→ real-time media/session layer
→ streaming STT
→ dialog/agent orchestrator
→ identity verification when needed
→ support RAG + tools
→ response
→ streaming TTS
→ browser audio

Use:
- LiveKit or equivalent real-time media layer
- FastAPI
- Python
- LangGraph
- local/default STT adapter such as faster-whisper where feasible
- pluggable cloud STT
- pluggable TTS
- PostgreSQL
- Qdrant or pgvector
- React/Next.js
- Docker Compose

The app must support a text fallback mode when audio dependencies are unavailable.

## Supported support flows

At minimum:
- password reset request
- account unlock
- VPN troubleshooting
- MFA problem
- software access request
- outage query
- unknown issue escalation

## Identity verification

Before account-changing actions:
1. collect employee identifier
2. call deterministic user lookup
3. run a safe demo OTP/verification flow
4. store verification status and expiry
5. only then permit sensitive tool calls

The LLM must not decide identity validity.

## Voice UX

Implement:
- live transcript
- agent transcript
- partial/final transcript state
- push-to-talk or open-mic mode
- barge-in/interruption
- turn detection
- mute/end call
- reconnect handling where practical
- visible action confirmations
- ticket number on escalation

## Latency instrumentation

Measure stage-by-stage:
- audio capture/transport
- STT
- intent/LLM
- retrieval/tools
- TTS
- total perceived response latency

Expose p50/p95 dashboard.

Optimize for a strong local POC and document bottlenecks.

## Indian-English evaluation

Create a small safe evaluation framework for:
- Indian-English support phrases
- common IT acronyms
- names of support concepts
- noisy audio samples if locally generated/provided

Do not claim accent performance without measurement.

Create scripts and schema so a larger user-provided test set can be added.

Metrics:
- word error rate
- intent accuracy
- end-to-end task success
- latency
- containment/escalation
- verification failure rate

## RAG

Seed IT runbooks and support knowledge.

All procedural support advice must be grounded in retrieved content.

Show citations in the transcript/detail view.

## ITSM

Provide mock ITSM adapter so the entire app works without enterprise credentials.

Create tickets with:
- transcript summary
- intent
- troubleshooting performed
- verification state
- citations
- tool results

## Dashboard

Show:
- calls
- containment
- escalation
- average call length
- p50/p95 latency
- STT WER results
- intent success
- top intents
- verification failures
- latest tickets

## Security/privacy

- explicit microphone permission
- no hidden recording
- clear session recording/transcript setting
- configurable transcript retention
- secret redaction
- no sensitive identity data sent unnecessarily to LLM
- deterministic verification
- allowlisted tools
- audit logs
- authentication for admin dashboard

## Testing

Include:
- text-mode deterministic E2E tests
- agent tests
- identity verification tests
- RAG tests
- ITSM tests
- latency instrumentation tests
- audio component tests where feasible
- browser E2E for session start/end and text fallback
- mock STT/TTS for CI

## Deliverables

- Docker setup
- `.env.example`
- Makefile
- seeded knowledge
- mock user directory
- mock ITSM
- README
- architecture
- voice pipeline guide
- latency report
- evaluation guide
- demo script

## Acceptance criteria

Reviewer can:
1. open browser
2. start support session
3. speak or use text fallback
4. see streaming/live transcript
5. request account-sensitive action
6. complete deterministic demo identity verification
7. execute safe action
8. interrupt agent speech where supported
9. escalate an unresolved issue
10. see ticket and dashboard metrics
11. run tests/evaluation

Maintain `PLAN.md`, `TASKS.md`, and `FINAL_STATUS.md`. Do not stop until the main end-to-end flows are usable.

---

# 10. P28 — Multilingual Support Agent for Indian Languages

## CODEX MASTER PROMPT

Build a complete **Multilingual Enterprise Support Agent** optimized for Indian-language support, especially English, Tamil, Romanised Tamil, Hindi, and Romanised Hindi.

The product must demonstrate that multilingual support is an engineering/evaluation problem, not simply "ask the LLM to answer in Tamil."

The application must detect language and script, normalize transliterated input, retrieve enterprise knowledge cross-lingually, generate grounded answers in the user's preferred language/script, and evaluate competing retrieval architectures.

## Main flows

Examples:
- "VPN connect aagala"
- "password reset panna mudiyala"
- Tamil-script support question
- Hindi Devanagari question
- Romanised Hindi question
- English/Hindi or English/Tamil code-switching
- mixed technical terms such as VPN, MFA, Outlook, Wi-Fi

System should:
1. detect language(s)
2. detect script
3. identify code-switching
4. normalize/transliterate where beneficial
5. preserve original query
6. retrieve grounded support content
7. answer in matching/preferred language
8. preserve technical terms where translation would reduce clarity
9. provide citations
10. escalate unsupported questions

## Compare two architectures

Implement both:

### Architecture A — Translate then retrieve
Input
→ language detection
→ translate/normalize to English
→ English retrieval
→ answer
→ translate back

### Architecture B — Shared multilingual embedding retrieval
Input
→ normalization
→ multilingual embeddings
→ shared vector retrieval
→ answer in target language

Allow experiments comparing the two.

## Stack

- FastAPI
- Python
- React/Next.js
- PostgreSQL
- Qdrant or pgvector
- bge-m3 or another suitable multilingual embedding model through adapter
- AI4Bharat-compatible transliteration/translation adapter where available
- provider-agnostic LLM layer
- Docker Compose
- pytest
- Playwright

If a heavyweight model cannot run in the environment, implement a clean service adapter plus lightweight fallback/mock so the project remains fully runnable.

## Knowledge base

Seed English enterprise IT support content.

Also add a smaller set of approved Tamil/Hindi variants to test multilingual behavior.

Store:
- document language
- canonical document ID
- translation relationship
- source
- version
- metadata

Prevent conflicting translations from silently overriding canonical content.

## Normalization

Build explicit pipeline for:
- Unicode normalization
- language detection
- script detection
- Romanised Tamil normalization
- Romanised Hindi normalization
- code-switch token handling
- common IT acronym preservation
- transliteration alternatives

Keep original and normalized forms for evaluation/debugging.

## UI

Chat interface with:
- language indicator
- detected script
- optional manual language override
- original user text
- answer
- citations
- optional "show normalized query" debug view
- escalation

Admin/evaluation dashboard:
- accuracy by language
- accuracy by script
- code-switch performance
- retrieval architecture comparison
- latency
- cost
- citation coverage
- low-confidence cases

## Evaluation dataset

Create a purpose-built 300-query synthetic/curated mixed-language test set.

Include categories:
- English
- Tamil script
- Romanised Tamil
- Hindi script
- Romanised Hindi
- English + Tamil
- English + Hindi
- technical acronym-heavy
- typo/noisy input
- unanswerable questions

Each test case should contain:
- input
- language labels
- script labels
- canonical intent
- answerability
- expected source IDs
- acceptable answer properties

Do not fabricate performance numbers.

## Metrics

Measure:
- retrieval recall@k
- source hit rate
- answer correctness
- faithfulness
- intent accuracy
- language match
- transliteration/normalization quality proxy
- citation coverage
- latency
- cost

Report results separately by language/script. Do not hide weak categories in one aggregate score.

## Back-translation quality check

For generated non-English answers:
- optionally back-translate for semantic consistency checking
- flag large inconsistency
- do not blindly replace original answer from the check

## Escalation

Low evidence or low confidence:
- ask a clarification when appropriate
- otherwise create a mock support ticket containing original + normalized query and retrieval attempts

## Security

- no user PII needed for seeded demo
- strict output grounding
- prompt-injection protection
- safe rendering
- audit logs
- configurable retention

## Testing

Include:
- normalization tests
- script detection tests
- Romanised input tests
- retrieval tests
- architecture A/B tests
- API
- UI
- evaluation runner
- deterministic CI mode

## Deliverables

- Docker setup
- `.env.example`
- Makefile
- 300-query evaluation dataset
- seeded knowledge
- README
- architecture
- language pipeline documentation
- evaluation methodology
- comparison report template
- demo script

## Acceptance criteria

Reviewer can:
1. ask the same IT question in English, Tamil, Romanised Tamil, Hindi, and Romanised Hindi
2. see correct detection/normalization
3. receive grounded answers with citations
4. switch between retrieval architectures
5. run the 300-query evaluation
6. view metrics split by language/script
7. inspect failures
8. escalate an unsupported query

Maintain `PLAN.md`, `TASKS.md`, and `FINAL_STATUS.md`. Build and verify the full application.

---

# Recommended Codex Usage

For each project:

1. Create a fresh repository/folder.
2. Paste only the relevant project prompt into Codex.
3. Allow Codex to create its `PLAN.md` and `TASKS.md`.
4. Let it implement the application in vertical slices.
5. When a run stops because of context/tool limits, continue with:

> Read `PLAN.md`, `TASKS.md`, `FINAL_STATUS.md` if present, inspect the repository and current test failures, then continue executing the original master prompt. Do not redesign completed working parts unnecessarily. Resume from the highest-priority incomplete acceptance criterion. Run tests, fix failures, and continue until the original acceptance criteria are satisfied.

6. Before considering a project complete, use:

> Perform a final production-POC audit against every acceptance criterion in the original master prompt. Do not rely on TODO comments or previous claims. Start the application from a clean state using only the README, run the main E2E demo, run all automated tests and evaluation commands, fix anything broken, remove critical placeholder implementations, verify no secrets are committed, then update `FINAL_STATUS.md` with evidence of what actually passed.

