# SECURITY

## Threat Model

The service is a change-validation control plane; its own compromise or misuse
would translate directly into production network incidents. The primary risks
addressed are: unauthorized mutation of the network twin, bypassing human
approval, silent expansion of access (segmentation violations), and untraceable
changes.

## Controls Implemented

### Approval state machine
All lifecycle transitions are validated against a single transition table.
Applying a change requires APPROVED status; the mutating tools independently
refuse execution otherwise. Illegal transitions return HTTP 409 with an
explicit message.

### Risk-gated approvals
Changes scored HIGH or CRITICAL require a written justification to be approved;
the justification, actor, decision and status delta are persisted in the
approvals table for audit.

### Mutating tool gate
`apply_change_tool` and `rollback_tool` declare permission `mutating`. The tool
executor refuses any invocation without an explicit approval flag from the
orchestration layer, which itself only sets that flag after the state machine
approved the transition.

### Post-apply verification and auto-rollback
Every apply re-runs the intent suite against the promoted CURRENT twin. Any
intent failure triggers automatic rollback to the archived pre-change snapshot,
restoring the last known-good state without operator intervention.

### Least-privilege policy simulation
The twin enforces default-deny between zones at the firewall layer, explicit
segmentation ACLs for east-west isolation, management-plane restriction
(only-from-subnet intents), and route-redundancy requirements. Changes that
weaken these controls are detected as first-class regressions
(SEGMENTATION_VIOLATION, INTENT_MUST_NOT_REACH_VIOLATED, ROUTE_HIJACK).

### Audit trail
Every approval decision, validation run, regression, agent investigation,
hypothesis, RCA record, tool call (input/output/duration/error), KPI snapshot
and lifecycle event is persisted. The audit log answers who approved what, when,
with what evidence.

### LLM containment
The LLM adapter only renders narration of computed results. It receives no
credentials context, cannot invoke tools, cannot alter verdicts, and falls back
to deterministic mock narration on any failure. Live mode requires explicit
LLM_MODE=live plus an API key.

## Secrets Handling

Secrets are read exclusively from environment variables (see .env.example).
No secret is ever logged, persisted in payloads, or embedded in reports.
The default deployment runs fully offline in mock mode requiring no key.

## Known Gaps (pre-production)

- No authentication/authorization layer yet; production must add OIDC SSO,
  RBAC roles (requester vs approver separation) and session security before
  exposure beyond localhost.
- No TLS termination internally; terminate at the ingress layer.
- SQLite is single-writer; production should use Postgres with row-level
  auditing.
- Tool timeout enforcement uses daemon threads; long-running external calls in
  live mode should move to an executor with cancellation.
