# Architecture Decision Records

Each ADR records one decision: the context, the options, the choice, and its consequences. Start new ADRs from [the template](0000-template.md). An accepted ADR is never edited to change its decision; a new ADR supersedes it instead.

Every ADR that depends on an external API cites the doc URL, the date printed on the page, and the date it was read (rule 11 in [CLAUDE.md](../../CLAUDE.md)).

| # | Decision | Status |
|---|---|---|
| [0001](0001-platform-constraints-and-toolchain.md) | Platform constraints and toolchain | Accepted |
| [0002](0002-ports-and-adapters.md) | Ports and adapters: one agent, two backends | Accepted |
| [0003](0003-local-backend-postgres.md) | Local backend: Postgres + pgvector in Docker | Accepted |
| [0004](0004-databricks-vs-snowflake.md) | Databricks as the data and AI platform | Accepted |
| [0005](0005-retrieval-and-embeddings.md) | Retrieval: section chunks, scoped hybrid search, abstention | Accepted |
| [0006](0006-langgraph.md) | LangGraph for the agent | Accepted |
| [0007](0007-running-the-agent-on-databricks.md) | Running the agent on Databricks | Accepted (serving deferred) |
| [0008](0008-checkpointer.md) | Checkpointer: SQLite locally, Postgres or Lakebase hosted | Accepted (hosted pending) |
| [0009](0009-sandbox-erp.md) | A SIMULATED sandbox ERP | Accepted |
| [0010](0010-audit-hash-chain.md) | Audit trail as an append-only hash chain | Accepted |
| [0011](0011-policy-python-and-opa.md) | Python evaluator backed by OPA/Rego | Accepted |
