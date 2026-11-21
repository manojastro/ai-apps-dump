# Implementation status

Status: **incomplete; local prototype only**. Do not use for real business transactions.

## Implemented
- Deterministic Decimal invoice comparison and a SQLite-backed local case store.
- Demo invoice and order records, duplicate intake protection, record-scoped synthetic contact checks, evidence snapshots, workflow events, approval, rejection, and requests for reinvestigation.
- Transactional mock exception/order writes and outbound storage after approval. Version and evidence checks reject stale approval; duplicate approval cannot repeat execution.
- FastAPI endpoints guarded by an explicitly configured bearer token; the API is restricted to the demo tenant and has no production identity or role management.

## Verified
- `PYTHONPATH=backend .venv/Scripts/python -m pytest backend/tests -q`: 11 passed, one dependency deprecation warning, on 2026-11-04. This includes local store and API tests, not complete end-to-end product verification.

## Critical remaining work
- Real authentication, RBAC, trusted email ingestion and sender verification. An email address supplied in a request is spoofable; current contact checks are demo-only.
- Full relational enterprise schema, migrations, PostgreSQL, tenant isolation across all resources, comprehensive scenarios and versioned policy rules.
- Actual MCP communication and servers; persistent LangGraph orchestration; provider abstraction and external provider; structured evidence, claim verification, risk scoring and complete order feasibility.
- Approval editing and granular permissions, complete audit and failure recovery, robust idempotency, concurrency tests and integration tests.
- React dashboard, all requested screens and browser tests, evaluation dataset and metrics, observability, user documentation.
- Deployment work intentionally deferred at user request. Docker daemon was unavailable when checked.

The current code is not production-ready and does not satisfy the master brief. The seeded order date is static and the simplified delivery check is not a real logistics feasibility assessment.

## Latest core work — 2026-11-04
- Added conservative handling of multiple record identifiers, negated delivery requests and order-status messages containing dates. Approval now checks order evidence for changes even when the action is only to send a response, and blocks delivery dates that have passed.
- Added a small SQLite-checkpointed LangGraph investigation wrapper and a restart test for the authoritative case store. The wrapper is experimental, has one node, is not connected to the API, and does not implement the required full graph or approval interrupt.
- Verification: `PYTHONPATH=backend .venv/Scripts/python -m pytest backend/tests -q` produced 18 passed with one dependency deprecation warning. The broad outstanding requirements above remain.

## Latest work — UI and MCP prototype
- Added a React/Vite local workspace with case intake, search, status filters, evidence, audit history, approval, rejection, reinvestigation, and stored outbound display. Dashboard numbers are calculated from stored cases.
- Added a read-only ERP MCP server using real stdio communication, with a process-scoped demo principal and an integration test. It is not yet used by the investigation workflow; CRM/logistics MCP servers and write controls remain outstanding.
- Browser-tested both synthetic case flows through approval and stored outbound response. The confirmed order message is generated only after the mock update succeeds in the same transaction.
- Verification: 21 backend tests passed with one dependency warning; frontend TypeScript and Vite production build passed.
- Remaining gaps listed above still apply. In particular, the UI is a prototype rather than the complete nine-page product, and the graph and MCP server are not wired into its workflow. Deployment remains deferred.

## Deployment audit — 2026-11-04
- Added Dockerfiles, an nginx reverse proxy, a persistent SQLite volume, a backend health check, a loopback-only frontend port and required token configuration for the existing prototype.
- `docker compose config --quiet` passed. Container build/start was not tested: Docker Desktop's daemon was unavailable. This setup is for local synthetic demos only and is not production deployment readiness.
- Current verification: 21 backend tests passed with one deprecation warning; frontend build passed; `pip check` passed; `npm audit --omit=dev --audit-level=high` found 0 vulnerabilities.
- Required feature gaps above remain. In particular, production identity and tenant controls, the full business scenarios, wired MCP and LangGraph execution, production database and migrations, and the complete UI/evaluation/observability systems have not been delivered or verified.

## Local deployment — 2026-11-04
Docker images built and both services started on localhost port 18080. The backend reported healthy; the frontend returned HTTP 200 and the authenticated dashboard responded through the proxy. This verifies local startup only; the missing production and feature requirements above remain unresolved. The reviewer token is stored in the local ignored `.env` file.

## Mail reporting dashboard
- Added an authenticated tenant-scoped report of local incoming cases and outbound messages with date, direction and text filters, daily counts, case links and CSV export. Outbound is explicitly labeled stored, not sent.
- Verified the endpoint, tenant scoping and 22 backend tests; production frontend build passed. Browser-tested a synthetic case through incoming and stored outbound reporting. Local Docker services were rebuilt with the change.
- The app still does not connect to a mailbox or send emails; the report cannot show real mailbox traffic until those integrations are implemented.
