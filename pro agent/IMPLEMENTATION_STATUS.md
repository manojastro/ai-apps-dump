# Implementation status

Last updated: 2026-10-07. All numbers below come from checks actually run in this repository on the
development machine (Windows 11, Docker Desktop, PostgreSQL 17 container, headless Chromium 1.63).

## Milestones

| Milestone | Status | Gate evidence |
|---|---|---|
| 1. Repo, locks, env validation, containers, migrations, auth, supplier portals, fixtures | Done | `mock_portals/tests/test_portals.py` 8/8: manual browse + order on all three portals, idempotent PO replay, conflicting reuse rejected, quote change rejected atomically, 5 concurrent same-token submissions → 1 order, session expiry, MFA |
| 2. Extraction schemas, browser tools, evidence, normalization, policy engine | Done | `tests/test_quotes_policy.py` 9/9 (all layouts normalize; 8 GB fails `spec.ram_gb`; tax-driven breach fails `budget.landed_total`; pack/delivery/stock/arithmetic/freshness/destination rules) + live tool probe against all three portals |
| 3. Bounded graph, model adapters, fixture mode, durable worker, comparison, retries, cancellation, handoff | Done | Scenario tests reach verified comparison through browser actions; worker restart resumes from checkpoint; MFA pauses for a human |
| 4. Approvals, fingerprints, revalidation, protected submission, idempotent supplier contract, receipt verification, reconciliation | Done | Happy path and timeout replay each produce exactly one mock order; price change before/after approval invalidates and re-approves; duplicate delivery → one order |
| 5. UI, audit, exports, evaluation, CI, tracing, deployment, docs | Done (see open items) | UI → API → worker → browser → supplier → receipt run completed from the browser UI; CSV/PDF exports; benchmark recorded (see docs/evaluation.md) |

## Check results (latest run)

| Check | Result |
|---|---|
| `backend: ruff check .` / `ruff format --check .` | pass / pass |
| `backend: pytest -m "not browser"` (unit + API security) | 19 passed |
| `backend: pytest -m browser` (18 real Chromium scenarios) | 18 passed (16 on first full run; the two failures were real bugs — fixture counter scope and post-login 502 handling — fixed and re-run) |
| `mock_portals: ruff check . && pytest` | pass, 8 passed |
| `frontend: tsc -b && vite build` | pass; oxlint: 0 errors, 2 warnings |
| `alembic check` | no drift |
| Fixture benchmark | see docs/evaluation.md |
| Docker image build | see "Open items" |

## Open items / honest limitations

* **Real-model mode has not been exercised**: no API key was available during development. The Claude
  adapter follows the SDK's documented `beta.messages.parse` + structured outputs + server-side fallback
  interface, but its completion rate and cost are unmeasured. The 85% real-model target is unverified.
* Docker images and the production compose overlay are written but have not been deployed to an Ubuntu
  VM; no domain/TLS deployment was performed (no credentials or domain supplied).
* OIDC (Entra ID) seam is implemented with issuer/audience/tenant checks but untested against a live tenant.
* OpenTelemetry tracing is optional and was not exercised against a collector.
* LangGraph checkpoint tables are not covered by RLS (documented in the threat model).
* The browser pane used for manual UI verification could not render clicks while hidden, so the final
  approval in the manual UI check was submitted through the same authenticated API the UI uses.
* Capacity: only single-run memory was measured (Chromium ≈ 300 MB). No concurrency/capacity claim is made.

## Next steps

1. Run `python -m procnav.evals.run --mode real` with a spending cap and record completion and cost.
2. Build and run `docker compose up --build`, then deploy with `docker-compose.prod.yml` to a VM and run
   the smoke checks in docs/runbook.md.
3. Measure worker resource use under `MAX_CONCURRENT_RUNS=2`.
