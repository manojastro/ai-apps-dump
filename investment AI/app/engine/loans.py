from __future__ import annotations

from app.engine.mathutil import compound_future_value, remaining_interest
from app.models.profile import HouseholdProfile, Liability


def home_loan_of(profile: HouseholdProfile) -> Liability | None:
    for item in profile.liabilities:
        if item.type == "home_loan" and item.outstanding_balance > 0:
            return item
    return None


def prepay_vs_invest(
    loan: Liability,
    prepay_amount: float,
    years: float = 5.0,
) -> dict:
    """Compare guaranteed interest saved vs hypothetical investment outcomes. Not a recommendation."""
    prepay = min(prepay_amount, loan.outstanding_balance)
    interest_full = remaining_interest(
        loan.outstanding_balance, loan.interest_rate, loan.emi, loan.remaining_tenure_months
    )
    new_principal = max(0.0, loan.outstanding_balance - prepay)
    interest_after = remaining_interest(
        new_principal, loan.interest_rate, loan.emi, loan.remaining_tenure_months
    )
    guaranteed_saving = max(0.0, interest_full - interest_after)
    low = compound_future_value(prepay, 5.0, years)
    base = compound_future_value(prepay, 8.0, years)
    high = compound_future_value(prepay, 12.0, years)
    return {
        "outstanding_principal": loan.outstanding_balance,
        "interest_rate_pct": loan.interest_rate,
        "emi": loan.emi,
        "remaining_tenure_months": loan.remaining_tenure_months,
        "prepayment_amount": prepay,
        "guaranteed_interest_saving": round(guaranteed_saving, 2),
        "investment_horizon_years": years,
        "investment_outcomes_hypothetical": {
            "low_5pct": round(low, 2),
            "base_8pct": round(base, 2),
            "high_12pct": round(high, 2),
        },
        "note": (
            "Investment outcomes are hypothetical scenario returns, not expected or promised profit. "
            "Prepayment interest saving is contractual if applied to this loan. Neither choice is forced."
        ),
    }
