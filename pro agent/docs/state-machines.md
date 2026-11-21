# Approval and order-ledger state machines

Both are enforced by PostgreSQL triggers (`procnav/core/security_sql.py`), not only by application code.

## Approval requests

```mermaid
stateDiagram-v2
  [*] --> pending: agent creates request bound to fingerprint
  pending --> approved: approver (not requester) decides
  pending --> rejected: approver decides
  pending --> expired: TTL elapsed
  pending --> invalidated: offer changed / approver chose alternative / run canceled
  approved --> consumed: order intent created (exactly once)
  approved --> invalidated: revalidation found a material change
  approved --> expired: TTL elapsed before submission
```

The fingerprint is `sha256` of the canonical binding: request id and version, supplier, quote id and
canonical hash, cart view (SKU, quantity, unit price, discount, tax, shipping, total, currency,
delivery date, destination, supplier quote reference), maximum amount, delivery deadline, destination
reference, and policy version. The decision API also requires the approver to echo the fingerprint they
reviewed (`acknowledged_fingerprint`); a mismatch returns `409 CONFLICT`.

Decisions are idempotent (one `approvals` row per request; same approver + same decision returns the
stored record) and audited with the reason, fingerprint and policy evaluation.

## Order intents (ledger)

```mermaid
stateDiagram-v2
  [*] --> approved: approval consumed
  [*] --> created
  created --> approved
  created --> canceled
  created --> failed
  approved --> submitting: row-locked, attempt recorded, before any click
  approved --> canceled
  approved --> failed
  submitting --> submitted: confirmation page showed an order reference
  submitting --> unknown: timeout or ambiguous response after a possible click
  submitting --> failed: refused before click, or supplier rejected atomically
  submitting --> cancellation_requested: user canceled during submission
  cancellation_requested --> submitted
  cancellation_requested --> unknown
  cancellation_requested --> canceled: absence established
  cancellation_requested --> failed
  unknown --> submitted: order found in history
  unknown --> reconciled
  unknown --> failed: absence established (new approval needed)
  unknown --> canceled
  unknown --> submitting: only after absence is established reliably
  submitted --> reconciled: receipt verified against approval
  submitted --> unknown
  reconciled --> [*]
  failed --> [*]
  canceled --> [*]
```

Rules:

* `intent_key`, `approved_fingerprint`, `max_amount` and `approval_request_id` are immutable.
* At most one intent per run may be in `created/approved/submitting/submitted/unknown/cancellation_requested`.
* Closing a browser or canceling a run never marks an order canceled; only an established supplier
  outcome does.
