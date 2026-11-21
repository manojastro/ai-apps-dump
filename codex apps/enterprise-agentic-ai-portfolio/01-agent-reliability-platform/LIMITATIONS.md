# Limitations

- **Synthetic source:** traces and artifact outcomes are deterministic fixtures rather than LangGraph, MCP, or vendor telemetry.
- **Mock reasoning:** RCA is typed and evidence-grounded but rule-synthesized. The OpenAI-compatible environment settings are reserved for a future provider adapter.
- **Synthetic version executions:** the local release gate accepts only its server-created, registered deterministic executor and runs nine cases. Registry artifact digests and public nonce/run/evidence hashes are identity and consistency bindings, not cryptographic proof of external execution. The `BenchmarkRunner` interface documents a future signed remote-attestation path, but no verifier/trust store is implemented and all external runners fail closed.
- **Local execution only:** remediation changes an action-specific, versioned synthetic policy value in SQLite and validates apply and rollback through a separate read-only repository; it does not modify a deployed agent.
- **SQLite concurrency:** WAL improves local behavior, but this design is not intended for multiple API replicas or high ingest volume.
- **Immutable-style local records:** triggers prevent normal update/delete statements for audit rows and bound approval attestations, but a host administrator can replace the database file. Production needs signed remote append-only storage.
- **Local authentication:** API-key support is intentionally simple and local mode disables it by default. Reviewer identities are not backed by an identity provider.
- **In-process rate limit:** counters do not coordinate across workers and reset on restart.
- **Metrics:** the `/metrics` surface uses a few counters/gauges; it does not provide full OpenTelemetry traces or Prometheus histograms.
- **Cost model:** token price is a fixed synthetic rate and not a live provider price.
- **Dashboard:** optimized for demonstration, with no pagination controls, live streaming, or WCAG audit.

These constraints are visible in the UI (`MOCK`) and `/api/v1/platform`; the POC does not present synthetic outcomes as production measurements.
