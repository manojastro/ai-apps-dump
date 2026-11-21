# Production Hardening Gaps

1. Replace demo bearer/CSRF values with organization OIDC, MFA for approvers, short-lived sessions, and fine-grained tenant/resource authorization.
2. Store policy and runbook versions in a signed, reviewed configuration service; add policy simulation and two-person approval for selected MEDIUM changes.
3. Move action dispatch to a durable queue/workflow engine with transactional outbox, distributed idempotency lock, and worker crash recovery.
4. Replace the synchronous deterministic detector with Alertmanager/Kubernetes watch ingestion, telemetry correlation, and SLO-aware health probes.
5. Add per-tool production Kubernetes adapters, server-side dry-run/admission checks, dedicated workload identity, NetworkPolicy, and an isolated management cluster.
6. Make rollback records immutable and verify every compensating action in chaos tests; escalate through PagerDuty/ITSM on rollback failure.
7. Use managed PostgreSQL with migration tooling, encryption, backups, retention, row-level access controls, and an append-only external audit sink.
8. Put the API behind TLS/WAF/distributed rate limiting; store secrets in a vault and implement systematic telemetry/model redaction.
9. Validate a real provider adapter with adversarial evidence, groundedness, calibrated confidence, latency/cost budgets, and human-reviewed real incidents.
10. Add HA, load/soak testing, browser CI, SBOM/signing, image scanning, dependency pinning, SAST, and disaster-recovery exercises.

