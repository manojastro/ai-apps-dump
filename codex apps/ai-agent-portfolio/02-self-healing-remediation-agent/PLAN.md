# Self-Healing Remediation Agent — Implementation Plan

Resolved project root: `D:\ai apps dump\codex apps\ai-agent-portfolio\02-self-healing-remediation-agent`

## Scope and assumptions

- Build an independently runnable production-style POC entirely within this directory.
- Default runtime uses a deterministic in-memory sandbox so the complete workflow and test suite run without Kubernetes, PostgreSQL, or paid model credentials.
- A Kubernetes adapter and kind bootstrap/manifests provide the real-cluster sandbox path; execution stays constrained to `selfheal-demo` and typed allowlisted actions.
- SQLite persists local incidents and approval decisions. PostgreSQL is configured for the containerized deployment.
- The UI is a React/TypeScript single-page application served separately in development and by Nginx in Compose.

## Milestones

1. Establish project metadata, configuration, schemas, persistence, and seeded incident/runbook data.
2. Implement deterministic evidence collection, runbook retrieval, diagnosis, risk classification, policy, approval, execution, verification, rollback, and audit workflow.
3. Expose health, incident, approval, action, dashboard, metrics, and evaluation APIs.
4. Build the operator dashboard and incident-detail approval experience.
5. Add the 50+ case replay benchmark, unit/API/graph/failure tests, and a critical Playwright flow.
6. Add Docker Compose, local cluster bootstrap/teardown, demo manifests, and safe incident injection helpers.
7. Document architecture, threat model, evaluation, demo, production gaps, and developer commands.
8. Run tests, evaluation, build/static checks, smoke tests, and record truthful final status.

## Verification strategy

- `pytest -q`
- `python -m app.evaluation --output reports/evaluation.json --markdown reports/evaluation.md`
- frontend type/build verification with `npm run build`
- FastAPI smoke test against seeded workflows
- `docker compose config`

