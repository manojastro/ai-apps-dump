# Local setup

Prerequisites: Python tooling `uv` (≥0.11), Node.js 24+, npm. Docker is optional.

## Option A — no Docker (verified on Windows 11)

```bash
cd engine
uv sync --all-extras
uv run python -m spreadlens.devdb
uv run alembic upgrade head
uv run python -m spreadlens.seed
uv run uvicorn spreadlens.main:app --port 8000
```

`spreadlens.devdb` starts an embedded PostgreSQL 16 (the `pgserver` dev dependency) under `engine/data/pg-dev`,
creates the `spreadlens` and `spreadlens_test` databases and writes their URLs to `engine/.env`. It is safe to
run again (reuses the running server). The API process also runs the background worker
(`SPREADLENS_RUN_WORKER_IN_API=true`).

In a second terminal:

```bash
cd web
npm install
npm run dev
```

Open http://localhost:3000 → sign in as `analyst@demo.local`, `reviewer@demo.local` or `admin@demo.local` with the
password in `SPREADLENS_SEED_PASSWORD` (default `spreadlens-demo`, **local demo only**). A second workspace user,
`other@demo.local`, demonstrates tenant isolation.

To preload the two bundled synthetic reports (FY2025, and FY2026 with restated comparatives):

```bash
cd engine && uv run python -m spreadlens.seed --demo
```

## Option B — Docker Compose

```bash
docker compose up --build
```

Postgres on 5433, engine on 8000, separate worker, web on 3000. Migrations and seeding run in the `migrate` service.

## Live mode (eve agents, needs a Vercel AI Gateway key)

```bash
cd agent-runtime && npm install && npm run build
```

Set `AI_GATEWAY_API_KEY`, `EVE_SERVICE_TOKEN` and `SPREADLENS_AGENT_TOOL_TOKEN` in your shell, then start all five
agents (ports 3101–3105):

```bash
cd agent-runtime && npm start
```

In `engine/.env` set `SPREADLENS_AGENT_MODE=live`, `SPREADLENS_EVE_SERVICE_TOKEN` (= `EVE_SERVICE_TOKEN`) and
`SPREADLENS_AGENT_TOOL_TOKEN`, then restart the engine. The UI header switches to "LIVE processing". With Compose:
`docker compose --profile live up --build`. Model choice: `SPREADLENS_EVE_MODEL` (AI Gateway id) or per agent,
e.g. `SPREADLENS_EVE_MODEL_FINANCIAL_MAPPING`. Check each agent with `npm run info`.

## Tests

```bash
cd engine && uv run pytest
```

Unit + integration + security + durability + evaluation thresholds (~3 minutes; uses `spreadlens_test` and a
separate `spreadlens_eval` database). Scanned-PDF OCR test (slow, ~80 s):

```bash
cd engine && uv run pytest -m ocr
```

Evaluation report (writes `engine/eval/last_report.json`):

```bash
cd engine && uv run python -m eval.run_eval
```

Browser tests (engine on :8000 and web on :3000 running, seeded):

```bash
cd web && npx playwright install chromium && npm run test:e2e
```

Regenerate synthetic fixtures:

```bash
cd engine && uv run python -m fixtures.generate
```
