from __future__ import annotations

from app.models.plan import PlanScenario, StressResult
from app.models.profile import HouseholdProfile, IPS


def run_stress(
    profile: HouseholdProfile,
    ips: IPS,
    scenario: PlanScenario,
    portfolio_value: float,
    reserve_inr: float,
) -> list[StressResult]:
    results: list[StressResult] = []
    equity_shock = -0.25 * (scenario.equity_pct / 100.0) * portfolio_value
    results.append(
        StressResult(
            name="equity_shock",
            description="Hypothetical equity -25% applied to the equity sleeve only.",
            impact_summary=f"Illustrative mark-to-market change ₹{equity_shock:,.0f}.",
            metrics={
                "equity_pct": scenario.equity_pct,
                "portfolio_drawdown_pct": round(25.0 * scenario.equity_pct / 100.0, 2),
                "inr_impact": round(equity_shock, 2),
            },
        )
    )
    if scenario.international_pct > 0:
        fx = -0.08 * (scenario.international_pct / 100.0) * portfolio_value
        results.append(
            StressResult(
                name="currency_shock",
                description="Hypothetical INR -8% versus USD on international sleeve only.",
                impact_summary=f"Illustrative FX translation impact ₹{fx:,.0f}.",
                metrics={"international_pct": scenario.international_pct, "inr_impact": round(fx, 2)},
            )
        )
    gold_move = 0.15 * (scenario.gold_pct / 100.0) * portfolio_value
    results.append(
        StressResult(
            name="gold_scenario",
            description="Hypothetical gold +15% on the gold sleeve.",
            impact_summary=f"Illustrative gold sleeve change ₹{gold_move:,.0f}.",
            metrics={"gold_pct": scenario.gold_pct, "inr_impact": round(gold_move, 2)},
        )
    )
    essential = (
        profile.essential_expenses_monthly_inr
        + profile.rent_monthly_inr
        + profile.insurance_premiums_monthly_inr
        + sum(x.emi for x in profile.liabilities)
    )
    months = (reserve_inr / essential) if essential > 0 else 0
    results.append(
        StressResult(
            name="income_shock",
            description=(
                "Hypothetical job loss for six months. SIPs paused. Essential expenses and EMIs continue."
            ),
            impact_summary=(
                f"Reserve covers about {months:.1f} months of essential outflow at ₹{essential:,.0f}/month."
            ),
            metrics={
                "reserve_inr": round(reserve_inr, 2),
                "monthly_essential_outflow": round(essential, 2),
                "reserve_survival_months": round(months, 2),
                "sip_paused": 1,
            },
        )
    )
    near_goals = [g for g in ips.goals if g.priority == "must_have"]
    if near_goals:
        results.append(
            StressResult(
                name="near_term_goal_impact",
                description="Near-term must-have goals remain funded only from liquid sleeves in this simulation.",
                impact_summary="Equity shock should not be assumed to fund a must-have goal due within three years.",
                metrics={"must_have_goals": float(len(near_goals))},
            )
        )
    return results
