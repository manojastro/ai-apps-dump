# Typed browser tool contracts

Implemented in `backend/procnav/browser/tools.py` on `SupplierBrowser`, one isolated Playwright
context per tenant and supplier session. Every call returns a `ToolResult` and is persisted as a
`browser_steps` row (addressable by run + `seq`) and a run event.

```python
class ToolResult(BaseModel):
    tool: str
    ok: bool
    status: str            # ok | error | blocked | handoff
    data: dict             # structured, redacted observation
    error_code: str | None # stable codes below
    message: str | None
    url: str | None
    evidence_ids: list[str]
    at: datetime           # UTC timestamp
    duration_ms: int
    step_seq: int | None
```

| Tool | Input | Output `data` | Side effect | Notes |
|---|---|---|---|---|
| `open_supplier` | supplier (from config) | title, `logged_in_now` | none | Restores encrypted storage state; logs in with credentials resolved by reference; MFA → `HumanHandoff` |
| `observe_page` | — / `{url, purpose}` | page summary (headings, pairs, alerts, in-main links) | none | `revisit` only allows pages already observed in this session |
| `find_product` | `query` (1-120 chars) | `candidates[{index,text,href}]` | none | Semantic locators: `role=search` textbox, label/placeholder fallback; 5xx retried |
| `inspect_product` | `href` | `product: ExtractedProduct` (label → value pairs, chips) | none | `href` must have been offered by an observed page; screenshot evidence |
| `add_to_cart` | `quantity` 1-1000 | landing page | reversible cart change | Quantity by label (`Quantity`/`Qty`/`How many?`) or spinbutton |
| `inspect_cart` | `expected_sku`, `expected_qty` | `removed_other_lines` | reversible | Removes other lines so checkout has one approved line; verifies quantity |
| `extract_quote` | `address_ref` | `checkout: ExtractedCheckout` | none | Checkout preview → destination selected by reference → confirmation summary; no submission |
| `refresh_quote` | `href, quantity, sku, address_ref` | product + checkout | reversible | Revalidation path; returns the sequence of results |
| `request_approval` | (graph node) | approval request id | DB only | Implemented by `create_approval` + `await_approval` nodes; never callable from page content |
| `submit_approved_order` | `intent_key`, `address_ref`, approved cart, ledger check, live-diff check | `order_ref`, `replayed` | **purchase** | Protected; see below |
| `inspect_order_history` | `intent_key` | `found`, `ambiguous`, `order_refs` | none | Reconciliation; no status API in mock adapters |
| `verify_receipt` | `order_ref` | receipt fields, receipt evidence id | none | Waits a bounded time for "processing" orders; download URL egress-checked; address redacted before storage |
| `pause_for_human` | reason | — | — | `HumanHandoff` exception → `human_handoff` node (`interrupt`) |
| `perform_page_action` | `{type: click_link|fill_search, index, text}` | navigation result | none | Model-proposed recovery action, validated against the current observation; purchase controls refused |

## Protected submission

`submit_approved_order` refuses unless **all** hold, checked in this order at the last moment:

1. Supplier is simulated or DRY_RUN is false (real suppliers are not enabled in this release).
2. The live confirmation page, re-normalized, has **no** material difference from the approved cart.
3. The order ledger says this exact intent is `submitting` (the caller moved it there under a row lock).
4. The PO-reference field exists; the intent key is typed as the supplier idempotency token.

Only this tool may operate controls named like `Place order` / `Confirm purchase` / `Submit purchase order`;
every other click path raises `BLOCKED_PROTECTED_ACTION`. A navigation timeout after the click raises
`SUBMISSION_OUTCOME_UNKNOWN` and the ledger moves to `unknown`.

## What the model can and cannot do

The model (or fixture model) proposes: search phrases, which result links to inspect, product facts
(real mode), a recommendation, and recovery actions. It cannot: run JavaScript, issue network requests,
use raw Playwright, enter credentials, operate purchase controls, create or alter approvals, or change
policy. Proposals referencing elements not in the current observation are rejected (`INVALID_ACTION`).

## Stable tool error codes

`TIMEOUT`, `BROWSER_ERROR`, `ELEMENT_NOT_FOUND`, `INVALID_INPUT`, `INVALID_ACTION`, `BLOCKED_NAVIGATION`,
`BLOCKED_REDIRECT`, `BLOCKED_PROTECTED_ACTION`, `SUPPLIER_UNAVAILABLE`, `SUPPLIER_ERROR`, `LOGIN_FAILED`,
`CART_MISMATCH`, `CHECKOUT_ERROR`, `DESTINATION_UNAVAILABLE`, `TERMS_CHANGED`, `LEDGER_REFUSED`, `DRY_RUN`,
`SUBMISSION_OUTCOME_UNKNOWN`, `SUPPLIER_REJECTED_<supplier code>` (e.g. `QUOTE_CHANGED`,
`INSUFFICIENT_STOCK`, `PO_REFERENCE_CONFLICT`), `ORDER_NOT_FOUND`, `RECEIPT_PENDING`, `HUMAN_HANDOFF`.

## Isolation and redaction

* New `BrowserContext` per tenant + supplier; storage state encrypted with Fernet (`CREDENTIALS_KEY`)
  and retained for at most the supplier's `session_retention_seconds`. Never shared across tenants.
* Egress guard (`browser/guard.py`) on every request: allowed origins only (intersection of supplier
  config and `BROWSER_ALLOWED_ORIGINS`), `data:` inline resources, metadata and link-local addresses
  always blocked, redirects re-checked, extra tabs closed, download URLs checked.
* Passwords, cookies, tokens, e-mail addresses and postal addresses are redacted from step data,
  model inputs, audit data and logs; screenshots mask password fields and lines with postal codes.
