# Control matrix

> **SYNTHETIC EXAMPLE POLICY VALUES.** These numbers illustrate a typical Accounts Payable
> control set. They are not any real organization's policy.

The source of truth is [`policy/control_matrix.yaml`](../policy/control_matrix.yaml); this
page explains it. Each rule cites a section of the
[AP policy manual](../data/docs/ap_policy_manual.md) (AP-POL). The matrix is validated when
loaded: a typo, a missing exception, or limits that don't increase all fail loudly.

Every policy decision records the matrix version: the SHA-256 of its content, which is
currently `2c7e124e7de58a00cc3d77ae80a7f22090e31b0224b41568748c45632418c118`.

## Values

| Setting | Value | Source |
|---|---|---|
| Price tolerance | ≤ 2.00% **and** ≤ ₹5,000 per invoice (both inclusive) | AP-POL §4.2 |
| AP Clerk | up to ₹1,00,000 gross | AP-POL §3.1 |
| AP Manager | above ₹1,00,000, up to ₹10,00,000 | AP-POL §3.1 |
| Finance Controller | above ₹10,00,000 | AP-POL §3.1 |
| Near-duplicate window | 7 days | AP-POL §5.2 |
| GST rounding allowance | ₹1 per tax component | AP-POL §6.1 |
| Actions that need no human approval | HOLD_FOR_GRN | AP-POL §8.2 |
| Never approve | AUDITOR, PLATFORM_ADMIN, and every non-human identity | AP-POL §2.3 |

## Allowed and default actions per exception

| Exception | Allowed actions | Default |
|---|---|---|
| CLEAN | APPROVE, ESCALATE_FRAUD_REVIEW | APPROVE |
| PRICE_VARIANCE | REQUEST_CREDIT_NOTE, ROUTE_TO_BUYER, ESCALATE_FRAUD_REVIEW | REQUEST_CREDIT_NOTE |
| QTY_OVERBILLED | HOLD_FOR_GRN, REQUEST_CREDIT_NOTE, ESCALATE_FRAUD_REVIEW | HOLD_FOR_GRN; REQUEST_CREDIT_NOTE if more than ordered |
| MISSING_GRN | HOLD_FOR_GRN, ESCALATE_FRAUD_REVIEW | HOLD_FOR_GRN |
| DUPLICATE_INVOICE | REJECT_DUPLICATE, ESCALATE_FRAUD_REVIEW | REJECT_DUPLICATE |
| GST_MISMATCH | REQUEST_CORRECTED_INVOICE, ESCALATE_FRAUD_REVIEW | REQUEST_CORRECTED_INVOICE |
| PO_CLOSED | ROUTE_TO_BUYER, ESCALATE_FRAUD_REVIEW | ROUTE_TO_BUYER |
| VENDOR_BANK_CHANGE | ESCALATE_FRAUD_REVIEW only (Finance Controller + call-back) | ESCALATE_FRAUD_REVIEW |

Any other exception/action pair is denied. A test checks every such pair.

## Rules

Each rule has at least one allow test and one deny test in
[`tests/policy/test_rules.py`](../tests/policy/test_rules.py).
[`test_rule_coverage.py`](../tests/policy/test_rule_coverage.py) fails if a rule lacks either.

| Rule | What it enforces | Source |
|---|---|---|
| CM-01 | APPROVE with a price variance only within tolerance, even if the exception says CLEAN | AP-POL §4.2 |
| CM-02 | The approver's authority follows the gross invoice value | AP-POL §3.1 |
| CM-03 | Vendor bank change: escalate only, Finance Controller plus out-of-band verification | AP-POL §7.2 |
| CM-04 | REJECT_DUPLICATE needs at least AP Clerk confirmation | AP-POL §5.3 |
| CM-05 | Segregation of duties: the approver differs from the preparer | AP-POL §2.2 |
| CM-06 | The agent, Auditors and Platform Admins never approve | AP-POL §2.3 |
| CM-07 | No write action without ALLOW and every required approval (the executor's gate) | AP-POL §10.1 |
| CM-08 | Every decision cites at least one policy or contract source | AP-POL §9.1 |
| CM-09 | The action must be allowed for the exception | AP-POL §4.1 |
| CM-10 | Only listed reversible actions skip human approval | AP-POL §8.2 |

## How a decision is formed

`evaluate(proposal, matrix, approvals, verifications)` returns one of three outcomes:

- **DENY**: a rule failed (wrong action, missing citation, self-approval, the agent as
  approver, APPROVE beyond tolerance, or a bank change not escalated). Nothing may run.
- **REQUIRE_APPROVAL**: nothing failed, but a human step is still missing, such as an
  approver with enough authority or the bank call-back.
- **ALLOW**: every rule passed and every required human step is recorded.

The result lists every rule checked, with its status (`pass`, `fail` or `pending`), a
message and its source. `require_allow(decision)` raises unless the outcome is ALLOW. The
Phase 4 executor calls it before every write.

## Interpretations approved for Phase 1 (2026-10-25)

1. Tolerance is measured per invoice: total overcharge ≤ ₹5,000 and ≤ 2% of the PO value
   of the invoiced quantities.
2. An invoice priced below the PO is not a variance.
3. Approval limits use the gross value including GST.
4. "Up to" is inclusive and "above" is exclusive. Limits apply to every resolution.
5. A higher role satisfies a lower requirement.
6. HOLD_FOR_GRN runs on ALLOW without a human approval; everything else needs one.
7. Severity order for the primary exception: bank change > duplicate > PO closed >
   missing GRN > quantity overbilled > price variance > GST mismatch.
8. Default actions as in the table above, plus ROUTE_TO_BUYER for a contract-authorised
   price escalation.
9. **Duplicates (corrected).** Exact: same vendor and the same normalized number, on any
   date. Near: same vendor, same gross, invoice dates ≤ 7 days apart, and a **different**
   normalized number. The approved text said "equal after normalizing" for near
   duplicates, which made the rule redundant with the exact rule. The implementation
   follows the spec's wording instead ("same amount and date window, different number
   format"). **Pending Manoj's confirmation.**
10. A bank change requested only in invoice notes counts as a vendor bank change. The
    rule-only matcher cannot see it; the agent must.
