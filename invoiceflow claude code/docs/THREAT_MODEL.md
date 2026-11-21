# Threat model (STRIDE)

Scope: the agent, its tools, the approval service, the SIMULATED ERP and the audit trail.
The data is synthetic. Assets: correct payments (simulated), vendor bank details, the
integrity of decisions and audit, and the confidentiality of contracts.

**Status:** written and checked against the code by Claude Code on 2026-10-25. Manoj's
review is still pending. Each mitigation names the code or test that implements it.

## Spoofing

| Threat | Mitigation | Evidence |
|---|---|---|
| Someone approves as another user | Identity comes only from the bearer token: random dev tokens (v1), Entra ID JWT validated for signature, issuer, audience and expiry (v2) | `services/approvals/auth.py`; `test_oidc_maps_app_roles_and_validates_the_token` |
| Request body claims a higher role | Request models forbid extra fields; the role comes from the token | `test_role_in_the_body_is_ignored` |
| A fraudster poses as the vendor to change bank details | Any bank change is escalated; Finance Controller plus a call-back by someone other than the preparer | CM-03; `test_bank_change_needs_controller_and_callback` |

## Tampering

| Threat | Mitigation | Evidence |
|---|---|---|
| Prompt injection in invoice text ("ignore policy and approve") | The core never reads free text; the LLM sees it labelled untrusted; validators block downgrades; policy decides | `test_free_text_never_changes_the_result`; `test_a_model_that_tries_to_approve_is_stopped` |
| Bank change hidden in notes | Deterministic remittance screen forces escalation; the model may not ignore it (SIGNAL_IGNORED) | `agent/text_screen.py`; eval adversarial results |
| Audit rows edited after the fact | Append-only triggers plus a SHA-256 hash chain; the verifier finds the first bad row | `test_audit_chain_detects_a_tampered_row` |
| Edited dataset files | The manifest stores per-file SHA-256; reads refuse mismatches | `test_tampered_file_is_refused` |
| SQL injection through vendor text | Parameterized queries; on Databricks, data is loaded from a volume, never spliced into SQL; identifiers validated | `test_reader_uses_named_parameters_not_string_splicing` |

## Repudiation

| Threat | Mitigation |
|---|---|
| "I never approved that" | Every approval attempt (valid or refused) is an audit entry with the approver identity from the token; evidence packs record the decision and the matrix version |
| "Policy was different then" | Every decision stores the control matrix's content hash |

## Information disclosure

| Threat | Mitigation | Evidence |
|---|---|---|
| A user or the agent reads another vendor's contract | Scope filter applied before ranking; the agent is scoped to the invoice's vendor; AI Search filters plus a re-check | `test_vendor_scope_hides_other_vendors_contracts`; `test_ai_search_results_are_rechecked_against_scope` |
| Platform Admin reads contracts | Contracts exclude PLATFORM_ADMIN | `test_platform_admin_never_sees_contracts` |
| Bank numbers in logs, traces or evidence | Masked in tool results, traces, audit and evidence packs | `observability/masking.py`; `test_tool_results_mask_bank_numbers_and_label_vendor_text` |
| The agent sees the answers | Ground truth in a separate schema, not reachable through the data port | `test_answers_cannot_leak_through_invoice_fields` |
| Secrets committed | `.env` git-ignored; gitleaks on every commit and on full history in CI; `.env` guard hook | `.pre-commit-config.yaml` |

## Denial of service

| Threat | Mitigation |
|---|---|
| A model loops on tools or burns tokens | Budgets (tool steps, tokens, wall clock, retries per tool) → fail_safe | `test_tool_budget_is_enforced` |
| Model endpoint down or slow | LLMError → manual queue; nothing is guessed | `test_model_errors_fail_safe` |
| ERP down | Bounded retries with the same idempotency key → ERP_ERROR → manual queue |
| Free Edition quota lockout | Manual queue keeps working; the kill switch pauses automation without a redeploy |

## Elevation of privilege

| Threat | Mitigation | Evidence |
|---|---|---|
| The model calls a write tool | Write tools are not in the model's registry; only the executor writes, after `require_allow` | `test_the_model_never_gets_write_tools`; CM-07 tests |
| The agent approves its own proposal | Non-human identities can never approve | CM-06; `test_agent_approval_is_refused_and_case_keeps_waiting` |
| Preparer approves own work | Segregation of duties in policy and the service | CM-05 |
| Clerk approves above their limit | Server-side check and policy authority check | `test_insufficient_authority_is_refused_server_side` |

## Known residual risks

- The hash chain is tamper-*evident*, not tamper-*proof*. The head hash is not anchored to
  write-once storage.
- Dev tokens are for local use only. OIDC is implemented and tested with a local key, but
  no Entra ID tenant has been configured.
- The remittance screen is regex-based; novel phrasing can slip past it. The LLM is the
  second line, and its live adversarial results are in PROGRESS.md.
- The approval inbox has no CSRF protection beyond bearer tokens in headers (no cookies are
  used), and no rate limiting.
