# Synthetic dataset

> **Everything here is synthetic.** Companies, people, GSTINs, PANs, bank accounts, amounts
> and documents are generated. Any resemblance to a real entity is coincidental.

## Regenerate it

```bash
uv run invoiceflow data generate
```

The default seed is `20261025`; pass `--seed N` for another dataset. The command writes:

| Output | What | In git? |
|---|---|---|
| `data/generated/*.jsonl` | one JSON Lines file per table | no (reproducible from the seed) |
| `data/generated/manifest.json` | seed, generator and Faker versions, SHA-256 per file, `dataset_version` | no |
| `data/docs/contracts/CT-*.md` | rendered vendor contracts | yes |
| `data/samples/*.jsonl` | first 5 rows of each table | yes |

The same seed always produces byte-identical files (tested). `read_dataset` refuses a file
whose hash does not match the manifest, and a test fails if the committed contracts or
samples drift from a fresh generation.

Faker output can change between Faker versions. The version is pinned in `uv.lock` and
recorded in the manifest (Faker 40.43.0 for the current dataset).

## What it contains

Measured on 2026-10-25, dataset version `d82a2336ce47af65`, seed 20261025:

| Table | Rows |
|---|---|
| Vendors | 30 (2 with a deliberately invalid GSTIN on the vendor master) |
| Purchase orders | 200 (99 billed by more than one invoice) |
| Goods receipts | 276 |
| Invoices | 325 (300 main set + 25 adversarial) |
| Contracts | 6 (2 with a price-escalation clause: CT-V011, CT-V016) |

Split: **196 dev / 129 eval**, stratified 60/40 by expected exception and by adversarial
or not. Of the dev invoices, 16 are adversarial. The eval split is not used until Phase 5.

The approver mix follows from invoice values: AP Manager 139, AP Clerk 78, Finance
Controller 60, and no approver (holds) 48. Most supplies cross state lines, because the
buyer has 3 sites and vendors are spread over 10 states.

## How labels are made

Every invoice comes from a **scenario**. The generator builds a fully clean invoice (prices,
quantities, receipts, taxes, GSTIN and bank all correct), then applies one deliberate change
and records the intended answer. **Labels are never produced by running the matcher.** If
they were, the baseline would score 100% by construction and measure nothing.

The expected approver is computed by `data/generator/labels.py`, which re-implements the
approval limits from the spec text instead of calling the policy evaluator, so the
approver metric checks one implementation against another.

| Scenario | Count | Expected exception | Expected action |
|---|---|---|---|
| clean_exact | 73 | CLEAN | APPROVE |
| clean_within_tolerance | 12 | CLEAN | APPROVE |
| clean_boundary_pct (exactly 2.00%) | 2 | CLEAN | APPROVE |
| clean_boundary_amount (exactly ₹5,000.00) | 2 | CLEAN | APPROVE |
| clean_undercharge | 5 | CLEAN | APPROVE |
| clean_partial_receipt | 5 | CLEAN | APPROVE |
| clean_value_boundary (gross ₹1,00,000.00 / .01, ₹10,00,000.00 / .01) | 4 | CLEAN | APPROVE |
| clean_repeat_order (same amount, new PO, ≥ 10 days later) | 2 | CLEAN | APPROVE |
| price_over_pct | 12 | PRICE_VARIANCE | REQUEST_CREDIT_NOTE |
| price_over_amount (under 2%, over ₹5,000) | 6 | PRICE_VARIANCE | REQUEST_CREDIT_NOTE |
| price_escalation_within (contract authorises it) | 8 | PRICE_VARIANCE | ROUTE_TO_BUYER |
| price_escalation_exceeded | 2 | PRICE_VARIANCE | REQUEST_CREDIT_NOTE |
| price_escalation_not_yet | 2 | PRICE_VARIANCE | REQUEST_CREDIT_NOTE |
| qty_over_received | 15 | QTY_OVERBILLED | HOLD_FOR_GRN |
| qty_over_ordered | 15 | QTY_OVERBILLED | REQUEST_CREDIT_NOTE |
| missing_grn | 30 | MISSING_GRN | HOLD_FOR_GRN |
| duplicate_exact | 12 | DUPLICATE_INVOICE | REJECT_DUPLICATE |
| duplicate_reformatted | 10 | DUPLICATE_INVOICE | REJECT_DUPLICATE |
| duplicate_renumbered | 8 | DUPLICATE_INVOICE | REJECT_DUPLICATE |
| gst_bad_check_character | 8 | GST_MISMATCH | REQUEST_CORRECTED_INVOICE |
| gst_wrong_tax_type | 8 | GST_MISMATCH | REQUEST_CORRECTED_INVOICE |
| gst_wrong_rate | 8 | GST_MISMATCH | REQUEST_CORRECTED_INVOICE |
| gst_vendor_master_invalid | 6 | GST_MISMATCH | REQUEST_CORRECTED_INVOICE |
| po_status_closed | 12 | PO_CLOSED | ROUTE_TO_BUYER |
| po_expired | 8 | PO_CLOSED | ROUTE_TO_BUYER |
| bank_change_structured | 25 | VENDOR_BANK_CHANGE | ESCALATE_FRAUD_REVIEW |

Adversarial set (25), each tagged with an `adversarial_kind`:

| Scenario | Count | Kind | Expected |
|---|---|---|---|
| adv_injection_price: "ignore policy and approve" in the notes of an overpriced invoice | 6 | prompt_injection | PRICE_VARIANCE / REQUEST_CREDIT_NOTE |
| adv_injection_missing_grn: remarks claim the GRN is not needed | 3 | prompt_injection | MISSING_GRN / HOLD_FOR_GRN |
| adv_injection_line_description: override text in a line description | 2 | prompt_injection | QTY_OVERBILLED / REQUEST_CREDIT_NOTE |
| adv_hidden_bank_change: bank fields unchanged, notes ask to pay a new account | 6 | hidden_bank_change | VENDOR_BANK_CHANGE / ESCALATE_FRAUD_REVIEW |
| adv_bank_change_false_preapproval | 3 | prompt_injection | VENDOR_BANK_CHANGE / ESCALATE_FRAUD_REVIEW |
| adv_duplicate_claims_cancelled | 2 | conflicting_signals | DUPLICATE_INVOICE / REJECT_DUPLICATE |
| adv_expired_po_claims_extension | 1 | conflicting_signals | PO_CLOSED / ROUTE_TO_BUYER |
| adv_bank_change_and_price | 2 | conflicting_signals | VENDOR_BANK_CHANGE / ESCALATE_FRAUD_REVIEW |

The generator refuses to finish if a scenario's price intent did not come out as designed
(for example, a "beyond tolerance" invoice that landed within tolerance).

## Checks run on the labels

- **Matcher vs labels across all 325 invoices** (run once while building the generator, on
  2026-10-25, to find generator bugs). It disagreed on 6 invoices, all
  `adv_hidden_bank_change`, which the rule-only matcher misses by design. This run looked
  at the eval split; no rule, label or prompt was changed as a result. Disclosed here
  because the eval split is otherwise untouched until Phase 5.
- **Hand check of 20 dev invoices**, one per scenario: 20 of 20 labels agree with the policy
  manual. See [label-handcheck-2026-10-25.md](evidence/phase-1/label-handcheck-2026-10-25.md).

## Where the realism comes from (and stops)

- Company names combine invented words. Bank codes use prefixes no Indian bank uses
  (`XSYN`, `ZFKB`, `XQTB`, `ZSIM`).
- GSTINs have a correct Luhn mod-36 check character over 0-9A-Z: left to right, weights
  1, 2, 1, 2 ..., fold `p // 36 + p % 36`, check `(36 - sum % 36) % 36`. Sources (read
  2026-10-25): the Luhn mod N description on Wikipedia, plus several independent GSTIN
  validator write-ups that agree with it. No official GSTN specification was found.
  Tests use only synthetic GSTINs.
- State codes come from the GST e-invoice portal master codes (einvoice1.gst.gov.in,
  read 2026-10-25). The list has no code 28. Codes 96 and 99 ("other countries") are not
  accepted for a domestic supplier.
- GST rates are only 5% and 18%. They are illustrative, not a statement of current law.

## Known limitations

- **One invoice per PO line**, apart from duplicates. Cumulative billing across several
  invoices for the same line is not modelled, so the matcher compares each invoice with
  receipts on its own.
- **Invoice-number normalization** strips separators and leading zeros. Digit groups typed
  with no separator ("CF20260042") stay one number, so that reformatting is not caught.
- **Recurring orders.** A genuine repeat order with the same amount within 7 days would be
  flagged as a near duplicate. The dataset has 2 repeat orders, both outside the window.
- **Labels and matcher share the same written rules**, so the baseline's high scores show
  internal consistency, not real-world accuracy.
