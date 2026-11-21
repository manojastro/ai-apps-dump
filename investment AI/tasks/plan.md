# Implementation Plan: Aegis Plan India

## Overview

Build a locally runnable, deployable India-focused educational investment research and financial-planning simulator. Deterministic Python owns arithmetic, caps, eligibility, vetoes, and weights. LLMs only summarize and explain. Mock mode (`DATA_MODE=mock`) must complete the full user journey without Firecrawl or LLM credentials.

## Architecture Decisions

- **Monorepo as specified:** FastAPI in `app/`, Next.js App Router in `apps/web/`.
- **PDF:** ReportLab (Windows-friendly; no GTK/Pango required by WeasyPrint).
- **Database:** SQLAlchemy 2.x + Alembic; SQLite local default, PostgreSQL via `DATABASE_URL`.
- **Jobs:** In-process background generation with persisted `plan_jobs` status (no Redis required for local/demo).
- **LLM:** OpenAI-compatible client (`LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`). Defaults target SpaceXAI/xAI (`https://api.x.ai/v1`, `grok-4.5`) when live.
- **Firecrawl:** Official v2 SDK adapter (`scrape`, `scrape_json`, `search`, `extract_multi_page`, `agent_research`) with allowlist, cache, 429 backoff, call budget. Never used in mock mode.
- **Agents:** LangGraph state machine wrapping eight agents; mock mode uses deterministic stubs, never invents rates.
- **Auth:** Session abstraction with a local demo household; no Aadhaar/PAN collection.

## Task List

### Phase 1: Foundation
- [ ] Scaffold repo, Docker, CI skeleton, env, README stub
- [ ] Backend FastAPI health/ready
- [ ] Frontend Next.js landing shell

### Phase 2–7: Core
- [ ] Pydantic domain models
- [ ] SQLAlchemy + Alembic
- [ ] PII redactor, allowlist, provenance types
- [ ] Mock regulatory/market/universe fixtures
- [ ] Deterministic engine (IPS, allocation, loans, emergency, tax, stress)
- [ ] Versioned risk-policy rules

### Phase 8–10: Research + API
- [ ] Firecrawl adapter + cache
- [ ] LangGraph eight-agent pipeline
- [ ] REST API + audit + jobs

### Phase 11–15: Product UI + PDF
- [ ] Onboarding, holdings, research, war room, compare, plan, sources
- [ ] Aegis Financial Action Plan PDF

### Phase 16–18: Quality
- [ ] pytest + frontend tests + evals
- [ ] CI, docs, demo polish

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Live tax/NPS/LRS rules change | High | Snapshot service; mock fixtures labelled MOCK; never hardcode as permanent |
| Firecrawl/LLM unavailable | High | `DATA_MODE=mock` full flow; degraded cache path |
| WeasyPrint on Windows | Med | ReportLab |
| Agent non-determinism | High | Structured Pydantic outputs; Python finalizes weights |

## Open Questions

None blocking. Spec is the source of truth. Mock mode is the demo path.
