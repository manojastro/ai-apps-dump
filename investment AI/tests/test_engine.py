from app.engine.allocations import construct_scenarios
from app.engine.ips import build_ips
from app.engine.mathutil import remaining_interest, weights_sum_ok
from app.data.fixtures import mock_candidates
from app.models.profile import HouseholdProfile


def test_weights_sum_to_100(household_2: HouseholdProfile):
    ips = build_ips(household_2)
    scenarios = construct_scenarios(ips, 1_000_000, 20_000, mock_candidates())
    assert len(scenarios) == 3
    for s in scenarios:
        mapping = {w.sleeve: w.weight_pct for w in s.weights}
        assert weights_sum_ok(mapping)
        assert abs(s.equity_pct + s.fixed_income_pct + s.cash_pct + s.gold_pct + s.alternatives_pct + s.international_pct - 100) <= 0.05


def test_ips_not_age_alone():
    from copy import deepcopy

    def profile(age, capacity, horizon):
        return HouseholdProfile(
            first_name="X",
            age=age,
            monthly_take_home_inr=100000,
            essential_expenses_monthly_inr=20000,
            risk={
                "emotional_tolerance": 3,
                "financial_capacity": capacity,
                "income_stability": 4,
                "investment_experience": 3,
                "liquidity_need": 2,
                "goal_horizon_years": horizon,
            },
            tax_regime="new",
        )

    young_low = build_ips(profile(25, 1, 2))
    old_high = build_ips(profile(60, 5, 20))
    assert young_low.equity_ceiling_pct <= old_high.equity_ceiling_pct or young_low.capacity_for_loss == "low"


def test_loan_interest_positive():
    interest = remaining_interest(1_000_000, 8.0, 9000, 120)
    assert interest > 0
