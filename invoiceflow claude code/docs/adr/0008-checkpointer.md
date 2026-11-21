# ADR 0008: Checkpointer: SQLite locally, Postgres or Lakebase hosted

- **Status:** Accepted (hosted choice pending deployment)
- **Date:** 2026-10-25
- **Deciders:** Claude Code; the hosted choice needs Manoj's approval

## Context

Human approval can take days. Paused cases must survive restarts and redeploys.

## Options considered

1. **SQLite (`langgraph-checkpoint-sqlite`).** It's durable on one machine and needs no
   Docker, which suits local development, tests and CI.
2. **Postgres (`langgraph-checkpoint-postgres`).** The standard multi-instance choice, and
   it runs on the local Docker backend.
3. **Lakebase.** Databricks' Postgres. Free Edition includes one project with
   scale-to-zero, which avoids paid Azure Postgres.
4. **Azure Database for PostgreSQL.** Managed, but paid.

## Decision

SQLite locally (`agent/runner.py: sqlite_checkpointer`). The runner accepts any LangGraph
`BaseCheckpointSaver`, so a hosted Postgres or Lakebase saver plugs in without code changes.
The hosted choice waits for deployment, and anything paid needs Manoj's approval.

## Consequences

- Durable resume is proven with SQLite across two processes. Lakebase compatibility is
  **not yet tested** (an ADR 0001 open item).
