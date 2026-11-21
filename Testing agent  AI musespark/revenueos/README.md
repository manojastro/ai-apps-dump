# RevenueOS AI

An enterprise revenue intelligence platform. It joins CRM, billing, product usage and support data into one account record, predicts deal outcomes, churn and forecast, and explains the results through an AI copilot.

**Core rule:** models calculate, the LLM explains, and every claim cites its source data.

> All data is synthetic. Every metric below proves the pipeline works on rules planted in the data. None of them say anything about real-world accuracy.

## Status

| Area | Status | Evidence |
|---|---|---|
| Backend, database, ML, forecast | Tested | 98 pytest tests pass against real Postgres 16 + pgvector |
| Frontend | Tested | Type check, production build, 5 Playwright flows pass, reviewed in light and dark mode |
| Copilot plumbing | Tested with a scripted stand-in | Tool loop, scoping, audit, guardrails, 20/20 eval plumbing check |
| **Copilot answer quality** | **Not tested** | No `ANTHROPIC_API_KEY` was available, so no real LLM call has ever been made |
| **`docker compose up`** | **Not tested** | Compose files pass `docker compose config`, but Docker Desktop would not start here, so no image has been built |
| **GitHub Actions CI** | **Not run** | Workflow is written, but the repo has not been pushed |
| No-Docker setup from a clean copy | Tested | Fresh virtualenv and Postgres, full rebuild, 98 tests pass, frontend builds |
| Cloud deployment | Not done | Plan in [docs/deployment_plan.md](docs/deployment_plan.md) |

## Measured results

Run on 2026-11-07 with seed 42 and `DATA_AS_OF=2026-10-31`.

**Win probability** (147 held-out deals, 555 snapshots, split at 2026-05-24)

| Model | AUC (95% interval) | Brier | Precision | Recall |
|---|---|---|---|---|
| LightGBM (selected on validation) | 0.830 (0.756 to 0.888) | 0.167 | 0.756 | 0.783 |
| Logistic regression | 0.836 (0.774 to 0.889) | 0.166 | 0.733 | 0.807 |
| Stage win rate baseline | 0.750 (0.697 to 0.800) | 0.197 | 0.711 | 0.709 |

Both models beat the baseline. Logistic regression edged LightGBM on the test set, within noise. LightGBM stays selected because it won on validation, and the test set must not be used to choose. Calibration is good: the five probability bins predicted 0.14, 0.36, 0.53, 0.73 and 0.87, against observed 0.09, 0.32, 0.55, 0.73 and 0.87.

**Churn within 90 days** (165 accounts, 477 snapshots, 35 positive rows)

| Model | AUC (95% interval) | Top-decile capture |
|---|---|---|
| LightGBM (selected on validation) | 0.943 (0.841 to 0.993) | 28 of 35 (80%) |
| Logistic regression | 0.965 (0.929 to 0.995) | 27 of 35 (77%) |
| Renewal date only baseline | 0.857 (0.785 to 0.911) | 13 of 35 (37%) |

This is a small test set with only 35 positive rows, so treat these as rough.

**Forecast back-test** (walk-forward, 4 quarters, snapshot 14 days into each quarter)

| Quarter | Actual | Model | Model error | Stage-weighted error | Rep commit error | In P10 to P90 |
|---|---|---|---|---|---|---|
| 2025Q4 | $3.11M | $3.18M | 2.3% | 14.6% | 59.5% | Yes |
| 2026Q1 | $4.86M | $4.72M | 2.8% | 21.9% | 38.3% | Yes |
| 2026Q2 | $5.08M | $4.44M | 12.6% | 14.2% | 31.4% | Yes |
| 2026Q3 | $3.31M | $3.46M | 4.5% | 4.4% | 51.7% | Yes |
| **Average** | | | **5.5%** | **13.8%** | **45.3%** | **4 of 4** |

The model beat stage-weighting in three quarters and roughly tied in 2026Q3. "Actual" counts deals visible at the snapshot plus quarter-to-date wins. Deals created and closed later cannot be forecast from pipeline. Four quarters is too few to validate the range, and 4 of 4 inside an 80% range may mean it is a little wide.

**Current quarter (2026Q4):** expected $2.17M, range $1.47M to $2.82M, rep commit $1.49M, stage-weighted $2.02M.

**Retention:** $948,418 at-risk ARR across 18 high-risk accounts, traceable to account ids through `GET /churn/summary`. A test checks that the total matches those accounts.

**Data:** 206 accounts, 600 deals, 1,500 loaded tickets, 1,987 invoices, 60,022 usage rows, 5,776 activities, 1,497 contacts. The second load produced identical counts. The quality report found all injected issues: 6 duplicate groups, 82 null values, 25 orphans, 12 stale deals, 11 impossible dates.

**Performance:** Account 360 page, median 325 ms and max 479 ms over 10 loads, on a local production build.

**Copilot eval:** **not run**, because no API key was available. The pass rate is unknown. `--dry-run` gives 20/20, but that only proves the wiring. A script supplies the answers, so it must not be quoted as a quality result.

## Run it

Prerequisites: Python 3.11 with [uv](https://docs.astral.sh/uv/), Node 22 or newer.

Copy `.env.example` to `.env`, then set `JWT_SECRET` and `DEMO_USER_PASSWORD`. Set `ANTHROPIC_API_KEY` to enable the copilot.

**Option A: no Docker.** This is the tested path. It runs a real embedded PostgreSQL 16 with pgvector.

```bash
cd backend
```

```bash
uv sync
```

```bash
uv run python -m scripts.dev_db
```

```bash
uv run python -m scripts.build_all
```

```bash
uv run uvicorn app.main:app --port 8000
```

In a second terminal:

```bash
cd frontend
```

```bash
npm ci
```

```bash
npm run build
```

```bash
npm run start
```

**Option B: Docker.** Written, but not yet verified.

```bash
docker compose up --build
```

```bash
docker compose exec backend python -m scripts.build_all
```

Open http://localhost:3000. The API docs are at http://localhost:8000/docs.

**Demo logins.** The password is your `DEMO_USER_PASSWORD`.

| Email | Sees |
|---|---|
| `cro@revenueos.example` | All teams |
| `admin@revenueos.example` | All teams, Admin page and audit log |
| `revops@revenueos.example` | All teams, Admin page without audit log |
| `manager1.na@revenueos.example` | North America only |
| `manager1.emea@revenueos.example` | EMEA only |
| `csm.apac@revenueos.example` | APAC only |

## Test it

Backend tests wipe the database named in `TEST_DATABASE_URL`, and refuse to run unless the name contains "test".

```bash
cd backend && uv run pytest
```

```bash
cd backend && uv run ruff check .
```

Browser flows need the app running, with `E2E_PASSWORD` set to your demo password:

```bash
cd frontend && npx playwright install chromium && npm run test:e2e
```

Copilot eval. The first command checks wiring for free. The second calls the API and costs money:

```bash
cd backend && uv run python ../eval/run_eval.py --dry-run
```

```bash
cd backend && uv run python ../eval/run_eval.py
```

`scripts.build_all` is a full demo rebuild. It empties every table, including the audit log. `scripts.load_data` only upserts.

## Why this design, phase by phase

- **Phase 0, setup.** Postgres with pgvector keeps relational data and search in one system. Migrations and CI come first, because adding them later is painful.
- **Phase 1, data.** The generator is a small causal simulation, so models have real patterns to learn. Injected mess is recorded, so tests can prove the quality report finds all of it.
- **Phase 2, Account 360.** One call returns everything, because the value is seeing systems side by side. Citations appear from the start, so the copilot can reuse them.
- **Phase 3, deal intelligence.** Point-in-time features and time-based splits stop the model learning from the future. SHAP finds what mattered, and templates state it using the real value.
- **Phase 4, forecast.** A simulation gives a range, which is more honest than one number. The back-test trains only on the past. Weekly changes reconcile exactly.
- **Phase 5, retention.** A churn label looks 90 days ahead, so training stops 90 days before testing begins. Expansion stays rule-based, because rules are enough and easy to explain.
- **Phase 6, copilot.** The LLM only reaches data through scoped, read-only tools, with no SQL tool. Code checks citations and numbers after each answer, because a prompt alone is a request, not a control.
- **Phase 7, governance.** Scope is enforced once in the backend, and it applies to the API and copilot alike. Role and team are read from the database, so a tampered token grants nothing.

More detail: [architecture](docs/architecture.md), [decisions](docs/decisions.md), [data dictionary](docs/data_dictionary.md), [limitations](docs/limitations.md), [demo script](docs/demo_script.md), [deployment plan](docs/deployment_plan.md), [final report](docs/final_report.md).

## Repo map

```
backend/app/api/        routers: accounts, deals, forecast, churn, copilot, admin, auth
backend/app/core/       config, security, logging, rate limiting
backend/app/db/         models, session, migrations
backend/app/services/   account360, deal_intel, forecast, retention, briefing, scope
backend/app/ml/         features, train_win, train_churn, forecast_sim, explain
backend/app/copilot/    tools, prompts, rag, guardrails, audit, agent
backend/app/connectors/ base interface and CSV connector
backend/app/jobs/       scheduled refresh
backend/scripts/        generate_synthetic_data, load_data, data_quality, build_all, dev_db
backend/tests/          pytest suite
frontend/               Next.js app and Playwright flows
eval/                   20-question copilot test set and scorer
docs/                   architecture, decisions, data dictionary, limitations, demo, deployment
```
