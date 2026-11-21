from __future__ import annotations

from typing import Any

from app.models.plan import PlanScenario, RiskFinding
from app.models.profile import HouseholdProfile, IPS


def critique(
    profile: HouseholdProfile,
    ips: IPS,
    scenarios: list[PlanScenario],
    findings: list[RiskFinding],
) -> dict[str, Any]:
    by_name: dict[str, dict[str, Any]] = {}
    for s in scenarios:
        if s.name == "protect":
            argument_for = "Highest liquidity and the smallest equity drawdown in a -25% equity shock."
            argument_against = "Long-horizon goals may grow more slowly if inflation exceeds the cash/debt yield."
            change = "A much longer horizon with a completed reserve and higher loss capacity would weaken Protect's case."
        elif s.name == "balance":
            argument_for = "Keeps a debt floor and a diversified equity engine without treating Grow as better."
            argument_against = "Still experiences material equity drawdowns; not a capital-preservation mandate."
            change = "A three-year must-have goal or a reserve gap would argue for Protect instead."
        else:
            argument_for = "Uses more of the IPS equity ceiling for long-horizon surplus after policy checks."
            argument_against = "Largest hypothetical drawdown. Inappropriate when capacity or reserve is weak."
            change = "If loss capacity is low or a veto fires, Grow should be dropped, not relabelled as better."
        failure = [
            "Inflation higher than the cash/debt sleeve can support.",
            "Equity drawdown coinciding with a job-loss year.",
            "Tax or NPS rules changing versus this snapshot.",
            "A constraint (no international / no VDA / no direct equity) being ignored in real-world behaviour.",
            "Acting on this simulation as if it were an order or SEBI-regulated advice.",
        ]
        assumptions = [
            f"Tax regime treated as '{ips.tax_regime}'.",
            f"Equity ceiling {ips.equity_ceiling_pct}% from the IPS, not from age alone.",
            "No product is purchased or sold by this application.",
            "Jewellery is consumption, not an investment sleeve.",
            "Returns are not promised.",
        ]
        s.argument_for = argument_for
        s.argument_against = argument_against
        s.assumptions = assumptions
        s.failure_modes = failure
        s.what_would_change_conclusion = change
        by_name[s.name] = {
            "argument_for": argument_for,
            "argument_against": argument_against,
            "assumptions": assumptions,
            "failure_modes": failure,
            "what_would_change_conclusion": change,
        }
    return {
        "scenarios": by_name,
        "does_not_endorse_construction": True,
        "findings_count": len(findings),
        "household": profile.first_name,
    }
