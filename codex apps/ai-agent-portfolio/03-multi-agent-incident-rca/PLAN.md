# Multi-Agent Incident RCA — Build Plan

Resolved project root: `D:\ai apps dump\codex apps\ai-agent-portfolio\03-multi-agent-incident-rca`

This directory is the sole write boundary for Project 03. No sibling project directories will be modified.

## Architecture

- FastAPI API and supervisor/worker investigation engine in `backend/app`.
- LangGraph supervisor workflow with deterministic local LLM/provider mode and strict, read-only tool adapters.
- PostgreSQL-compatible persistence model with a zero-infrastructure SQLite development/test fallback.
- Neo4j graph adapter with an in-memory development/test fallback.
- Synthetic Prometheus-compatible metrics, structured logs, deployment events, ticket history, and dependency graph for five services.
- Next.js/React enterprise operations console in `frontend`.
- Prometheus scrape configuration, OpenTelemetry-ready instrumentation, structured audit logs, Docker Compose services, and isolated project-specific resources.
- Deterministic 60-case replay dataset, evaluation CLI, JSON/Markdown reports, pytest suite, and three Playwright flows.

## Delivery sequence

1. Scaffold manifests, environment configuration, migrations, and data contracts.
2. Implement synthetic observability environment and immutable evidence store.
3. Implement specialized workers, correlation, ranking, critic, citation gate, and RCA composer.
4. Expose incident, evidence, graph, timeline, hypothesis, RCA, evaluation, health, metrics, and audit APIs.
5. Build the Next.js operations console and all required views.
6. Add deterministic seeds, incident generator, 60 replay cases, evaluation reports, tests, and failure-mode coverage.
7. Add Docker Compose, Make targets, API/architecture/security docs, and demo script.
8. Run available automated checks, correct failures, and record exact results in `FINAL_STATUS.md`.

## Verification strategy

- Compile/import validation for Python sources.
- Fast deterministic pytest suite for workers, routing, correlation, citation enforcement, API, replay, timeouts, RBAC/redaction, and graph behavior.
- Evaluation gate requiring 100% citation coverage and 0 unsupported factual claims.
- Frontend type/lint/build checks where the local runtime supports dependency installation.
- Docker Compose configuration validation where Docker is available.
- Playwright specifications cover incident creation/investigation, evidence/graph exploration, and RCA/evaluation review.

## Safety constraints

- Telemetry adapters are read-only and accept typed, allow-listed query schemas.
- No arbitrary shell-execution tool is exposed to agents.
- Untrusted log/ticket text is redacted, length-bounded, and explicitly wrapped as data before provider calls.
- All evidence IDs are content-addressed and immutable.
- The citation gate rejects factual RCA claims without valid evidence references.
- RBAC protects write/investigation operations; every sensitive action is audited.

