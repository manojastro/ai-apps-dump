# Architecture

The workflow follows `plan → collect_evidence → correlate → rank_hypotheses → critic → compose_rca`. When LangGraph is installed the same topology is compiled as a `StateGraph`; deterministic orchestration keeps the offline test path credential-free. Collection uses `asyncio.gather`, with individual timeouts and failure isolation.

Each worker owns exactly one adapter:

| Worker | Permitted tool | Output |
|---|---|---|
| Metrics Investigator | `read_metrics` | Prometheus-style observations |
| Logs Investigator | `read_logs` | Sanitized structured log observations |
| Deployment/Change Investigator | `read_changes` | Deployment/config events |
| Ticket/Incident History Investigator | `read_tickets` | Sanitized history/knowledge observations |

An evidence ID is the uppercase first 12 hexadecimal characters of SHA-256 over canonical source identity and normalized content, prefixed by `EV-`. A collision with different content is rejected. The correlation stage orders observations by source time. The ranker groups independent causal signals and retains distractors. The critic explicitly checks contradiction/recovery evidence and can demote the leader. The composer builds typed claims; only the citation gate can release an RCA.

PostgreSQL stores incidents, complete investigation snapshots, and audits. Neo4j stores component nodes and dependency edges with parameterized Cypher. SQLite and an in-memory graph are development/test fallbacks, not shared with other projects.

Five synthetic services expose `/`, `/healthz`, `/work`, and `/metrics`. Prometheus scrapes them and the API. OpenTelemetry API/SDK dependencies provide the instrumentation boundary for extension to an OTLP collector.

