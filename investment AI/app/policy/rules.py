from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import get_settings
from app.models.plan import Candidate, PlanScenario, RiskFinding, Veto
from app.models.profile import Holding, HouseholdProfile, IPS

RULES_VERSION = "1.0.0"

FORBIDDEN_VEHICLES = {"chit_fund", "unlisted", "speculative_ncd"}
FORBIDDEN_NAME_HINTS = ("chit fund", "guaranteed 18", "telegram tip", "whatsapp tip")


@dataclass
class PolicyResult:
    findings: list[RiskFinding]
    vetoes: list[Veto]
    status: str
    scenarios: list[PlanScenario]


def _source_coverage(scenario: PlanScenario, candidates: list[Candidate]) -> float:
    verified_names = {c.name for c in candidates if c.verification in {"verified", "stale"}}
    if not scenario.weights:
        return 100.0
    covered = 0.0
    total = 0.0
    for sleeve in scenario.weights:
        total += sleeve.weight_pct
        if sleeve.sleeve in {"cash", "fixed_income", "equity", "gold"}:
            if sleeve.example_vehicles and any(v in verified_names for v in sleeve.example_vehicles):
                covered += sleeve.weight_pct
            elif sleeve.example_vehicles:
                covered += sleeve.weight_pct * 0.5
            else:
                covered += sleeve.weight_pct
        else:
            covered += sleeve.weight_pct
    if total <= 0:
        return 100.0
    return round(100.0 * covered / total, 2)


def evaluate_policy(
    profile: HouseholdProfile,
    ips: IPS,
    holdings: list[Holding],
    scenarios: list[PlanScenario],
    candidates: list[Candidate],
    *,
    source_coverage_override: dict[str, float] | None = None,
) -> PolicyResult:
    settings = get_settings()
    findings: list[RiskFinding] = []
    vetoes: list[Veto] = []

    essential = profile.essential_expenses_monthly_inr + profile.rent_monthly_inr
    liquid = sum(h.current_value_inr for h in holdings if h.category in {"cash_safety"} and not h.locked)
    target = ips.minimum_liquid_reserve_months * essential
    gap = max(0.0, target - liquid)
    if gap > 0:
        findings.append(
            RiskFinding(
                rule_id="RISK-01",
                status="PASS_WITH_CONDITIONS",
                title="Emergency reserve below policy target",
                detail=(
                    f"Liquid reserve ₹{liquid:,.0f} vs target ₹{target:,.0f} "
                    f"({ips.minimum_liquid_reserve_months:.0f} months of essentials)."
                ),
                metadata={"gap": gap, "target": target, "liquid": liquid},
            )
        )
        for s in scenarios:
            s.risk_flags.append("emergency_reserve_short")
    else:
        findings.append(
            RiskFinding(
                rule_id="RISK-01",
                status="PASS",
                title="Emergency reserve meets policy",
                detail=f"Liquid reserve ₹{liquid:,.0f} meets ₹{target:,.0f} target.",
                metadata={"gap": 0, "target": target, "liquid": liquid},
            )
        )

    thin_reserve = (liquid / essential) < 3 if essential else True
    for s in scenarios:
        if s.alternatives_pct > 0.05 and thin_reserve:
            vetoes.append(
                Veto(
                    code="VDA_RESERVE",
                    rule_id="RISK-02",
                    message="Speculative sleeves cannot underpin a household plan while emergency savings are below 3 months.",
                )
            )
            findings.append(
                RiskFinding(
                    rule_id="RISK-02",
                    status="VETO",
                    title="Speculative allocation rejected",
                    detail="Emergency savings are too thin for a VDA/crypto sleeve.",
                    metadata={"reserve_months": liquid / essential if essential else 0},
                )
            )
        if s.alternatives_pct > 0.05 and not ips.vda_opt_in:
            vetoes.append(
                Veto(
                    code="VDA_DEFAULT_ZERO",
                    rule_id="RISK-02",
                    message="VDA/crypto allocation must be 0% unless the household explicitly opts in.",
                )
            )
            findings.append(
                RiskFinding(
                    rule_id="RISK-02",
                    status="VETO",
                    title="Speculative sleeve without opt-in",
                    detail=f"{s.label} has alternatives {s.alternatives_pct}% without VDA opt-in.",
                )
            )
        elif ips.vda_opt_in and s.alternatives_pct > settings.vda_opt_in_cap_pct + 0.05:
            vetoes.append(
                Veto(
                    code="VDA_CAP",
                    rule_id="RISK-02",
                    message=f"VDA sleeve exceeds configurable cap of {settings.vda_opt_in_cap_pct}%.",
                )
            )
            findings.append(
                RiskFinding(
                    rule_id="RISK-02",
                    status="VETO",
                    title="VDA cap exceeded",
                    detail=f"{s.label} alternatives {s.alternatives_pct}% > cap {settings.vda_opt_in_cap_pct}%.",
                )
            )

    total_value = sum(h.current_value_inr for h in holdings) or 1.0
    for h in holdings:
        share = 100.0 * h.current_value_inr / total_value
        if share > settings.concentration_cap_pct and h.category not in {"retirement"}:
            findings.append(
                RiskFinding(
                    rule_id="RISK-03",
                    status="PASS_WITH_CONDITIONS",
                    title="Concentration above cap",
                    detail=f"{h.name} is {share:.1f}% of holdings versus cap {settings.concentration_cap_pct}%.",
                    metadata={"holding": h.name, "share": share},
                )
            )

    constraint_violations = _constraint_violations(ips, scenarios, holdings)
    for msg in constraint_violations:
        vetoes.append(Veto(code="HARD_CONSTRAINT", rule_id="RISK-04", message=msg))
        findings.append(
            RiskFinding(rule_id="RISK-04", status="VETO", title="Hard constraint violated", detail=msg)
        )

    for s in scenarios:
        coverage = (source_coverage_override or {}).get(s.name, _source_coverage(s, candidates))
        s.source_coverage_pct = coverage
        unverified_share = max(0.0, 100.0 - coverage)
        if unverified_share > settings.source_coverage_veto_pct:
            vetoes.append(
                Veto(
                    code="SOURCE_COVERAGE",
                    rule_id="RISK-05",
                    message=(
                        f"More than {settings.source_coverage_veto_pct}% of {s.label} depends on unverified data."
                    ),
                )
            )
            findings.append(
                RiskFinding(
                    rule_id="RISK-05",
                    status="VETO",
                    title="Source coverage hard veto",
                    detail=f"{s.label} source coverage {coverage:.1f}%.",
                    metadata={"coverage": coverage},
                )
            )
        else:
            findings.append(
                RiskFinding(
                    rule_id="RISK-05",
                    status="PASS",
                    title="Source coverage acceptable",
                    detail=f"{s.label} source coverage {coverage:.1f}%.",
                    metadata={"coverage": coverage},
                )
            )

    for h in holdings:
        lname = h.name.lower()
        if h.vehicle_type in FORBIDDEN_VEHICLES or any(x in lname for x in FORBIDDEN_NAME_HINTS):
            vetoes.append(
                Veto(
                    code="FORBIDDEN_PRODUCT",
                    rule_id="RISK-06",
                    message=f"{h.name} is not permitted in a household simulation.",
                )
            )
            findings.append(
                RiskFinding(
                    rule_id="RISK-06",
                    status="VETO",
                    title="Forbidden product",
                    detail=f"{h.name} cannot be allocated.",
                )
            )
    for s in scenarios:
        for w in s.weights:
            for vehicle in w.example_vehicles:
                if any(x in vehicle.lower() for x in FORBIDDEN_NAME_HINTS):
                    vetoes.append(
                        Veto(code="FORBIDDEN_PRODUCT", rule_id="RISK-06", message=f"{vehicle} is forbidden.")
                    )

    grow = next((s for s in scenarios if s.name == "grow"), None)
    if grow and (ips.capacity_for_loss == "low" or ips.equity_ceiling_pct < 35):
        if grow.equity_pct > ips.equity_ceiling_pct + 0.05:
            vetoes.append(
                Veto(
                    code="GROW_ELIGIBILITY",
                    rule_id="RISK-07",
                    message="Grow equity exceeds ceiling given low capacity or short horizon.",
                )
            )
            findings.append(
                RiskFinding(
                    rule_id="RISK-07",
                    status="VETO",
                    title="Grow not eligible at this equity weight",
                    detail=f"Grow equity {grow.equity_pct}% vs ceiling {ips.equity_ceiling_pct}%.",
                )
            )
        else:
            findings.append(
                RiskFinding(
                    rule_id="RISK-07",
                    status="PASS_WITH_CONDITIONS",
                    title="Grow is capped",
                    detail="Grow remains available as a more aggressive simulation, not as a better plan.",
                )
            )

    if profile.tax_regime == "new":
        findings.append(
            RiskFinding(
                rule_id="RISK-08",
                status="PASS",
                title="New-regime tax discipline",
                detail="No 80C fill-order is applied. Products are not added solely to save tax.",
            )
        )

    if "preserve_epf" in ips.constraints:
        findings.append(
            RiskFinding(
                rule_id="RISK-09",
                status="PASS",
                title="EPF preservation",
                detail="EPF is treated as locked and is not reallocated.",
            )
        )
    if "preserve_ppf" in ips.constraints:
        findings.append(
            RiskFinding(
                rule_id="RISK-09",
                status="PASS",
                title="PPF preservation",
                detail="PPF is treated as locked and is not reallocated.",
            )
        )

    findings.append(
        RiskFinding(
            rule_id="RISK-10",
            status="PASS",
            title="Unregistered land excluded",
            detail="Unregistered land is never automatically allocated.",
        )
    )

    hard = [v for v in vetoes if v.hard]
    if hard:
        status = "VETO"
    elif any(f.status == "INSUFFICIENT_DATA" for f in findings):
        status = "INSUFFICIENT_DATA"
    elif any(f.status == "PASS_WITH_CONDITIONS" for f in findings):
        status = "PASS_WITH_CONDITIONS"
    else:
        status = "PASS"
    return PolicyResult(findings=findings, vetoes=vetoes, status=status, scenarios=scenarios)


def _constraint_violations(ips: IPS, scenarios: list[PlanScenario], holdings: list[Holding]) -> list[str]:
    msgs: list[str] = []
    if "no_international" in ips.constraints or not ips.international_opt_in:
        for s in scenarios:
            if s.international_pct > 0.05:
                msgs.append(f"{s.label} includes international assets against a household prohibition.")
    if "no_crypto" in ips.constraints or not ips.vda_opt_in:
        for s in scenarios:
            if s.alternatives_pct > 0.05:
                msgs.append(f"{s.label} includes alternatives/VDA against policy.")
    if "no_direct_stocks" in ips.constraints or not ips.direct_equity_opt_in:
        for h in holdings:
            if h.vehicle_type == "direct_equity":
                # Research is allowed; default simulation must not depend on it.
                pass
        for s in scenarios:
            for w in s.weights:
                if any("direct stock" in v.lower() or "single-stock" in v.lower() for v in w.example_vehicles):
                    msgs.append(f"{s.label} lists direct stocks while they are disabled.")
    return msgs


def llm_cannot_override() -> dict[str, Any]:
    return {
        "policy_owner": "python",
        "llm_may_override_veto": False,
        "rules_version": RULES_VERSION,
    }
