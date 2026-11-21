# Security

## Security posture

This repository is a local POC with explicit controls around the dangerous boundary: agent-proposed actions do not directly become executed actions.

## Trust boundaries

1. **Observed trace:** untrusted data. Tool names, arguments, final output, and errors are never evaluated or executed.
2. **Deterministic control plane:** trusted application rules and typed schemas.
3. **Human approval:** separate authenticated-capable state transition for medium-and-higher risk.
4. **Execution controller:** only catalog-bound, versioned synthetic policy changes through a fixed allow-list.
5. **Artifact-state provider:** read-only source of outcome truth, keyed by run and artifact identity.
6. **Release executor:** exact built-in deterministic instance created and registered by the server; arbitrary runner injection is outside the trusted boundary.

## Implemented controls

- Pydantic models reject extra fields and validate scenarios, risks, decisions, and bounds.
- There is no `subprocess`, shell execution, `eval`, or arbitrary module/tool loading.
- Execution tools are exactly `policy_registry`, `evaluation_policy`, and `runtime_policy`.
- Command-style arguments in a simulated trace trigger `INVALID_ARGUMENTS` and `UNSAFE_ACTION`; they remain inert JSON evidence.
- Medium, high, and critical proposals cannot execute until a persisted approval exists for the exact canonical payload hash and version.
- Approval and execution are separate requests and audit events.
- Execute rechecks action type, tool, catalog, incident, risk, approval requirement, payload version, and payload hash; approved payload fields are immutable and bound approval attestations cannot be updated or deleted by database triggers.
- Outcome verification uses a server-owned required-state contract and persisted server-observed start/deadline timestamps to validate artifact identity, checksum, size, and freshness against provider state; trace-carried outcome or timing fields cannot override it.
- Policy rollback is verified through a separate read-only SQLite state provider after the change adapter returns. A no-op, exception, or lying controller response cannot produce `ROLLED_BACK`; authoritative mismatch becomes `ROLLBACK_FAILED`.
- The local regression gate accepts only the exact built-in executor type and server-registered instance. Raw cases bind server-assigned nonces, case IDs, unique run IDs, requested `agent_version`, and registry-owned version artifact digests. Release metrics are reconstructed from raw traces and provider snapshots, not runner summaries.
- SHA-256 evidence digests detect accidental or malformed changes inside the trusted local path; because they are public and unkeyed they do not attest external execution. A production remote runner requires verified signed attestation bound to the registered candidate artifact digest.
- Legacy approvals without hashes are invalidated during migration as immutable `REAPPROVAL_REQUIRED` history; fresh approval appends a new exact-payload-bound row.
- The synthetic policy adapter persists action-specific before/after state. The controller reads post-state independently, calculates validation checks, and rolls back mismatches or apply failures.
- `X-API-Key` authentication can be enabled with `API_KEY`; constant-time comparison is used.
- Per-client sliding-window rate limiting defaults to 120 non-health requests/minute.
- CORS defaults to `http://localhost:8101` and permits only GET/POST.
- CSP, frame denial, MIME sniffing denial, referrer, and browser-permission headers are applied.
- Common secret-bearing keys are redacted before trace/audit JSON persistence.
- The API does not return raw internal exceptions for workflow failures.
- SQLite foreign keys are enabled; audit update and delete operations are rejected by triggers.
- The container runs as an unprivileged `app` user.

## Authentication and authorization abstraction

Local mode leaves `API_KEY` empty for a one-command demo. If configured, all state-changing `/api/v1` endpoints require `X-API-Key`. The current reviewer name is an audited identity string, not full identity proof.

A production deployment should replace this dependency with OIDC/JWT validation and role checks such as `viewer`, `evaluator`, `approver`, and `executor`. Approver/executor separation should be enforced organizationally.

## Secret management

No credentials are committed. `LLM_API_KEY`, `LLM_BASE_URL`, and `API_KEY` are environment variables. A production deployment should use a secrets manager and workload identity. Do not place real secrets in traces or action reasons.

## Threats and residual risk

| Threat | POC mitigation | Production requirement |
|---|---|---|
| Prompt/tool injection | trace treated only as data; fixed tools | signed trace envelopes, tenant policy |
| Unauthorized/tampered execution | optional API key + catalog and immutable payload-bound approval gate | OIDC, RBAC/ABAC, signed proposals, four-eyes control |
| Audit tampering | database triggers | remote append-only/WORM storage and signing |
| Resource exhaustion | input bounds + rate limit | distributed limiter, body limits, quotas |
| Secret leakage | key-based redaction | structured classification and DLP |
| Database loss | project-local persistent file | encrypted HA database and backups |
| Dependency compromise | minimal pinned dependencies | lockfile/SBOM/signatures/scanning |

## Reporting

This is demonstration software. Do not expose it to an untrusted network without production identity, TLS termination, database hardening, distributed rate limiting, and a security review.
