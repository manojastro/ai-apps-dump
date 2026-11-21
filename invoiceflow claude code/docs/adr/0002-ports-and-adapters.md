# ADR 0002: Ports and adapters: one agent, two backends

- **Status:** Accepted
- **Date:** 2026-10-25
- **Deciders:** Manoj (approved the Phase 0 layout and the Phase 1 plan), Claude Code

## Context

The same agent code must run on a laptop (fast tests, CI, no cloud) and on Databricks
(Unity Catalog, AI Search, model serving). If the agent called Postgres or Databricks
directly, every test would need that backend, and "it works on both" would be a claim
rather than a test.

## Options considered

1. **Call each backend directly, with `if backend == ...` branches.** Simple at first.
   Branches spread through the agent, and the two paths drift apart without anyone
   noticing.
2. **An ORM or query layer over both.** Databricks SQL, Unity Catalog functions and AI
   Search don't fit one ORM. It hides the differences instead of testing them.
3. **Ports and adapters.** Small interfaces (`typing.Protocol`) in `src/invoiceflow/ports/`,
   with one implementation per backend in `src/invoiceflow/adapters/`. The agent depends
   only on the interfaces.

## Decision

Option 3. Phase 1 adds the first port, `APDataReader` (read-only: vendor, PO, goods
receipts, invoice, ledger order, prior invoices), with two adapters:

- `adapters/local/memory.py`: in memory, over a generated dataset. Used by unit tests,
  CI and the baseline. Needs no Docker.
- `adapters/local/postgres.py`: the Docker Postgres backend.

The Databricks adapter follows in Phase 2. Missing records raise a structured
`NotFoundError(entity, key)` on every backend, never a bare "error".

Ground-truth labels are **not** reachable through `APDataReader`. They come through a
separate reader that only evaluation code uses, so the agent's tools, which are built on
the port, cannot see the answers.

## Consequences

- The real proof is the **parity test**: every vendor, PO, goods receipt, invoice and
  prior-invoice list must be equal field by field across backends, and the baseline must
  give identical results on each (`tests/integration/test_postgres_backend.py`). Phase 2
  repeats it against Databricks.
- Domain models are frozen Pydantic objects that round money to paise and quantities to
  3 decimals in their validators. Values from JSON, Postgres `numeric` and Python therefore
  compare equal.
- Each new capability (retrieval, LLM, ERP, approvals, audit) gets its own port. That is
  more files, but each one can be explained and tested on its own.

## Evidence and sources

- `uv run pytest -m integration` runs the parity test (needs Docker; see PROGRESS.md for
  the recorded result).
