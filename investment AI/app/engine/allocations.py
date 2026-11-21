from __future__ import annotations

from app.engine.mathutil import clamp, normalize_weights
from app.models.plan import Candidate, PlanScenario, SleeveWeight
from app.models.profile import IPS

FORBIDDEN = {"chit_fund", "unlisted", "speculative_ncd", "telegram_tip"}


def _vehicles(candidates: list[Candidate], category: str, limit: int = 5) -> list[str]:
    names = [c.name for c in candidates if c.category == category][:limit]
    return names


def construct_scenarios(
    ips: IPS,
    portfolio_value: float,
    monthly_surplus: float,
    candidates: list[Candidate],
) -> list[PlanScenario]:
    specs = [
        (
            "protect",
            "Protect",
            {
                "cash": 32.0,
                "fixed_income": 43.0,
                "equity": 18.0,
                "gold": 7.0,
                "international": 0.0,
                "alternatives": 0.0,
            },
            "low",
            "high",
            "Prioritises liquidity, capital stability and near-term goals.",
        ),
        (
            "balance",
            "Balance",
            {
                "cash": 14.0,
                "fixed_income": 33.0,
                "equity": 43.0,
                "gold": 8.0,
                "international": 2.0,
                "alternatives": 0.0,
            },
            "moderate",
            "moderate",
            "Diversified long-term growth with a bounded downside sleeve.",
        ),
        (
            "grow",
            "Grow",
            {
                "cash": 8.0,
                "fixed_income": 22.0,
                "equity": 60.0,
                "gold": 6.0,
                "international": 4.0,
                "alternatives": 0.0,
            },
            "higher",
            "lower",
            "More aggressive long-term growth potential — not 'better'.",
        ),
    ]
    scenarios: list[PlanScenario] = []
    for name, label, raw, vol, liq, rationale in specs:
        weights = dict(raw)
        if not ips.international_opt_in:
            weights["cash"] += weights["international"]
            weights["international"] = 0.0
        else:
            weights["international"] = min(weights["international"] + 4.0, 12.0 if name == "grow" else 8.0)
        if ips.vda_opt_in and name == "grow":
            weights["alternatives"] = min(3.0, weights.get("alternatives", 0) + 2.0)
            weights["equity"] = max(0.0, weights["equity"] - 2.0)
        else:
            weights["alternatives"] = 0.0
        weights["equity"] = min(weights["equity"], ips.equity_ceiling_pct)
        if name == "grow" and (ips.capacity_for_loss == "low" or ips.equity_ceiling_pct < 40):
            weights["equity"] = min(weights["equity"], ips.equity_ceiling_pct * 0.7)
        if name == "protect":
            weights["equity"] = min(weights["equity"], ips.equity_ceiling_pct * 0.55)
        if weights["fixed_income"] < ips.required_debt_floor_pct * 0.6:
            bump = ips.required_debt_floor_pct * 0.6 - weights["fixed_income"]
            weights["fixed_income"] += bump
            weights["equity"] = max(8.0, weights["equity"] - bump)
        if "only_regulated_mutual_funds" in ips.constraints:
            pass
        weights = normalize_weights(weights)
        sleeve_map = {
            "cash": ("cash_safety", "Liquidity and emergency reserve"),
            "fixed_income": ("fixed_income", "Stability and known cash-flows"),
            "equity": ("equity", "Long-term growth engine"),
            "gold": ("gold", "Diversifier; jewellery treated as consumption"),
            "international": ("international", "Optional diversifier; LRS/TCS from snapshot"),
            "alternatives": ("alternatives", "Capped; default zero unless opted in"),
        }
        sleeves: list[SleeveWeight] = []
        for key, pct in weights.items():
            cat, role = sleeve_map[key]
            sleeves.append(
                SleeveWeight(
                    sleeve=key,
                    weight_pct=pct,
                    inr_amount=round(portfolio_value * pct / 100.0, 2),
                    role=role,
                    example_vehicles=_vehicles(candidates, cat),
                )
            )
        contrib = max(0.0, monthly_surplus)
        if name == "protect":
            goal_fit = "Favours near-term must-have goals and reserve completion."
        elif name == "balance":
            goal_fit = "Splits surplus between reserve top-up and long-horizon goals."
        else:
            goal_fit = "Directs more surplus to long-horizon growth after reserve policy is met."
        scenarios.append(
            PlanScenario(
                name=name,  # type: ignore[arg-type]
                label=label,
                equity_pct=weights["equity"],
                fixed_income_pct=weights["fixed_income"],
                cash_pct=weights["cash"],
                gold_pct=weights["gold"],
                alternatives_pct=weights["alternatives"],
                international_pct=weights["international"],
                weights=sleeves,
                estimated_volatility_class=vol,  # type: ignore[arg-type]
                liquidity=liq,  # type: ignore[arg-type]
                goal_fit=goal_fit,
                rationale=rationale,
                monthly_contribution_inr=round(contrib, 2),
                do_not_do=[
                    "Do not treat this simulation as an instruction to buy or sell a security.",
                    "Do not allocate to chit funds or unlisted speculative products.",
                    "Do not increase equity while the emergency reserve is below policy.",
                    "Do not use social-media tips as a source.",
                ],
            )
        )
    return scenarios


def reconstruct_tighter(scenarios: list[PlanScenario], ips: IPS) -> list[PlanScenario]:
    """One retry path: cut alternatives and equity, raise cash/debt."""
    rebuilt: list[PlanScenario] = []
    for s in scenarios:
        mapping = {w.sleeve: w.weight_pct for w in s.weights}
        mapping["alternatives"] = 0.0
        mapping["equity"] = clamp(mapping.get("equity", 0) * 0.75, 8.0, ips.equity_ceiling_pct * 0.8)
        mapping["cash"] = mapping.get("cash", 0) + 8
        mapping["fixed_income"] = mapping.get("fixed_income", 0) + 6
        mapping["international"] = min(mapping.get("international", 0), 4 if ips.international_opt_in else 0)
        mapping = normalize_weights(mapping)
        total = sum(w.inr_amount for w in s.weights) or 0
        new_weights = []
        for w in s.weights:
            pct = mapping.get(w.sleeve, 0)
            new_weights.append(
                SleeveWeight(
                    sleeve=w.sleeve,
                    weight_pct=pct,
                    inr_amount=round(total * pct / 100.0, 2),
                    role=w.role,
                    example_vehicles=w.example_vehicles,
                )
            )
        rebuilt.append(
            s.model_copy(
                update={
                    "weights": new_weights,
                    "equity_pct": mapping.get("equity", 0),
                    "fixed_income_pct": mapping.get("fixed_income", 0),
                    "cash_pct": mapping.get("cash", 0),
                    "gold_pct": mapping.get("gold", 0),
                    "alternatives_pct": 0.0,
                    "international_pct": mapping.get("international", 0),
                    "rationale": s.rationale + " Recalculated once under tighter risk constraints.",
                    "risk_flags": list(set(s.risk_flags + ["tighter_constraints_retry"])),
                }
            )
        )
    return rebuilt
