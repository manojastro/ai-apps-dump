"""Expected approver for a label, written directly from the spec (Section 4).

Deliberately independent of `invoiceflow.policy`: if both were the same code, the baseline's
approver accuracy would only measure the evaluator against itself. A shared misreading of
the spec would still slip through both, which is why the docs record the interpretation.
"""

from decimal import Decimal

from invoiceflow.data.models import Action, ExceptionCode, Role

CLERK_LIMIT = Decimal("100000.00")  # "AP Clerk may approve ... up to ₹1,00,000"
MANAGER_LIMIT = Decimal("1000000.00")  # "Finance Controller is required above ₹10,00,000"


def expected_approver(action: Action, exception: ExceptionCode, gross: Decimal) -> Role | None:
    if action is Action.HOLD_FOR_GRN:
        return None  # reversible hold, executes without approval (interpretation 6)
    if exception is ExceptionCode.VENDOR_BANK_CHANGE:
        return Role.FINANCE_CONTROLLER
    if gross <= CLERK_LIMIT:
        return Role.AP_CLERK
    if gross <= MANAGER_LIMIT:
        return Role.AP_MANAGER
    return Role.FINANCE_CONTROLLER
