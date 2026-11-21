"""One allow test and one deny test per control-matrix rule, plus exhaustive denial checks.

Each test names the rule it covers with `@pytest.mark.rule(rule_id, "allow" | "deny")`;
tests/policy/test_rule_coverage.py fails if any rule lacks either kind.
"""

from decimal import Decimal as D

import pytest
from hypothesis import given
from hypothesis import strategies as st

from invoiceflow.core.tolerance import PriceVariance
from invoiceflow.data.models import Action, ExceptionCode, Role
from invoiceflow.policy.evaluator import evaluate, require_allow
from invoiceflow.policy.matrix import load_matrix
from invoiceflow.policy.models import (
    Approval,
    Identity,
    Outcome,
    PolicyDecision,
    PolicyViolationError,
    Proposal,
    Verification,
)

MATRIX = load_matrix()
AGENT = Identity(id="agent-invoiceflow", kind="agent")
CLERK = Identity(id="u-clerk-1", kind="human", role=Role.AP_CLERK)
CLERK_2 = Identity(id="u-clerk-2", kind="human", role=Role.AP_CLERK)
MANAGER = Identity(id="u-manager-1", kind="human", role=Role.AP_MANAGER)
CONTROLLER = Identity(id="u-fc-1", kind="human", role=Role.FINANCE_CONTROLLER)
AUDITOR = Identity(id="u-audit-1", kind="human", role=Role.AUDITOR)
ADMIN = Identity(id="u-admin-1", kind="human", role=Role.PLATFORM_ADMIN)
NO_VARIANCE = PriceVariance(
    overcharge_amount=D("0"), base_amount=D("1000"), overcharge_pct=D("0"), within_tolerance=True
)
OVER_TOLERANCE = PriceVariance(
    overcharge_amount=D("201.00"),
    base_amount=D("10000.00"),
    overcharge_pct=D("2.0100"),
    within_tolerance=False,
)
CALLBACK = Verification(kind="BANK_DETAILS_CALLBACK", performed_by=CLERK_2)


def proposal(
    exception: ExceptionCode = ExceptionCode.CLEAN,
    action: Action = Action.APPROVE,
    gross: str = "50000.00",
    variance: PriceVariance = NO_VARIANCE,
    citations: tuple[str, ...] = ("AP-POL §4.1",),
    preparer: Identity = AGENT,
) -> Proposal:
    return Proposal(
        invoice_id="INV-0001",
        exception=exception,
        action=action,
        gross_value=D(gross),
        price_variance=variance,
        citations=citations,
        preparer=preparer,
    )


def decide(
    p: Proposal, *approvers: Identity, verifications: tuple[Verification, ...] = ()
) -> PolicyDecision:
    return evaluate(p, MATRIX, [Approval(approver=a) for a in approvers], verifications)


def status(decision: PolicyDecision, rule_id: str) -> str | None:
    result = decision.result(rule_id)
    return result.status if result else None


# CM-01 price tolerance -------------------------------------------------------------------


@pytest.mark.rule("CM-01", "allow")
def test_cm01_approve_within_tolerance() -> None:
    decision = decide(proposal(), CLERK)
    assert decision.outcome is Outcome.ALLOW
    assert status(decision, "CM-01") == "pass"


@pytest.mark.rule("CM-01", "deny")
def test_cm01_approve_beyond_tolerance_is_denied_even_if_labeled_clean() -> None:
    decision = decide(proposal(variance=OVER_TOLERANCE), CLERK)
    assert decision.outcome is Outcome.DENY
    assert status(decision, "CM-01") == "fail"


# CM-02 approval limits -------------------------------------------------------------------


@pytest.mark.rule("CM-02", "allow")
@pytest.mark.parametrize(
    ("gross", "approver", "required"),
    [
        ("100000.00", CLERK, Role.AP_CLERK),
        ("100000.01", MANAGER, Role.AP_MANAGER),
        ("1000000.00", MANAGER, Role.AP_MANAGER),
        ("1000000.01", CONTROLLER, Role.FINANCE_CONTROLLER),
        ("500.00", CONTROLLER, Role.AP_CLERK),  # a higher role satisfies a lower requirement
    ],
)
def test_cm02_sufficient_authority_is_allowed(
    gross: str, approver: Identity, required: Role
) -> None:
    decision = decide(proposal(gross=gross), approver)
    assert decision.outcome is Outcome.ALLOW
    assert decision.required_role is required


@pytest.mark.rule("CM-02", "deny")
@pytest.mark.parametrize(
    ("gross", "approver", "required"),
    [
        ("100000.01", CLERK, Role.AP_MANAGER),
        ("1000000.01", MANAGER, Role.FINANCE_CONTROLLER),
    ],
)
def test_cm02_insufficient_authority_is_not_executable(
    gross: str, approver: Identity, required: Role
) -> None:
    decision = decide(proposal(gross=gross), approver)
    assert decision.outcome is Outcome.REQUIRE_APPROVAL
    assert decision.required_role is required
    assert status(decision, "CM-02") == "pending"


# CM-03 vendor bank change ----------------------------------------------------------------


def bank_change(action: Action = Action.ESCALATE_FRAUD_REVIEW) -> Proposal:
    return proposal(exception=ExceptionCode.VENDOR_BANK_CHANGE, action=action, gross="1000.00")


@pytest.mark.rule("CM-03", "allow")
def test_cm03_escalation_with_controller_and_callback_is_allowed() -> None:
    decision = decide(bank_change(), CONTROLLER, verifications=(CALLBACK,))
    assert decision.outcome is Outcome.ALLOW
    assert decision.required_role is Role.FINANCE_CONTROLLER
    assert decision.requires_out_of_band_verification


@pytest.mark.rule("CM-03", "deny")
@pytest.mark.parametrize("action", [Action.APPROVE, Action.REQUEST_CORRECTED_INVOICE])
def test_cm03_bank_change_can_only_be_escalated(action: Action) -> None:
    decision = decide(bank_change(action), CONTROLLER, verifications=(CALLBACK,))
    assert decision.outcome is Outcome.DENY
    assert status(decision, "CM-03") == "fail"


@pytest.mark.rule("CM-03", "deny")
def test_cm03_escalation_without_verification_waits() -> None:
    decision = decide(bank_change(), CONTROLLER)
    assert decision.outcome is Outcome.REQUIRE_APPROVAL
    assert status(decision, "CM-03") == "pending"


@pytest.mark.rule("CM-03", "deny")
def test_cm03_needs_finance_controller_even_for_small_invoices() -> None:
    decision = decide(bank_change(), MANAGER, verifications=(CALLBACK,))
    assert decision.outcome is Outcome.REQUIRE_APPROVAL
    assert decision.required_role is Role.FINANCE_CONTROLLER


@pytest.mark.rule("CM-03", "deny")
def test_cm03_verification_by_the_agent_does_not_count() -> None:
    by_agent = Verification(kind="BANK_DETAILS_CALLBACK", performed_by=AGENT)
    decision = decide(bank_change(), CONTROLLER, verifications=(by_agent,))
    assert decision.outcome is Outcome.REQUIRE_APPROVAL


# CM-04 duplicate rejection ---------------------------------------------------------------


def reject_duplicate(gross: str = "1000.00") -> Proposal:
    return proposal(
        exception=ExceptionCode.DUPLICATE_INVOICE, action=Action.REJECT_DUPLICATE, gross=gross
    )


@pytest.mark.rule("CM-04", "allow")
def test_cm04_clerk_confirms_duplicate_rejection() -> None:
    decision = decide(reject_duplicate(), CLERK)
    assert decision.outcome is Outcome.ALLOW
    assert status(decision, "CM-04") == "pass"


@pytest.mark.rule("CM-04", "deny")
def test_cm04_duplicate_rejection_without_confirmation_waits() -> None:
    decision = decide(reject_duplicate())
    assert decision.outcome is Outcome.REQUIRE_APPROVAL
    assert decision.required_role is Role.AP_CLERK


# CM-05 segregation of duties -------------------------------------------------------------


@pytest.mark.rule("CM-05", "allow")
def test_cm05_different_person_approves() -> None:
    assert decide(proposal(preparer=CLERK), CLERK_2).outcome is Outcome.ALLOW


@pytest.mark.rule("CM-05", "deny")
def test_cm05_preparer_cannot_approve_own_proposal() -> None:
    decision = decide(proposal(preparer=CLERK), CLERK)
    assert decision.outcome is Outcome.DENY
    assert status(decision, "CM-05") == "fail"


@given(
    role=st.sampled_from([Role.AP_CLERK, Role.AP_MANAGER, Role.FINANCE_CONTROLLER]),
    gross=st.decimals(min_value=0, max_value=10**8, places=2, allow_nan=False),
)
def test_cm05_property_self_approval_is_always_denied(role: Role, gross: D) -> None:
    person = Identity(id="u-same", kind="human", role=role)
    decision = decide(proposal(preparer=person, gross=str(gross)), person)
    assert decision.outcome is Outcome.DENY


# CM-06 who can never approve -------------------------------------------------------------


@pytest.mark.rule("CM-06", "allow")
def test_cm06_human_ap_role_can_approve() -> None:
    assert decide(proposal(), CLERK).outcome is Outcome.ALLOW


@pytest.mark.rule("CM-06", "deny")
@pytest.mark.parametrize("approver", [AGENT, AUDITOR, ADMIN])
def test_cm06_agent_auditor_admin_approval_is_denied(approver: Identity) -> None:
    decision = decide(proposal(preparer=CLERK), approver)
    assert decision.outcome is Outcome.DENY
    assert status(decision, "CM-06") == "fail"


@given(gross=st.decimals(min_value=0, max_value=10**8, places=2, allow_nan=False))
def test_cm06_property_agent_approval_is_always_denied(gross: D) -> None:
    decision = decide(proposal(preparer=CLERK, gross=str(gross)), AGENT)
    assert decision.outcome is Outcome.DENY


# CM-07 execution gate --------------------------------------------------------------------


@pytest.mark.rule("CM-07", "allow")
def test_cm07_allow_passes_the_gate() -> None:
    require_allow(decide(proposal(), CLERK))


@pytest.mark.rule("CM-07", "deny")
@pytest.mark.parametrize("approvers", [(), (AGENT,)])
def test_cm07_anything_but_allow_is_blocked(approvers: tuple[Identity, ...]) -> None:
    decision = decide(proposal(), *approvers)
    assert decision.outcome is not Outcome.ALLOW
    with pytest.raises(PolicyViolationError):
        require_allow(decision)


# CM-08 citations -------------------------------------------------------------------------


@pytest.mark.rule("CM-08", "allow")
def test_cm08_cited_decision_passes() -> None:
    assert status(decide(proposal(), CLERK), "CM-08") == "pass"


@pytest.mark.rule("CM-08", "deny")
@pytest.mark.parametrize("citations", [(), ("",), ("   ",)])
def test_cm08_uncited_decision_is_denied(citations: tuple[str, ...]) -> None:
    decision = decide(proposal(citations=citations), CLERK)
    assert decision.outcome is Outcome.DENY
    assert status(decision, "CM-08") == "fail"


# CM-09 action must fit the exception -----------------------------------------------------


@pytest.mark.rule("CM-09", "allow")
def test_cm09_hold_for_missing_grn_is_allowed() -> None:
    decision = decide(proposal(exception=ExceptionCode.MISSING_GRN, action=Action.HOLD_FOR_GRN))
    assert decision.outcome is Outcome.ALLOW


@pytest.mark.rule("CM-09", "deny")
def test_cm09_approve_for_missing_grn_is_denied() -> None:
    decision = decide(proposal(exception=ExceptionCode.MISSING_GRN), CLERK)
    assert decision.outcome is Outcome.DENY
    assert status(decision, "CM-09") == "fail"


DISALLOWED = [
    (exception, action)
    for exception in ExceptionCode
    for action in Action
    if action not in MATRIX.exceptions[exception].allowed_actions
]


@pytest.mark.parametrize(("exception", "action"), DISALLOWED)
def test_cm09_every_disallowed_pair_is_denied(exception: ExceptionCode, action: Action) -> None:
    decision = decide(proposal(exception=exception, action=action), CONTROLLER)
    assert decision.outcome is Outcome.DENY


# CM-10 approval exemption ----------------------------------------------------------------


@pytest.mark.rule("CM-10", "allow")
def test_cm10_hold_executes_without_human_approval() -> None:
    decision = decide(proposal(exception=ExceptionCode.MISSING_GRN, action=Action.HOLD_FOR_GRN))
    assert decision.outcome is Outcome.ALLOW
    assert decision.required_role is None
    assert status(decision, "CM-10") == "pass"


@pytest.mark.rule("CM-10", "deny")
def test_cm10_approve_without_human_approval_waits() -> None:
    decision = decide(proposal())
    assert decision.outcome is Outcome.REQUIRE_APPROVAL
    assert status(decision, "CM-10") == "pending"


def test_every_decision_records_the_matrix_version() -> None:
    assert decide(proposal(), CLERK).matrix_version == MATRIX.version_hash
