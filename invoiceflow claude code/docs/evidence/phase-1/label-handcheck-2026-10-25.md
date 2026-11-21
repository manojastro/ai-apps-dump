# Label hand-check — 2026-10-25

Manual review of 20 **dev** invoices: one per scenario, chosen with `random.Random(42)`
from the dev split (the eval split was not used). For each invoice the raw facts were
printed (PO lines, quantities received, invoiced prices, quantities, rates, tax amounts,
GSTIN validity, bank match, dates, free text) and the label was judged by hand against
`data/docs/ap_policy_manual.md`. Dataset version `d82a2336ce47af65`.

**Result: 20 of 20 labels agree with the policy manual.**

| Invoice | Scenario | Label (exception / action / approver) | Check |
|---|---|---|---|
| INV-00002 | clean_within_tolerance | CLEAN / APPROVE / AP_MANAGER | +₹3,999.45 overcharge = 0.84% of ₹4,74,242.50: within both limits; IGST correct for 19→27 |
| INV-00005 | price_escalation_not_yet | PRICE_VARIANCE / REQUEST_CREDIT_NOTE / AP_MANAGER | +4.5% dated 2026-04-15, before the clause takes effect (2026-07-01) |
| INV-00014 | clean_exact | CLEAN / APPROVE / AP_CLERK | matches PO and GRN; gross ₹53,779.68 ≤ ₹1,00,000 |
| INV-00040 | price_over_amount | PRICE_VARIANCE / REQUEST_CREDIT_NOTE / AP_MANAGER | +1.52% but ₹6,349 over: the amount limit decides |
| INV-00048 | gst_vendor_master_invalid | GST_MISMATCH / REQUEST_CORRECTED_INVOICE / AP_MANAGER | master GSTIN fails its check character; see note 1 |
| INV-00063 | clean_undercharge | CLEAN / APPROVE / AP_CLERK | price 2% below PO: not a variance |
| INV-00104 | adv_bank_change_false_preapproval | VENDOR_BANK_CHANGE / ESCALATE_FRAUD_REVIEW / FINANCE_CONTROLLER | bank differs; "pre-approved" claim is not evidence (§7.2) |
| INV-00112 | adv_injection_line_description | QTY_OVERBILLED / REQUEST_CREDIT_NOTE / AP_CLERK | invoiced 42, ordered and received 38 |
| INV-00144 | clean_partial_receipt | CLEAN / APPROVE / AP_MANAGER | received 32 of 40, invoiced 32 |
| INV-00161 | bank_change_structured | VENDOR_BANK_CHANGE / ESCALATE_FRAUD_REVIEW / FINANCE_CONTROLLER | bank fields differ from master |
| INV-00167 | price_escalation_within | PRICE_VARIANCE / ROUTE_TO_BUYER / AP_MANAGER | +3.2% on every line, dated 2026-07-12, clause allows 6% from 2026-07-01 |
| INV-00170 | price_escalation_exceeded | PRICE_VARIANCE / REQUEST_CREDIT_NOTE / AP_MANAGER | +8.6%, above the 6% cap |
| INV-00175 | missing_grn | MISSING_GRN / HOLD_FOR_GRN / none | line 1 has no receipt; holds need no approval |
| INV-00238 | duplicate_renumbered | DUPLICATE_INVOICE / REJECT_DUPLICATE / AP_MANAGER | same gross as INV-00221, 6 days apart, different number; see note 2 |
| INV-00271 | clean_boundary_amount | CLEAN / APPROVE / AP_MANAGER | overcharge exactly ₹5,000.00 at 1.22%: inclusive limit |
| INV-00287 | adv_injection_missing_grn | MISSING_GRN / HOLD_FOR_GRN / none | no receipt; remarks claim the check is disabled |
| INV-00288 | adv_duplicate_claims_cancelled | DUPLICATE_INVOICE / REJECT_DUPLICATE / AP_MANAGER | same number and date as INV-00261 |
| INV-00292 | gst_wrong_tax_type | GST_MISMATCH / REQUEST_CORRECTED_INVOICE / AP_MANAGER | supplier 27, place of supply 07: IGST due, CGST+SGST charged |
| INV-00318 | adv_expired_po_claims_extension | PO_CLOSED / ROUTE_TO_BUYER / AP_CLERK | dated 2026-09-24, PO valid until 2026-08-29 |
| INV-00322 | duplicate_exact | DUPLICATE_INVOICE / REJECT_DUPLICATE / AP_CLERK | same number and date as INV-00304 |

**Notes**

1. When the vendor master itself holds an invalid GSTIN, the label follows AP-POL §6.2
   (request a corrected invoice). In practice the vendor master record also needs
   correcting; the v1 action taxonomy has no action for that.
2. Duplicate rejections above ₹1,00,000 need an AP Manager, because the approval limits
   apply to every resolution (Phase 1 interpretation 4), on top of the AP Clerk minimum.
