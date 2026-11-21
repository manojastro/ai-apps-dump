# Procurement Navigator

A portfolio project demonstrating a **bounded browser agent for a business workflow**: it compares
supplier offers by operating three supplier web portals, verifies them with deterministic purchasing
rules, asks a human approver to approve one exact purchase, and then completes a **simulated** order
with receipt verification and unknown-outcome reconciliation.

> Everything here is synthetic. The three suppliers (Alpha Supply, Beta Devices, Gamma Trade), brands,
> prices, the 18% tax rate and delivery times are fixtures. No real accounts, no money movement.
> Fixture mode labels every model decision as **simulated**.

## What it demonstrates

* **Tool selection and browser observation** — typed Playwright tools using accessibility semantics
  across three differently built portals (tables vs. cards vs. B2B sidebar; tax-inclusive vs. exclusive;
  per-order vs. per-unit freight), including a redesigned layout that breaks fixed selectors.
* **Verification** — Decimal landed-cost recomputation, 19 hard policy rules, a verifier that rejects a
  planted cheaper 8 GB recommendation with the exact failed rule, and a tax-driven budget breach.
* **Control boundary** — approval is an authenticated approver action bound to a SHA-256 purchase
  fingerprint; any material change (e.g. a post-approval price rise) invalidates it and the UI shows
  what changed. Page text ("ignore the budget…") and model output cannot authorize anything.
* **Durable execution and recovery** — LangGraph with Postgres checkpoints, job leases, heartbeats,
  per-run advisory lock, worker-restart resume, session-expiry re-login, transient-failure retries,
  human handoff for MFA.
* **Safe external actions** — order ledger with database-enforced transitions, supplier idempotency
  tokens, timeout → `unknown` → reconciliation from order history, exactly one mock order under
  duplicate delivery.
* **Security** — server-side sessions, CSRF, role checks, PostgreSQL row-level security with a non-owner
  runtime role, egress allowlist, isolated encrypted browser sessions, redaction, append-only audit.

## Quick start (offline demo mode)

Prerequisites: Docker, [uv](https://docs.astral.sh/uv/) ≥ 0.11, Node.js 22.

**Windows (PowerShell + Docker Desktop)**

```powershell
./scripts/dev.ps1 setup
./scripts/dev.ps1 start
```

**Ubuntu (Docker Engine)**

```bash
scripts/dev.sh setup
scripts/dev.sh start
```

Open http://localhost:5273. Demo users (created by `python -m procnav.manage seed`): `requester@acme.test`,
`approver@acme.test`, `admin@acme.test`, `viewer@acme.test` (and the same for `globex` as a second
tenant). The development password is `procnav-demo` unless `DEMO_PASSWORD` is set; production seeding
generates a random one.

Or run everything in containers: `cp .env.example .env && docker compose up -d --build`, then
http://127.0.0.1:8300.

Follow [docs/demo.md](docs/demo.md) for the five-minute demo and the timeout-reconciliation demo.

## Configure a real model

```bash
MODEL_MODE=real
MODEL_API_KEY=<Anthropic API key>
MODEL_NAME=claude-opus-5-5      # default
MAX_RUN_COST=1.00               # USD ceiling per run
```

The Claude adapter uses structured outputs, low effort, server-side refusal fallback, and optional
screenshot understanding for recovery. Real-model mode uses the same tools, validation, graph and
database; page content is passed as untrusted data. In containers add `-f docker-compose.real-model.yml`
for model-API egress.

## Reproduce the browser benchmark

```bash
# portals running (python -m mockportals.main), no dev worker running
cd backend
uv run python -m procnav.evals.run                       # fixture mode: bounded, single_pass, fixed_selector
uv run python -m procnav.evals.run --mode real --workflows bounded   # optional, spends money
```

Results go to `evals/results/*.json` and the *Evaluation* page. Method and latest numbers:
[docs/evaluation.md](docs/evaluation.md).

## Checks

```bash
cd backend && uv run ruff check . && uv run pytest -q -m "not browser"   # unit + API security
cd backend && uv run pytest -q -m browser                                # 18 real browser scenarios
cd mock_portals && uv run pytest -q                                      # supplier portal contract
cd frontend && npm run build
```

## Documentation

| Topic | Document |
|---|---|
| Architecture, workflow diagram, why checkpoints ≠ replay safety | [docs/architecture.md](docs/architecture.md) |
| Typed tool contracts | [docs/tool-contracts.md](docs/tool-contracts.md) |
| Supplier adapter contract; adding a supplier | [docs/supplier-adapter.md](docs/supplier-adapter.md) |
| Policy rules and normalization | [docs/policy.md](docs/policy.md) |
| Approval and order-ledger state machines | [docs/state-machines.md](docs/state-machines.md) |
| Threat model | [docs/threat-model.md](docs/threat-model.md) |
| API and error codes | [docs/api.md](docs/api.md) |
| Runbook: deploy to Ubuntu, backup/restore, migrations, rollback, retention, rotation, failed runs, reconciliation | [docs/runbook.md](docs/runbook.md) |
| Evaluation method and results | [docs/evaluation.md](docs/evaluation.md) |
| Troubleshooting | [docs/troubleshooting.md](docs/troubleshooting.md) |
| Selected versions | [docs/versions.md](docs/versions.md) |
| Implementation status | [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) |

## What the controlled demo validates — and what it does not

Validated (in the mock environment): the browsing, extraction and verification pipeline across three
layouts; that hard-policy violations are blocked; that changed terms invalidate approvals; zero
unapproved and zero duplicate mock purchases under replay, concurrent delivery, timeouts and restarts;
tenant isolation of evidence.

Not validated: arbitrary real supplier sites. A real integration would still need explicit per-site
authorization, a reviewed adapter, a supplier-supported conditional submission contract (or human final
submission), handling of CAPTCHA/MFA by people, legal review of terms of use, real tax rules, ERP
integration, and capacity measurements on production hardware. Local locks alone cannot guarantee
exactly-once execution on an external website.

## Credits

Browser-workflow automation as a category is inspired by [Skyvern](https://www.skyvern.com/)
([source](https://github.com/Skyvern-AI/skyvern)). This project is not affiliated with Skyvern and uses
none of its code or branding; it implements its own Playwright-based tools.

## Resume bullet template

> Built *Procurement Navigator*, a bounded browser agent (Python, FastAPI, LangGraph, Playwright,
> PostgreSQL, React) that compares supplier offers across three web portals, enforces 19 deterministic
> purchasing rules, binds human approvals to purchase fingerprints, and completes simulated orders with
> receipt verification; achieved **[__ %] task completion** across [__] reproducible scenarios
> ([__ %] in real-model mode at $[__] per run), **[__ %] recovery** on layout/session/transient failures,
> and **zero unapproved or duplicate orders** under replay, timeout and concurrent-worker tests.
