"""Inputs and outputs of the policy evaluator."""

from enum import StrEnum
from typing import Literal

from invoiceflow.core.tolerance import PriceVariance
from invoiceflow.data.models import Action, ExceptionCode, Frozen, Money, Role


class Identity(Frozen):
    """Who prepared or approved something. Every non-human preparer counts as an agent,
    including the rule-only baseline."""

    id: str
    kind: Literal["human", "agent"]
    role: Role | None = None


class Approval(Frozen):
    approver: Identity


class Verification(Frozen):
    """An out-of-band check, such as calling the vendor on a number from the master file."""

    kind: Literal["BANK_DETAILS_CALLBACK"]
    performed_by: Identity


class Proposal(Frozen):
    invoice_id: str
    exception: ExceptionCode
    action: Action
    gross_value: Money
    price_variance: PriceVariance
    citations: tuple[str, ...]
    preparer: Identity


class Outcome(StrEnum):
    ALLOW = "ALLOW"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    DENY = "DENY"


class RuleResult(Frozen):
    """`fail` makes the decision DENY; `pending` means a human step is still missing."""

    rule_id: str
    status: Literal["pass", "fail", "pending"]
    message: str
    source: str


class PolicyDecision(Frozen):
    outcome: Outcome
    required_role: Role | None
    requires_out_of_band_verification: bool
    results: tuple[RuleResult, ...]
    matrix_version: str

    def result(self, rule_id: str) -> RuleResult | None:
        """The most severe result recorded for a rule (fail > pending > pass)."""
        severity = {"pass": 0, "pending": 1, "fail": 2}
        matches = [r for r in self.results if r.rule_id == rule_id]
        return max(matches, key=lambda r: severity[r.status], default=None)


class PolicyViolationError(RuntimeError):
    """Raised when something tries to execute a decision that policy does not allow."""
