# Purchasing policy and quote normalization

Policy is versioned data (`policy_versions.rules`) evaluated by deterministic code
(`procnav/policies/engine.py`). It is never placed in model prompts, and a model confidence score is
never an input.

## Normalization (`procnav/quotes/normalize.py`)

* Money is `Decimal`; every component is rounded **ROUND_HALF_UP to 0.01 INR** once, at order level.
* Landed cost is read from the supplier's checkout confirmation, then independently recomputed:
  * subtotal = unit price × quantity
  * tax-exclusive: total = subtotal − discount + tax + shipping; tax must equal rate × taxable amount,
    where taxable is goods only or goods + shipping (the basis that matches is recorded)
  * tax-inclusive: total = subtotal − discount + shipping; embedded tax = gross − gross / (1 + rate)
* Inconsistent arithmetic, a missing component, an uncertain currency or an unstated tax basis is
  flagged and fails `arithmetic.consistent` / `cost.components_present` / `currency.allowed`.
* Quantities are individual laptops. A listing described as a bundle, pack or "multiple units" has an
  unknown pack size and fails `unit.pack_size` until clarified.
* Synthetic GST 18% is a fixture value, not tax advice.

## Hard rules (any failure → ineligible)

| Rule | Meaning |
|---|---|
| `spec.canonical_family`, `spec.cpu`, `spec.os`, `spec.storage_type` | Must match the canonical product |
| `spec.ram_gb`, `spec.ssd_gb` | At least the requested minimum |
| `unit.pack_size` | Exactly one laptop per unit |
| `quantity.match` | Checkout quantity equals the request |
| `stock.available` | Observed stock covers the full quantity |
| `supplier.eligible` | Enabled, approved, and allowed for the request |
| `delivery.confirmed` / `delivery.deadline` | Confirmed date on or before the deadline |
| `destination.match` | Ships to the requested destination reference |
| `currency.allowed` | Certain, equal to the request currency, allowed by policy |
| `quote.fresh` | Retrieved within `max_quote_age_seconds` |
| `cost.components_present`, `arithmetic.consistent` | See normalization |
| `budget.landed_total` | Landed total (tax + shipping included) within the request budget |
| `budget.spending_limit` | Within the per-order limit |

Soft preferences (`pref.fast_delivery`, `pref.supplier`) are shown but never decide eligibility.
An approver may choose another eligible supplier; soft-preference overrides are recorded.
Hard-rule exceptions require an explicit `policy_exceptions` record created by an administrator
(`POST /api/policy-exceptions`); the agent cannot create one.

## Ranking

Eligible quotes first, then lowest landed total, then earliest delivery date, then supplier key, then SKU.

## Verifier

The planner recommends a quote; the verifier re-evaluates it. If it fails any hard rule (e.g. the planted
8 GB recommendation fails `spec.ram_gb`: expected `>= 16 GB`, observed `8 GB`) the rejection is recorded
as a policy decision, audit event and run event, and the top-ranked eligible quote is selected instead.

## Material change

Before submission the cart is reloaded and compared field by field with the approved binding
(`material_change_fields`: supplier, SKU, quantity, unit price, discount, tax, shipping, total, currency,
delivery date, destination, supplier quote reference) plus request version and approval expiry.
Any difference invalidates the approval and creates a fresh request showing what changed.
