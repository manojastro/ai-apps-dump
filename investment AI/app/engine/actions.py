from __future__ import annotations

from app.models.plan import MonthlyAction, PlanScenario
from app.models.profile import HouseholdProfile, IPS


def five_actions(
    profile: HouseholdProfile,
    ips: IPS,
    scenario: PlanScenario,
    reserve_gap: float,
    insurance_gap_note: str | None,
    has_home_loan: bool,
) -> list[MonthlyAction]:
    actions: list[MonthlyAction] = []
    surplus = (
        profile.monthly_take_home_inr
        - profile.essential_expenses_monthly_inr
        - profile.discretionary_expenses_monthly_inr
        - profile.insurance_premiums_monthly_inr
        - profile.rent_monthly_inr
        - sum(x.emi for x in profile.liabilities)
    )
    if reserve_gap > 0:
        move = min(max(surplus, 0), reserve_gap)
        actions.append(
            MonthlyAction(
                title="Top up the emergency reserve",
                detail=(
                    f"Move about ₹{move:,.0f} this month toward liquid reserve until the "
                    f"{ips.minimum_liquid_reserve_months:.0f}-month policy target is met."
                ),
                amount_inr=round(move, 2),
                kind="reserve",
            )
        )
    else:
        actions.append(
            MonthlyAction(
                title="Keep the reserve intact",
                detail="Emergency reserve meets the current policy target. Avoid drawing it for discretionary spending.",
                kind="reserve",
            )
        )
    actions.append(
        MonthlyAction(
            title="Continue existing regulated contributions",
            detail=(
                "Continue EPF/VPF or existing SIPs already in place. This is not an instruction to start a new fund."
            ),
            kind="contribute",
        )
    )
    actions.append(
        MonthlyAction(
            title="Review protection cover",
            detail=insurance_gap_note
            or "Estimate term and health cover against dependents and essential expenses. Figures are educational estimates.",
            kind="review",
        )
    )
    if reserve_gap > 0:
        actions.append(
            MonthlyAction(
                title="Avoid increasing equity until reserve target is reached",
                detail="Policy blocks using surplus to raise the equity sleeve while the liquid reserve is short.",
                kind="avoid",
            )
        )
    else:
        actions.append(
            MonthlyAction(
                title="Keep surplus aligned to the selected simulation",
                detail=(
                    f"If cash-flow allows, the {scenario.label} simulation directs about "
                    f"₹{scenario.monthly_contribution_inr:,.0f}/month after expenses. This is a planning number, not an order."
                ),
                amount_inr=scenario.monthly_contribution_inr,
                kind="contribute",
            )
        )
    if has_home_loan:
        actions.append(
            MonthlyAction(
                title="Compare a home-loan prepayment scenario",
                detail="Run the prepay-versus-invest calculator with a surplus amount you actually have. Neither path is forced.",
                kind="compare",
            )
        )
    else:
        actions.append(
            MonthlyAction(
                title="Write down one constraint to reconfirm",
                detail="Reconfirm product prohibitions (direct equity, international, VDA) before any real-world action outside this app.",
                kind="review",
            )
        )
    return actions[:5]


def protection_notes(profile: HouseholdProfile) -> list[str]:
    essential_annual = (
        profile.essential_expenses_monthly_inr + profile.rent_monthly_inr
    ) * 12
    term_gap = max(0.0, essential_annual * 10 - 0)
    health = 500_000 if profile.dependents else 300_000
    return [
        f"Educational term-cover gap sketch: about ₹{term_gap:,.0f} of cover relative to ~10 years of essential outflow. Estimate only.",
        f"Educational health-cover sketch: consider whether existing cover is below ₹{health:,.0f} family floater equivalent. Estimate only.",
        "Protection is not an investment-return sleeve and is not allocated inside Protect/Balance/Grow weights.",
    ]
