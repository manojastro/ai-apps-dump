# Known limitations

This first release does not meet every item in the original full-platform specification.

1. The local SQLite profile is tested. PostgreSQL, Redis/RQ, Collector, Prometheus and Jaeger Compose integration still need end-to-end runtime verification. Docker startup alone is not proof of a functioning engine.
2. No real provider credentials were supplied. Live dynamic tool use, capability compatibility, billing and provider-restart behavior remain unverified. An Anthropic-specific adapter is absent.
3. Automatic reviewed recovery is implemented only for the replay lab. The real-demo CLI has authenticated bounded fault/reset controls, but live proposals are not wired to a reviewed live executor or fresh Prometheus recovery workflow.
4. The benchmark compares fixed scripts. Single-call LLM and iterative-model baselines, real-model replay tests, live-environment evaluations, judge assessment and an automated evaluation assistant are incomplete.
5. Synthetic cases are unreviewed. Process separation keeps labels out of agent input and tools, but there is no hardened OS sandbox protecting controller files from a compromised Python process.
6. The schema keeps hypotheses, tool calls and versions in JSON snapshots instead of fully normalized entities. The initial migration is frozen; future schema changes require new revisions.
7. Authentication is a local single-organization implementation, without SSO or multi-tenant isolation. Rate limiting is process-local. Windows file permissions inherit local ACLs. Configurable evidence retention, session cleanup and stronger audit storage are incomplete.
8. The live agent has fixed time windows and scope templates. Full incident-window selection, richer hypothesis revision/contradiction tracking and baseline normalization require further work.
9. The UI lab uses replay fixtures. Real traffic and faults use the CLI. Automatic alert-to-incident detection is not yet connected.
10. Live CPU testing ran as Windows processes without a container CPU cap. Some reset samples retained errors or high latency; the measurement report preserves this instead of claiming universal recovery.
11. Existing InsightAI uses `xlsx@0.18.5`, with an inherited high-severity npm advisory. ProductionLens does not import that parser. Replacing the original application's workbook support requires separate compatibility validation.
12. No external deployment, push or publication occurred. Prepared CI and deployment instructions are not themselves evidence that those environments were exercised.
