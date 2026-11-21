"""Rule-only baseline: matcher -> default action from the control matrix -> policy evaluator.

No LLM and no free text. Reads data only through the APDataReader port, so it runs the same
on the in-memory and Postgres backends. This is the bar the agent has to beat in Phase 5.
"""

from collections.abc import Sequence

from invoiceflow.core.matcher import match_invoice
from invoiceflow.data.models import Action, ExceptionCode, Frozen, GroundTruth, Role, Split
from invoiceflow.policy.evaluator import evaluate
from invoiceflow.policy.matrix import ControlMatrix
from invoiceflow.policy.models import Identity, Outcome, Proposal
from invoiceflow.ports.data import APDataReader

BASELINE_IDENTITY = Identity(id="rule-baseline", kind="agent")


class HeldOutSplitError(RuntimeError):
    """The eval split stays untouched until Phase 5, so nothing is tuned on it."""


class CaseResult(Frozen):
    invoice_id: str
    scenario: str
    adversarial_kind: str | None
    expected_exception: ExceptionCode
    predicted_exception: ExceptionCode
    expected_action: Action
    predicted_action: Action
    expected_approver: Role | None
    predicted_approver: Role | None
    policy_outcome: Outcome
    finding_reasons: tuple[str, ...]


def run_baseline(
    reader: APDataReader,
    labels: Sequence[GroundTruth],
    matrix: ControlMatrix,
    split: Split = Split.DEV,
) -> tuple[CaseResult, ...]:
    if split is not Split.DEV or any(label.split is not Split.DEV for label in labels):
        raise HeldOutSplitError("the held-out eval split is locked until Phase 5")
    params = matrix.match_params()
    results = []
    for label in sorted(labels, key=lambda lbl: lbl.invoice_id):
        invoice = reader.get_invoice(label.invoice_id)
        match = match_invoice(
            invoice,
            reader.get_purchase_order(invoice.po_id),
            reader.get_goods_receipts(invoice.po_id),
            reader.get_vendor(invoice.vendor_id),
            reader.prior_invoices(invoice),
            params,
        )
        action = matrix.default_action(match.primary, match.findings)
        decision = evaluate(
            Proposal(
                invoice_id=invoice.invoice_id,
                exception=match.primary,
                action=action,
                gross_value=invoice.gross_total,
                price_variance=match.price_variance,
                citations=(matrix.exceptions[match.primary].source,),
                preparer=BASELINE_IDENTITY,
            ),
            matrix,
        )
        results.append(
            CaseResult(
                invoice_id=invoice.invoice_id,
                scenario=label.scenario,
                adversarial_kind=label.adversarial_kind,
                expected_exception=label.expected_exception,
                predicted_exception=match.primary,
                expected_action=label.expected_action,
                predicted_action=action,
                expected_approver=label.expected_required_approver,
                predicted_approver=decision.required_role,
                policy_outcome=decision.outcome,
                finding_reasons=tuple(f.reason.value for f in match.findings),
            )
        )
    return tuple(results)
