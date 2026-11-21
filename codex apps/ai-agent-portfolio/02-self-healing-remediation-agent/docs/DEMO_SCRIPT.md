# Demo Script

1. Start with `docker compose up --build`; open <http://localhost:3002>.
2. Point out seeded detected/resolved/pending/blocked/rolled-back incidents and Prometheus at port 9092.
3. Inject **CrashLoopBackOff**. Open the detail and show telemetry/runbook references, LOW risk, allowlisted `restart pod`, verified recovery, and full audit.
4. Inject **Bad deployment**. It pauses at `PENDING APPROVAL`. Review evidence, risk, proposed change, and rollback strategy. Add a comment and approve. Refresh and show persisted approval plus resolution.
5. Inject **Excessive latency** with forced failure selected. Show the action succeeded, health verification failed, original cache state was restored, and status is `ROLLED BACK`.
6. Inject **Unsafe remediation**. Show HIGH risk, action outside the allowlist, zero executions, and external-change outcome.
7. Open `/metrics` and the dashboard metric cards.
8. Run `make test` and `make eval`; open `reports/evaluation.md`.
9. Optional real sandbox: run `scripts/create-sandbox.ps1`, inject a fault, inspect namespace-scoped resources, then `scripts/destroy-sandbox.ps1`.

