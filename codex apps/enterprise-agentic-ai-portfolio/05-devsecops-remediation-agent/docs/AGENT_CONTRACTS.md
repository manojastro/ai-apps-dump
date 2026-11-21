# Agent contracts

Runtime definitions are returned by `GET /api/v1/agents`. Decision-bearing outputs use
Pydantic types: `SecurityFinding`, `Evidence`, `ExploitabilityAssessment`,
`RemediationPlan`, `ReleaseRisk`, `InvestigationResult`, and `ValidationResult`.

The finding and exploitability agents are read-only; exploitability prediction does
not read the evaluation label. The remediation agent can select only a fixed
transformation from the known catalog. Immutable approval binds the exact persisted
preview bytes, action, and fixed-source hashes. The executor verifies these bindings
and cannot run source or commands. Validation compares the complete canonical AST,
including module layout, exact signature/body/return, imports, and every call with its
arguments. The release-risk agent is advisory and defaults to blocking whenever a
check fails; failed or unavailable validation restores before-source and records a
rolled-back failure outcome.

Unknown scenarios, ambiguous finding counts, changed sources, unapproved incidents,
invalid syntax, missing safe constructs, contract changes, remaining findings, and
new high-risk patterns all fail closed.
