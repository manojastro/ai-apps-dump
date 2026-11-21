# ADR 0010: Audit trail as an append-only SHA-256 hash chain

- **Status:** Accepted
- **Date:** 2026-10-25
- **Deciders:** Manoj (spec), Claude Code

## Decision

`audit/chain.py` uses one SQLite table. Each entry's hash is SHA-256 over its sequence
number, timestamp, case, event, payload and the previous entry's hash, starting from a
64-zero genesis value. Three properties follow:

- **Append-only.** Triggers reject UPDATE and DELETE.
- **Tamper-evident.** `verify_audit_chain` recomputes every link, so edits made by
  bypassing the triggers (for example, editing the database file) are detected at the
  first bad sequence number.
- **Idempotent.** Each append has a unique `event_key`, so a node that re-runs after a
  crash does not duplicate entries.

Payloads are masked before hashing, so bank numbers never enter the trail. Every decision
also gets an evidence pack (`audit/evidence.py`), whose SHA-256 is recorded in the chain.

## Consequences

- **Tamper-evident, not tamper-proof.** Someone with write access could rewrite the whole
  chain consistently. The production fix is to anchor the head hash somewhere the writer
  cannot change (WORM storage, or a Delta table with restricted grants), which is not done.
- Tested: the chain verifies after runs; a trigger-bypassing edit is detected at sequence 3;
  duplicate appends are no-ops.
