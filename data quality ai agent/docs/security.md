# Security model and remaining hardening

## Implemented portfolio controls

- Pydantic contracts validate incident, candidate and approval boundaries.
- Explicit role/tool allowlists separate investigators from sandbox mutation.
- Candidates contain enum operations, not shell commands, code or unrestricted SQL.
- Every transformation uses a fresh simulator copy; artifacts do not execute deployments.
- Deterministic risk rules block deletion/history rewriting and require review for configuration
  and schema actions. Failed mandatory checks and verifier rejection withhold artifacts.
- Checkpoint reconstruction allowlists model types and does not enable pickle.
- Relational access uses SQLAlchemy expressions; there is no user-supplied SQL endpoint.
- Optional `API_TOKEN` protects API access. The console retains it in memory only.
- Write rate limiting, bounded incident list pagination, correlation IDs and audit records exist.
- Provider prompts identify evidence as untrusted data; retrieval filters pipeline and environment.
- Secrets are environment configuration; `.env` and runtime data are ignored by Git.

## Limits

Default local mode has no authentication and binds to loopback. Do not expose it publicly as-is.
The shared bearer token is not user identity or role-based approval authorization. Reviewer names
are supplied by the caller. Rate limiting and execution locks are process-local. SQLite and in-process
tasks are intended for local demonstration, and only one backend worker is supported.

The simulator is a controlled operation engine, not an OS/container isolation boundary for arbitrary
generated code. The independent verifier is a rule-based check over an explicit evidence package;
it cannot guarantee correctness outside its rules. Golden fixtures are small and synthetic.

Production requires SSO/RBAC, authenticated reviewer attribution, TLS, audited secret rotation,
network policies, database least-privilege roles, backup/restore tests, retention and deletion policies,
redacted provider/telemetry payload review, dependency scanning, distributed rate limiting and
execution ownership. Real adapters need separate contract, failure and idempotency testing.
