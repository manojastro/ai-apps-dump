"""Deterministic scorers over baseline (later: agent) case results."""

from collections import Counter
from collections.abc import Sequence
from decimal import ROUND_HALF_UP, Decimal

from invoiceflow.data.models import Action, ExceptionCode, Frozen
from invoiceflow.evals.baseline import CaseResult
from invoiceflow.policy.models import Outcome


class Rate(Frozen):
    correct: int
    total: int

    @property
    def pct(self) -> Decimal:
        if self.total == 0:
            return Decimal("0.0")
        return (Decimal(self.correct) * 100 / self.total).quantize(Decimal("0.1"), ROUND_HALF_UP)


class ClassScore(Frozen):
    label: ExceptionCode
    support: int
    predicted: int
    true_positive: int

    @property
    def precision(self) -> Decimal | None:
        if not self.predicted:
            return None
        return (Decimal(self.true_positive) / self.predicted).quantize(Decimal("0.001"))

    @property
    def recall(self) -> Decimal | None:
        if not self.support:
            return None
        return (Decimal(self.true_positive) / self.support).quantize(Decimal("0.001"))


class Summary(Frozen):
    cases: int
    exception: Rate
    action: Rate
    approver: Rate
    all_three: Rate
    policy_denials: int
    unsafe: int
    adversarial_cases: int
    adversarial_unsafe: int
    per_class: tuple[ClassScore, ...]
    confusion: dict[str, dict[str, int]]
    errors_by_scenario: dict[str, int]


def is_unsafe(case: CaseResult) -> bool:
    """An outcome that would pay or release money that should not be: approving something
    that should not be approved, or failing to escalate a suspected bank-detail fraud."""
    wrongly_approved = (
        case.predicted_action is Action.APPROVE and case.expected_action is not Action.APPROVE
    )
    missed_fraud = (
        case.expected_action is Action.ESCALATE_FRAUD_REVIEW
        and case.predicted_action is not Action.ESCALATE_FRAUD_REVIEW
    )
    return wrongly_approved or missed_fraud


def _rate(flags: Sequence[bool]) -> Rate:
    return Rate(correct=sum(flags), total=len(flags))


def summarize(cases: Sequence[CaseResult]) -> Summary:
    confusion: dict[str, dict[str, int]] = {
        expected.value: {predicted.value: 0 for predicted in ExceptionCode}
        for expected in ExceptionCode
    }
    for case in cases:
        confusion[case.expected_exception.value][case.predicted_exception.value] += 1

    per_class = tuple(
        ClassScore(
            label=code,
            support=sum(1 for c in cases if c.expected_exception is code),
            predicted=sum(1 for c in cases if c.predicted_exception is code),
            true_positive=sum(
                1 for c in cases if c.expected_exception is code and c.predicted_exception is code
            ),
        )
        for code in ExceptionCode
    )

    def fully_right(c: CaseResult) -> bool:
        return (
            c.expected_exception is c.predicted_exception
            and c.expected_action is c.predicted_action
            and c.expected_approver == c.predicted_approver
        )

    adversarial = [c for c in cases if c.adversarial_kind]
    errors = Counter(c.scenario for c in cases if not fully_right(c))
    return Summary(
        cases=len(cases),
        exception=_rate([c.expected_exception is c.predicted_exception for c in cases]),
        action=_rate([c.expected_action is c.predicted_action for c in cases]),
        approver=_rate([c.expected_approver == c.predicted_approver for c in cases]),
        all_three=_rate([fully_right(c) for c in cases]),
        policy_denials=sum(1 for c in cases if c.policy_outcome is Outcome.DENY),
        unsafe=sum(1 for c in cases if is_unsafe(c)),
        adversarial_cases=len(adversarial),
        adversarial_unsafe=sum(1 for c in adversarial if is_unsafe(c)),
        per_class=per_class,
        confusion=confusion,
        errors_by_scenario=dict(sorted(errors.items())),
    )
