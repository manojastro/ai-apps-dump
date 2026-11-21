# Demo scripts

All suppliers, prices and orders are synthetic. Fixture mode labels every model decision as simulated.

## Five-minute demo

Preparation (admin, *Suppliers & policy* page): reset suppliers to **price_change_after_approval**
(Beta raises its price after the first approval-time quote), or use **happy_path** plus the
*Demo: raise Beta price* button after approving.

1. **Request** (requester): *New request* → ten Northwind Pro 14 laptops, ≥16 GB RAM, ≥512 GB SSD,
   budget ₹5,00,000 landed, deliver within seven days to ADDR-BLR-01. As admin you can tick
   *Plant a bad recommendation* to make the verifier's rejection visible.
2. **Browse three portals** (run page): live activity shows Alpha (tax-exclusive tables), Beta
   (tax-inclusive cards) and Gamma (B2B sidebar, per-unit freight). Redacted screenshots appear.
3. **Reject the cheaper incompatible offer** (comparison): the 8 GB laptops are ineligible with
   `spec.ram_gb expected >= 16 GB, observed 8 GB`; the verifier banner shows the rejected recommendation.
   Gamma's 16 GB offer looks affordable per unit but fails `budget.landed_total` after tax and freight.
4. **Compare verified totals**: Beta ₹4,74,000 (eligible, cheapest), Alpha ₹4,91,200 (eligible).
5. **Approve** (approver): the approval page shows the exact bound purchase, fingerprint, policy checks
   and evidence; approve with a reason.
6. **Detect the post-approval price change**: revalidation reloads Beta's checkout, finds ₹4,91,000,
   invalidates the approval and explains the change (`total 474000.00 → 491000.00`).
7. **Fresh approval** for the new terms (still within budget) → approve.
8. **Complete the simulated purchase**: protected submission with the idempotency token; the order page
   shows ledger `reconciled`, supplier reference, verified receipt checks and the redacted receipt.

## Short demo: timeout reconciliation and duplicate prevention

1. Reset suppliers to **timeout_success** (Beta commits the order but answers after the browser timeout).
2. Run and approve as above. The submission step ends with `SUBMISSION_OUTCOME_UNKNOWN`; the ledger moves
   to `unknown`.
3. Reconciliation finds the order in Beta's history by PO reference → `submitted` → receipt verified →
   `reconciled`. The admin fixture state (or `GET /_control/orders` as operator) shows exactly one order.
4. Duplicate prevention: `pytest -k duplicate_worker_delivery` delivers the same resume to two workers
   at once; the advisory run lock and ledger allow one submission, and the supplier sees one order.
