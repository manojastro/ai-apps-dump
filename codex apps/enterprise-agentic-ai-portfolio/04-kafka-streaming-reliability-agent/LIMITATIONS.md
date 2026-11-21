# Limitations

- The default adapter simulates Kafka state; it does not start brokers or exercise Kafka protocol behavior.
- Scenario after-state is deterministic. Validation demonstrates control flow and evidence semantics, not an actual consumer replay.
- SQLite is appropriate for a single-process demo, not concurrent enterprise control-plane workloads.
- Audit history is append-only by application convention, not cryptographically tamper-evident.
- Authentication is open by default for the zero-configuration demo. Optional API-key mode separates viewer, approver, and executor operations, but static keys are still weaker than production OIDC/workload identity.
- Request metrics are process-local and reset on restart. MTTD/MTTR use labeled simulated clocks rather than broker event timestamps; token metrics are absent because mock reasoning makes no LLM call.
- The frontend is a project-specific dependency-free dashboard, not a Next.js application.
- The `ReasoningProvider` seam exists, but this slice intentionally uses deterministic mock reasoning and makes no LLM call.
- Multiple concurrent failures, Kafka rebalances, exactly-once semantics, ordering constraints, and partial remediation failures need broader simulation and tests.
