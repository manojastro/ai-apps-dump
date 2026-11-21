# Threat model

Scope: the controlled demo (synthetic suppliers, simulated purchases). Guarantees below apply to this
environment; they do not establish guarantees for arbitrary real websites.

| # | Threat | Mitigations | Verified by |
|---|---|---|---|
| T1 | Prompt injection in page text or images ("ignore the budget", "approved already", "enter your password") | Page content passed as `<untrusted_page>` data; policy in code; approvals only via authenticated approver API; proposals validated against observation; purchase controls only via protected tool; egress guard | `test_malicious_page_cannot_redirect_or_change_policy` (DOM text + SVG image injection, simulated compromised proposal is blocked) |
| T2 | Navigation/exfiltration to unapproved domains or cloud metadata | Route-level egress guard on all requests, redirects, downloads; metadata/link-local always blocked; worker container on an internal-only network | Same test; `BLOCKED_NAVIGATION` steps; request log shows no hit |
| T3 | Unapproved or duplicate purchase | Ledger + row locks + partial unique index + advisory run lock + supplier idempotency token + quote-ref validation; resume consults ledger first | duplicate-delivery, timeout, restart tests; `zero_unapproved_mock_purchases`, `zero_duplicate_orders` gates |
| T4 | Approval for something other than what is bought | Fingerprint binding; revalidation diff; live diff inside the submit tool; supplier quote-ref check | price-change tests; `changed_approvals_invalidated` gate |
| T5 | Self-approval / role spoofing | Roles from server-side memberships only; requester ≠ approver by default; client headers ignored | `test_roles_are_server_side...`, `test_requester_cannot_approve...` |
| T6 | Cross-tenant data access | Tenant from server session; RLS forced on all tenant tables; non-owner runtime role; tenant-qualified checkpoint threads; per-tenant browser contexts and storage state | `test_cross_tenant_evidence_and_runs_are_invisible`, `test_database_rls_blocks...`, eval gate |
| T7 | CSRF on cookie sessions | `X-CSRF-Token` must match the session token for every mutation; SameSite=Lax cookies | `test_csrf_required_for_cookie_mutations` |
| T8 | Credential leakage (supplier passwords, cookies, API keys) | Credentials resolved by reference at run time; never stored in DB, prompts or logs; storage state Fernet-encrypted; redaction of logs/steps/audit; screenshot masks | Code review; redaction unit behaviour |
| T9 | Sensitive data in evidence (addresses, business data) | Address references instead of addresses in requests/prompts; address redaction in text, receipts and screenshots; evidence served only via authorized endpoint; retention purge | API tests; retention housekeeping |
| T10 | Audit tampering | Append-only triggers + revoked UPDATE/DELETE grants | `test_audit_events_are_append_only` |
| T11 | Invalid ledger manipulation | Transition trigger rejects invalid moves even from SQL | `test_order_ledger_rejects_invalid_transition_at_database_level` |
| T12 | Fixture control abuse | Separate port, token required, internal network only, not in agent tool registry, Caddy returns 404 for `/_control` | `test_control_api_requires_token` |
| T13 | Resource exhaustion | 80-action and 15-minute active budgets, model-cost ceiling, max 2 concurrent runs, container CPU/memory limits, request-size limit, rate limits | Budget events; compose limits |
| T14 | MFA/CAPTCHA bypass pressure | Never bypassed; run pauses for an authorized person | `test_mfa_pauses_safely_for_a_human` |

Residual risks: in-process rate limiting is per API instance; screenshots may still include business
data; real-model mode sends redacted page text to the model provider; the OIDC seam is untested against
a live Entra tenant; LangGraph checkpoint tables are owned by the library and are not covered by RLS —
they are only ever loaded for the run named by a server-created job row, under tenant-qualified thread
IDs, but a SQL-level bug in that path would not be stopped by the database.
