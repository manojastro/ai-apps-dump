# Aegis Plan India — Task List

## Phase 1: Foundation
- [x] Task 1: Repo skeleton (gitignore, pyproject, env, docker, CI stub)
- [x] Task 2: FastAPI health/ready + structured logging
- [x] Task 3: Next.js app shell with research-desk visual system

## Phase 2–3: Models + DB
- [x] Task 4: Pydantic domain models + disclaimer metadata
- [x] Task 5: SQLAlchemy entities + Alembic migration

## Phase 4–7: Deterministic core
- [x] Task 6: PII redactor + allowlist + provenance
- [x] Task 7: Mock regulatory/market/universe fixtures
- [x] Task 8: IPS, allocation, loan, emergency, tax, stress engines
- [x] Task 9: Versioned risk-policy rules + veto retry

## Phase 8–10: Research + API
- [x] Task 10: Firecrawl adapter, cache, 429 backoff
- [x] Task 11: LangGraph eight-agent pipeline (mock + live)
- [x] Task 12: REST API, jobs, audit trail

## Phase 11–15: UI + PDF
- [x] Task 13: Onboarding + holdings
- [x] Task 14: War room, compare, plan, sources
- [x] Task 15: ReportLab Financial Action Plan PDF

## Phase 16–18: Quality
- [x] Task 16: pytest assertions + evals fixtures
- [x] Task 17: Frontend tests + Playwright smoke
- [x] Task 18: README, architecture docs, demo polish

## Checkpoints
- [x] Deterministic engine tests pass before agents
- [x] Mock-mode plan generation works via API
- [x] Full UI flow for household fixture #2
- [x] PDF contains disclaimer, timestamps, sources
- [x] Local health/ready + demo plan (Docker Compose file is included; local uvicorn/next verified)
