# ADR 0009: A SIMULATED sandbox ERP (vs ERPNext)

- **Status:** Accepted
- **Date:** 2026-10-25
- **Deciders:** Manoj (spec: no real ERP in v1), Claude Code

## Context

The executor needs something to write to that behaves like an ERP in the ways that matter
for safety: idempotent writes, conflicts, retries, and events.

## Options considered

1. **A small FastAPI sandbox** (`services/erp_sandbox`) with idempotency keys and a
   transactional outbox. It is clearly labelled SIMULATED.
2. **ERPNext.** It's realistic but heavy to run, and slow to reset for tests. Its API
   specifics would dominate the project.

## Decision

The sandbox, behind an `ERPClient` port with two adapters:

- **In-process.** Used in tests and on Databricks, where a laptop service is unreachable.
- **HTTP.** Retries reuse the same idempotency key.

The key is `case_id:action:matrix_version[:12]`. ERPNext stays an optional later adapter.

## Consequences

- **No double posting:** a duplicate delivery returns the original decision ("replayed").
  An HTTP retry after a lost response still produces one row. Reusing a key with a
  different payload returns 409. These are tested in `tests/unit/agent/test_agent.py`.
- The decision and its outbox event commit in one transaction. Nothing publishes the
  outbox yet; it exists to show the pattern.
