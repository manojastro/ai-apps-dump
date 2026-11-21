# API guide

Operational endpoints:

- `GET /health`
- `GET /ready`
- `GET /metrics`

Versioned endpoints:

- `GET /api/v1/scenarios`
- `GET /api/v1/agents`
- `POST /api/v1/scenarios/{scenario}/scan`
- `GET /api/v1/incidents`
- `GET /api/v1/incidents/{incident_id}`
- `POST /api/v1/incidents/{incident_id}/approval`
- `POST /api/v1/incidents/{incident_id}/remediate`
- `GET /api/v1/evaluations/summary`
- `GET /api/v1/activity`

Interactive schemas are at `/docs`. In `AUTH_MODE=open`, anonymous reads are demo-only;
approval uses `forgeguard-local-demo-approver` and remediation uses
`forgeguard-local-demo-executor` as `X-API-Key`. These embedded values must never be
used outside a local demo. In `AUTH_MODE=api_key`, configure distinct viewer, approver,
and executor credentials. Roles are derived from matching credentials;
`X-Role` is not accepted.

Legacy bound-approval migrations can place an incident in `REAPPROVAL_REQUIRED`.
Remediation is blocked in that state. The approval endpoint accepts a new reviewed
decision, verifies the exact displayed preview and fixed-source hashes, and appends a
new immutable attestation. Failed or unavailable validation returns an incident in
`VALIDATION_FAILED` with rollback evidence; `source.after_sha256` remains null because
the original workspace content was restored.
