# Security

## Current controls

- No arbitrary command execution, dynamic imports, `eval`, or real Kafka mutation.
- Remediation names are checked against a fixed allow-list.
- Every action requires an approval record before execution; workflow state is re-read from the database.
- Pydantic constrains approval identity/reason lengths and FastAPI rejects malformed bodies.
- Optional API-key authentication requires three distinct viewer, approver, and executor keys. Approval identity is derived server-side in this mode; a viewer or executor key cannot approve, and an approver key cannot execute. Keys are read from the environment and never logged or stored.
- CORS origins and HTTP methods are explicit. Responses include anti-sniffing, anti-framing, and no-referrer headers.
- SQLite parameter binding prevents SQL injection.
- Container execution uses a non-root user and a dedicated data volume.

## Trust boundaries

Scenario input is an untrusted path parameter but must match a fixed registry. Approval input is operator-controlled. Simulator snapshots are trusted fixtures; a real adapter must treat broker messages, log text, labels, and schema contents as untrusted data and prevent prompt injection from granting tool authority.

## Secrets

Use environment variables or a workload secret store. Do not put secrets in `.env.example`, incident evidence, action parameters, logs, traces, or prompts. `LLM_API_KEY` is reserved but unused in mock mode.

## Production gaps

The role-separated static API-key mode is still not sufficient for enterprise deployment. Add OIDC, RBAC/ABAC, tenant isolation, rate limits at a gateway, CSRF protection if cookies are introduced, signed approvals, database encryption/backup, software-bill-of-materials scanning, immutable audit export, and network policies. Separate collector and executor identities. High-risk actions should require dual approval and a maintenance window.

## Responsible demo use

All included vulnerabilities/failures are synthetic. Do not adapt the execution interface to production without change-management review, least-privilege service identities, dry-run support, rollback testing, and fail-closed policy enforcement.
