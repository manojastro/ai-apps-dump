from __future__ import annotations

from datetime import date

from app.constants import RULES_VERSION
from app.engine.mathutil import clamp
from app.models.profile import HouseholdProfile, IPS


def _nearest_must_have_horizon(profile: HouseholdProfile) -> int:
    year = date.today().year
    must = [g for g in profile.goals if g.priority == "must_have"]
    pool = must or profile.goals
    if not pool:
        return 10
    return max(1, min(g.target_year - year for g in pool))


def build_ips(profile: HouseholdProfile) -> IPS:
    """Age may influence but never solely determines equity allocation."""
    horizon = profile.risk.goal_horizon_years or _nearest_must_have_horizon(profile)
    r = profile.risk
    # Capacity and stability weigh more than emotion; age is a mild modifier only.
    score = (
        r.emotional_tolerance * 8
        + r.financial_capacity * 14
        + r.income_stability * 12
        + r.investment_experience * 6
        + clamp(horizon, 1, 30) * 1.2
        + clamp((70 - profile.age) / 10.0, -2, 3) * 4
        - r.liquidity_need * 6
    )
    score = clamp(score, 0, 100)

    emi_total = sum(x.emi for x in profile.liabilities)
    emi_ratio = emi_total / profile.monthly_take_home_inr if profile.monthly_take_home_inr else 0
    sole_earner = profile.earners <= 1
    unstable = r.income_stability <= 2

    reserve_months = 6.0
    if unstable:
        reserve_months += 3
    if sole_earner:
        reserve_months += 1
    if emi_ratio >= 0.35:
        reserve_months += 2
    if profile.dependents >= 2:
        reserve_months += 1
    reserve_months = clamp(reserve_months, 3, 18)

    if score < 38:
        band = "conservative"
        ceiling = 35.0
        debt_floor = 45.0
        capacity = "low"
    elif score < 62:
        band = "moderate"
        ceiling = 55.0
        debt_floor = 30.0
        capacity = "moderate"
    else:
        band = "growth"
        ceiling = 70.0
        debt_floor = 20.0
        capacity = "high"

    if r.financial_capacity <= 2:
        ceiling = min(ceiling, 40.0)
        capacity = "low"
    if horizon <= 3:
        ceiling = min(ceiling, 25.0)
    if emi_ratio >= 0.25:
        ceiling = min(ceiling, ceiling - 10)
    if "existing_home_loan" in profile.constraints:
        ceiling = min(ceiling, 55.0)
    if profile.age >= 55:
        ceiling = min(ceiling, 45.0)
        debt_floor = max(debt_floor, 40.0)
    if "avoid_illiquid" in profile.constraints:
        debt_floor = max(debt_floor, 25.0)

    notes = [
        "Equity ceiling is derived from capacity, horizon, stability and constraints — not age alone.",
        f"Nearest material goal horizon used: {horizon} years.",
    ]
    if not profile.direct_equity_opt_in or "no_direct_stocks" in profile.constraints:
        notes.append("Direct single-stock positions are excluded from default simulations.")
    if not profile.vda_opt_in or "no_crypto" in profile.constraints:
        notes.append("VDA/crypto default allocation is 0%.")
    if not profile.international_opt_in or "no_international" in profile.constraints:
        notes.append("International assets are excluded unless the household opts in.")

    return IPS(
        risk_score=round(score, 1),
        risk_band=band,
        capacity_for_loss=capacity,
        equity_ceiling_pct=round(max(10.0, ceiling), 1),
        minimum_liquid_reserve_months=round(reserve_months, 1),
        required_debt_floor_pct=round(debt_floor, 1),
        goals=profile.goals,
        constraints=profile.constraints,
        tax_regime=profile.tax_regime,
        international_opt_in=profile.international_opt_in and "no_international" not in profile.constraints,
        direct_equity_opt_in=profile.direct_equity_opt_in and "no_direct_stocks" not in profile.constraints,
        vda_opt_in=profile.vda_opt_in and "no_crypto" not in profile.constraints,
        age=profile.age,
        first_name=profile.first_name,
        notes=notes,
        rules_version=RULES_VERSION,
    )
