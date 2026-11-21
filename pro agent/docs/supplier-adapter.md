# Supplier adapter contract

The MVP ships one adapter, `semantic_portal_v1`, used by all three synthetic portals. It relies on
accessible semantics rather than per-site CSS selectors.

## What a portal must offer for `semantic_portal_v1`

| Capability | Expectation |
|---|---|
| Sign-in | A username/account field with a label matching `user|account id|username`, a password field, a button named `Sign in`/`Log in`/`Login`. Interactive MFA is detected and handed to a person. |
| Search | A `role=search` form with a textbox, or a field labelled/placeholdered with `search|find|keyword`. |
| Product page | `h1` product name; label/value pairs as `dl`, `th/td` rows, two-column `.row`s, or labelled chips; quantity field; button `Add to cart/basket/quote cart`. |
| Cart | Nav link `Cart`/`Basket`/`Quote cart`; per-line `Remove <SKU>` buttons; checkout link. |
| Checkout | Destination `select` labelled `address|ship to|consignee` with options containing `(ADDR-…)`; continue button; confirmation summary with subtotal, discount, tax (labelled `GST…` with rate), shipping, total, currency, delivery date, quote reference. |
| Submission | PO-reference field (`PO number`/`order reference`/`PO reference`); a single purchase button. The supplier treats the PO reference as an idempotency token and validates the reviewed quote reference atomically. |
| Reconciliation | Order history page listing order reference and PO reference; order detail with a receipt download. |

## Adding a supplier

1. Add the portal origin to `BROWSER_ALLOWED_ORIGINS` and create a `suppliers` row (admin UI or seed)
   with `allowed_origins`, `adapter`, `is_simulated`, `status_api_supported`, `conditional_submit_supported`.
2. Store credentials in the secret store and reference them from `supplier_credentials_metadata.credential_ref`
   (`SUPPLIER_CREDENTIALS_JSON` in development).
3. Map supplier SKUs to canonical products in `fixtures/sku_map.json` (buyer master data).
4. Run the benchmark subset for that supplier and add scenario fixtures if the portal has new behaviour.
5. If the semantics above do not hold, implement a new adapter with the same tool contracts; do not
   relax policy, approval, privacy or reconciliation requirements to fit a site.

## Real suppliers (not enabled in this release)

* Require explicit written authorization per website and per purchasing action, and a reviewed adapter.
* `DRY_RUN=false` is rejected at startup in this release.
* **Local locks alone cannot guarantee exactly-once execution** on an external site, nor prevent a
  last-moment price change between revalidation and the click. Use a supplier-supported conditional
  submission contract (idempotency token + quote version) when available. If reliable validation
  cannot be enforced, use *human final submission mode*: the agent prepares and verifies the cart and a
  person clicks the final button.
* Never bypass CAPTCHA, MFA, login restrictions or browser security; pause for an authorized person.
* A supplier status API may be used for reconciliation only when the adapter explicitly supports it;
  otherwise reconcile from the account order-history page.

Skyvern ([skyvern.com](https://www.skyvern.com/), [source](https://github.com/Skyvern-AI/skyvern)) is the
category inspiration and a possible future adapter; it is not used in the MVP.
