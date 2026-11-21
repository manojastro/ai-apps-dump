# RecoveryGraph progress

Last updated: 2026-09-22. Resumed the interrupted build from browser/deployment verification.

## Completed

- Five simulator scenarios, controlled transformations and ten mandatory deterministic validators.
- Typed LangGraph fan-out/fan-in, bounded remediation, confidence/risk routing and isolated verifier.
- Durable human approval and restart tests, relational audit records and checkpoint persistence.
- FastAPI, filtered hybrid retrieval, configurable providers and node telemetry.
- React console with graph inspection, rejected/passed attempts, evidence, downloads and approval.
- Fixed mobile overflow and stale completed outcomes during incident selection, with regression coverage.
- Fixed retry token/cost accounting; regression test includes usage from both responses.
- Golden report, scripted API demonstration and passing real-browser smoke flow.
- Added Make shortcuts, GitHub Actions, Kubernetes manifests, README, security/deployment guides,
  graph/loop explanations, ADRs, interview guide and measured resume bullets.

## Test results

- Python: 40 passed; one upstream Starlette/AnyIO deprecation warning.
- Ruff: passed. Mypy: passed, 46 source files.
- Frontend: 3 component tests passed using threads; lint and production build passed.
- Initial Vitest fork startup timed out on Windows; the threads run passed.
- Browser: rejection/revision, node inspection, evidence, audit, download, approval and 390px
  mobile overflow assertion passed, with no page errors.
- Golden evaluation: 15/15 expected outcomes, 15/15 top-1 diagnoses, zero false acceptances among
  10 incorrect candidates. 10/15 complete; five intentionally exhaust attempts.
- API demo: attempt 1 rejected, attempt 2 passed, verifier APPROVE, 21 nodes,
  19 passing checks and one rejected check, final COMPLETED. One run took 0.447 seconds;
  timings are machine-dependent. No paid model calls.
- Compose configuration validates. Kubernetes manifests render with `kubectl kustomize`.
- README/documentation local links resolve.

## In progress / acceptance remaining

The native local Graph + Loop milestone is verified. Full deployment acceptance remains open.

## Blocked / limitations

- Docker engine unavailable: image builds, Postgres integration, Jaeger and container browser
  checks have not been verified on this workstation.
- Kubernetes manifests render but have not been deployed; GitHub Actions has not run on GitHub.
- Live OpenAI-compatible/Azure evaluation requires credentials. In-memory evaluation checkpoints
  emit type-registration warnings; durable stores already have explicit reconstruction allowlists.
- Single backend process; no distributed execution ownership or production identity/RBAC.

## Next

1. On a Docker host run `docker compose up --build -d`, then
   `docker compose exec -T backend python scripts/postgres_smoke.py`.
2. Run `uv run python scripts/browser_smoke.py --url http://127.0.0.1:8080`.
3. Run GitHub Actions and inspect container integration results.
4. Optionally configure real provider credentials and run the explicit online evaluation.
