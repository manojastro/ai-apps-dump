# Procurement Navigator — repository instructions

Read `IMPLEMENTATION_STATUS.md` first, then `docs/architecture.md`.

## Layout
- `backend/` (uv project `procnav`): API, worker, LangGraph workflow, browser tools, policy, ledger, evals.
- `mock_portals/` (uv project): synthetic supplier portals + private fixture control API.
- `frontend/` (npm): React + Vite + Tailwind UI.
- `fixtures/`: synthetic catalog, scenarios (evaluator-only expectations), buyer master data.
- `infra/`, `scripts/`, `docs/`, `evals/results/`.

## Commands
- DB: `docker compose -f docker-compose.dev.yml up -d` (PostgreSQL on 127.0.0.1:55433)
- Migrate/seed: `cd backend && uv run python -m procnav.manage migrate && uv run python -m procnav.manage seed`
- Run: portals `cd mock_portals && uv run python -m mockportals.main`; API `cd backend && uv run uvicorn procnav.api.app:app --port 8300`; worker `uv run python -m procnav.workers.main`; UI `cd frontend && npm run dev`
- Checks: `cd backend && uv run ruff check . && uv run pytest -q -m "not browser"`; browser scenarios `uv run pytest -q -m browser` (portals running, no dev worker competing for jobs); `cd mock_portals && uv run pytest -q`; `cd frontend && npm run build`
- Benchmark: `cd backend && uv run python -m procnav.evals.run` (stop the dev worker first)

## Invariants — do not weaken
- Policy and purchasing logic live in code, never in prompts. Model output is validated, never trusted.
- Approvals bind to a fingerprint; any material change invalidates them.
- Side effects go through the order ledger; a resumed run consults the ledger before any submission.
  Never retry a submission without establishing whether an external order may exist.
- Tenant scope comes from the server session or job row; RLS is forced on tenant tables.
- Browser contexts are isolated per tenant+supplier; egress is limited to configured origins.
- Fixture control APIs are never added to the agent tool registry.
- Alembic autogenerate must not touch LangGraph `checkpoint*` tables (filtered in `alembic/env.py`).
