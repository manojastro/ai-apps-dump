# Engineering Decisions

## 001 — SQLite over a service database

The POC optimizes for a reviewer running one command without credentials or another container. Standard-library SQLite keeps persistence real and inspectable. Versioned SQL migrations and repository interfaces make the later move to PostgreSQL explicit.

## 002 — Deterministic orchestration first

A custom sequential workflow is sufficient for this bounded state machine and avoids introducing a framework solely for appearance. Components are injected behind small interfaces so a durable graph orchestrator can replace it when retries, checkpoints, or distributed workers justify that cost.

## 003 — Evidence before language reasoning

Detection and independent outcome checks are deterministic. RCA receives only persisted findings/evidence and returns a strict schema. The demo reasoner is deterministic, which makes regression evaluation reproducible and prevents an unavailable provider from breaking the workflow.

## 004 — Zero-build dashboard

A static frontend removes the Node runtime and second dependency graph while retaining a domain-specific UI. It is not a generic admin template: information architecture centers on outcome contracts, RCA evidence, approval, trajectories, and release gates.

## 005 — Simulated remediation

No arbitrary system command is needed for an agent reliability control plane demo. Execution is deliberately limited to catalog-bound, versioned policy actions. The controller persists a policy value, reads the state back independently, calculates checks, and restores the previous snapshot on failure. Simulated unsafe command text exists only inside the trace fixture.

## 006 — Exact scenario labels

The regression dataset asserts exact finding sets rather than merely checking that one expected alert appears. This catches both false negatives and newly introduced false positives.

## 007 — Bind approval to immutable intent

Approval covers a canonical action payload hash and schema version, not just a mutable row identifier. Execution revalidates the row, payload, action catalog, incident, risk, tool, and approval binding. A database trigger makes the protected fields immutable after approval.

## 008 — Trust the local release executor, then derive gates from evidence

The local release gate only invokes the exact built-in executor instance created and registered server-side. A supported-version registry binds each raw case to a deterministic artifact digest. Injected, subclassed, separately instantiated, failed, or incomplete runners block. Within that trust boundary, the gate validates dataset/version/artifact identity and the exact named scenario set, then recomputes success, quality, cost, latency, tool, and safety metrics itself. Public evidence hashes do not prove external execution; a future remote adapter must add verified signed attestation bound to the candidate artifact digest.

## 009 — Append approval decisions

An approved attestation and an invalidated legacy `REAPPROVAL_REQUIRED` attestation are historical facts, not mutable workflow state. Database triggers reject updates and deletes. Re-review creates a new payload-bound approval row while retaining the old row.
