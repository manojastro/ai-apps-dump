# Threat model

## Implemented boundaries

- Unique generated local administrator credential; Argon2 password hashes.
- Opaque server-held session hashes, HttpOnly and SameSite Strict cookies, 8-hour expiry, CSRF headers and origin restrictions.
- Viewer/investigator/reviewer/administrator enforcement on API operations. Single shared organization.
- Evidence ownership and content hashes checked before accepted diagnoses. Cross-run evidence endpoints return 404.
- Logs, traces, runbooks and deployment strings have no authority to grant tools or change policy.
- No arbitrary shell, SQL, generated PromQL, URL fetch, Docker socket or production mutation tool.
- Exact action hash, reviewer identity, expiry, current preconditions and executor-side deduplication.
- Local demo fault control requires a separately generated controller token. Demo database is separate from platform storage.
- Login throttling and bounded request/connector payloads. Fixture logs are bounded; live demo log buffer has 1,000 records and a one-hour query horizon.

## Residual risks and deployment work

This release is not hardened for public exposure. Login throttling is process-local. Desktop file ACLs inherit the current user's directory policy; chmod alone is not a Windows ACL management solution. Session cleanup, configurable platform evidence retention, distributed rate limiting, SSO and multi-tenant authorization are incomplete.

Evaluation expected labels are kept out of agent inputs and read tools and trials use separate processes. The OS filesystem is not a security sandbox: a compromised Python dependency could read repository files. Container-level agent/controller storage separation is still needed for a stronger boundary.

Ordinary audit rows are not tamper-proof. Citation validity does not establish semantic claim support. The live provider's output and real recovery behavior have not been validated. Persisted model usage cannot know whether a provider charged a timed-out request.

An inherited npm audit finding exists in the preserved InsightAI `xlsx@0.18.5` dependency (prototype pollution/ReDoS). ProductionLens does not import that workbook parser. No unreviewed replacement was made to the separate application's file support.
