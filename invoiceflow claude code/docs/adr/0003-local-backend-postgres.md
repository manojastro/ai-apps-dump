# ADR 0003: Local backend: Postgres + pgvector in Docker

- **Status:** Accepted
- **Date:** 2026-10-25
- **Deciders:** Manoj (chose this default in Phase 0), Claude Code

## Context

The local backend serves unit and integration tests, CI and day-to-day development on
Windows. Later phases also need vector search (Phase 3), a LangGraph checkpointer (Phase 4),
an append-only audit table and an outbox (Phase 4).

## Options considered

1. **Postgres 17 + pgvector in Docker for everything.** One engine and one SQL dialect.
   pgvector covers retrieval, and the LangGraph Postgres checkpointer runs on it. Lakebase,
   the hosted option on Databricks, is also Postgres. Cost: integration tests need Docker.
2. **DuckDB for data, Postgres for everything else.** DuckDB runs in-process and is fast,
   with no Docker for data tests. Cost: two SQL dialects, two loaders, two sets of parity
   problems, and still Docker for the checkpointer.
3. **SQLite.** No vector search and no LangGraph Postgres checkpointer; a weaker Databricks
   stand-in.

## Decision

Option 1: the `pgvector/pgvector:0.8.7-pg17` image (published 2026-10-01, Docker Hub), via
`compose.yaml`. The port is bound to `127.0.0.1` only. The password comes from the
git-ignored `.env`.

Unit tests and the baseline don't need Docker at all: they use the in-memory adapter
(ADR 0002). Only tests marked `integration` need Postgres, and `uv run pytest` skips them
unless they are asked for with `-m integration`.

## Consequences

- Schema in `src/invoiceflow/data/ddl/postgres.sql` has two schemas: `ap` for AP data and
  `eval` for ground truth. The agent's database role will get no grant on `eval` (Phase 4).
- The loader is idempotent. It creates the schema if missing, truncates, and inserts
  everything in one transaction. Running it twice gives identical row counts, and a
  failure part-way leaves the previous load intact.
- Money is `numeric(14,2)` and quantity `numeric(14,3)`, never floating point.
- Windows note: the repo path contains spaces. Compose uses a named volume rather than a
  bind mount, which sidesteps path quoting.

## Evidence and sources

- Image tags checked on Docker Hub (hub.docker.com/v2/repositories/pgvector/pgvector/tags)
  on 2026-10-25: `0.8.7-pg17`, last updated 2026-10-01.
- Integration test results: see PROGRESS.md, Phase 1.
