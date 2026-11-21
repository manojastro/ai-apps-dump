# Build status

Updated 2026-09-07 after resuming the interrupted build. This is a working local first release, not completion of every requirement in REQUIREMENTS.md.

## Implemented
- Existing InsightAI preserved at `/insight`; ProductionLens React/Next.js interface at `/`.
- FastAPI sessions, roles, CSRF, bounded payloads, SQLAlchemy persistence and migrations.
- Separate worker, leased jobs, graph checkpoints, replay evidence collection, diagnosis and abstention.
- Exact-action approval/rejection, expiry, preconditions, deduplicated replay execution and fresh scripted recovery evidence.
- 48-case independent scripted benchmark, baseline/candidate comparison, lifecycle subprocess checks and release-policy decisions.
- Three instrumented demo services, actual HTTP traffic, four bounded faults, controller authentication and structured logs.
- Live provider/telemetry adapters and container configuration are implemented but not fully integration-validated.

## Observed evidence
- Full unit/API/workflow/migration suite: 28 passed; one upstream Starlette/AnyIO deprecation warning. Frozen initial migration upgrades, matches the model schema and downgrades in an isolated database.
- Fixed script: 48/48 assertions passed, 16/16 diagnoses correct. Maximum case latency 12,523.74 ms exceeded the 10,000 ms policy limit; release failed. Human review and real-model evidence also missing.
- Regressed script: 44/48 cases passed, 12/16 diagnoses correct, four regressions. Release failed as intended.
- Browser workflow passed: authentication, evidence viewer, rejected and approved recovery, report export, inconclusive result, missing-provider error, a fresh full 48-case benchmark, regression inspection, version comparison/export, and mobile layout/navigation. No browser page errors were observed.
- The fresh browser-triggered benchmark completed without manual resumption: 44/48 cases passed, 12/16 diagnoses correct, four regressions, maximum case latency 10,693.62 ms. Release failed for accuracy, regression and latency; human review and live-model evidence remain missing.
- Final production build, TypeScript, ESLint and Python Ruff checks passed. After rebuilding, focused browser checks passed for rerunning the saved candidate with one trial, actual single-case completion, and a simulated terminal worker failure displayed visibly.
- Real demo measurements: 40-request warmed healthy baseline; 35 requests per fault and recovery sample. Fault errors: payment 35/35, configuration 35/35, pool 35/35, CPU 4/35. Some recovery samples remain noisy; see `docs/evidence/live-demo-measurements.json`.

## Remaining verification / scope
- Setup/deployment documentation and GitHub Actions validation configuration are present; the hosted CI job has not run.
- Docker CLI/desktop startup was attempted, but a working Linux engine has not been established. Container images, PostgreSQL, Redis/RQ, Jaeger and Collector are unverified.
- No provider credentials: genuine live-model outcomes and cost are unverified.
- Live recovery executor, LLM evaluation baselines, evaluation assistant, stronger process isolation, production hardening and configurable retention remain incomplete.
- Inherited InsightAI `xlsx@0.18.5` dependency has an npm audit advisory; ProductionLens does not import it.

## Continuation
Read this file and `tasks/plan.md`. Check existing local processes before starting another stack. Run `npm run bootstrap`, then `npm run dev` if not already running. Read the generated local admin credential from `.productionlens/admin-password.txt`; never print it in logs. Validate with `npm test`, `npm run typecheck`, `npm run lint`, `npm run build`, and `npm run test:browser`. Preserve `docs/evidence` measurements and record new results without inventing missing checks.
