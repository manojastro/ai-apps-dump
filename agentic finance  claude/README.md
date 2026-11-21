# SpreadLens AI — Agentic Financial Spreading and Analyst Review

SpreadLens takes financial statements (digital PDF, scanned PDF, XLSX), extracts every figure **with its exact
source location**, standardises labels, units, periods and scope into a versioned taxonomy, runs
**deterministic** arithmetic checks, queues exceptions for analyst review, records every correction with
before/after values, and produces an Excel workbook and PDF review pack from one immutable, signed-off snapshot.

> Supports analyst review. It does not make lending decisions, and passing arithmetic checks does not prove that
> figures are correct or compliant. Banks, insurers and other specialised financial institutions are unsupported
> for automatic spreading in this version.

## What is in the repository

| Path | What |
|---|---|
| `engine/` | Python 3.12 + FastAPI: extraction (pdfplumber, local RapidOCR, openpyxl), Decimal numeric engine, taxonomy, rules, metrics, workflow coordinator + durable worker, review service, Excel/PDF exports, PostgreSQL schema (Alembic), tests, evaluation |
| `agent-runtime/` | eve workspace with five agents (live mode): document-understanding, table-extraction, financial-mapping, reconciliation, analyst-pack. Typed zod tools call back into the engine |
| `web/` | Next.js 16 + TypeScript + Tailwind: the ten review screens, BFF proxy with httpOnly session cookie, Playwright browser tests |
| `engine/fixtures/` | Synthetic documents (fictional companies) and ground truth |
| `docs/` | Architecture, learning guide, data dictionary, taxonomy & rules, API, setup, deployment, costs & limitations, demo script, evaluation, progress report |
| `docker-compose.yml` | Postgres + engine + worker + web (+ eve agents with `--profile live`) |

## Quick start (no Docker, no credentials)

```bash
cd engine && uv sync --all-extras && uv run python -m spreadlens.devdb && uv run alembic upgrade head && uv run python -m spreadlens.seed
```

```bash
cd engine && uv run uvicorn spreadlens.main:app --port 8000
```

```bash
cd web && npm install && npm run dev
```

Open http://localhost:3000 and sign in as `analyst@demo.local` / `spreadlens-demo` (local demo users only).
Full instructions, Docker Compose and live mode: [docs/local-setup.md](docs/local-setup.md).

## Verified

* 64 engine tests (unit, integration, security, durability, evaluation thresholds) + 1 OCR test — see [docs/progress-report.md](docs/progress-report.md)
* Playwright browser tests: source inspection, correction, approval, downloads
* Synthetic evaluation: every metric at threshold; see [docs/evaluation.md](docs/evaluation.md). Synthetic results are not real-world accuracy.

Start with [docs/learning-guide.md](docs/learning-guide.md) for a plain-English tour.
