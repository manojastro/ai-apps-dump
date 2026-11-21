from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TypedDict
from uuid import uuid4

from app.agents.critic import critique
from app.config import get_settings
from app.constants import DISCLAIMER, IST, PARSER_VERSION, PROMPT_VERSION, RULES_VERSION
from app.data.fixtures import mock_candidates, mock_market_snapshot
from app.engine.actions import five_actions, protection_notes
from app.engine.allocations import construct_scenarios, reconstruct_tighter
from app.engine.holdings import current_allocation
from app.engine.ips import build_ips
from app.engine.loans import home_loan_of, prepay_vs_invest
from app.engine.mathutil import monthly_surplus
from app.engine.stress import run_stress
from app.engine.tax import tax_considerations
from app.llm import LLMClient
from app.logging import get_logger
from app.models.facts import ApiMeta
from app.models.plan import AgentEvent, FinalPlan
from app.models.profile import Holding, HouseholdProfile
from app.policy.rules import evaluate_policy
from app.regulatory.regulatory_snapshot import build_mock_snapshot

log = get_logger(component="agents")


class PlanState(TypedDict, total=False):
    ips: dict
    holdings: list
    regulatory_snapshot: dict | None
    market_snapshot: dict | None
    candidates: list
    scenarios: list
    risk_findings: list
    vetoes: list
    final_plan: dict | None
    sources: list
    errors: list
    events: list
    profile: dict
    risk_status: str
    rebuilt: bool


def _event(agent: str, status: str, message: str, **meta: Any) -> AgentEvent:
    return AgentEvent(
        agent=agent,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        message=message,
        at=datetime.now(timezone.utc),
        metadata=meta,
    )


def run_pipeline(profile: HouseholdProfile, holdings: list[Holding], *, conflict: bool = False) -> FinalPlan:
    settings = get_settings()
    events: list[AgentEvent] = []
    errors: list[str] = []
    llm = LLMClient()
    now = datetime.now(timezone.utc)

    events.append(_event("profile_analyst", "running", "Building IPS from household inputs"))
    ips = build_ips(profile)
    events.append(
        _event(
            "profile_analyst",
            "complete",
            f"IPS validated. Risk band {ips.risk_band}, equity ceiling {ips.equity_ceiling_pct}%.",
        )
    )

    events.append(_event("holdings_analyst", "running", "Normalising holdings after PII redaction"))
    classified = holdings
    locked = [h for h in classified if h.locked]
    events.append(
        _event(
            "holdings_analyst",
            "complete",
            f"{len(classified)} holdings, {len(locked)} locked. PII redaction is deterministic Python.",
        )
    )

    events.append(_event("regulatory_research", "running", "Building regulatory snapshot"))
    snapshot = build_mock_snapshot(conflict=conflict)
    if settings.data_mode == "live":
        events.append(
            _event(
                "regulatory_research",
                "warning",
                "Live retrieval requested. Thresholds still require official pages; mock snapshot used if scrape fails.",
            )
        )
    events.append(
        _event(
            "regulatory_research",
            "complete",
            f"Tax snapshot updated. Assessment year {snapshot.assessment_year.value}. Degraded={snapshot.degraded}.",
        )
    )

    events.append(_event("macro_research", "running", "Researching only simulation-relevant macro context"))
    market = mock_market_snapshot()
    events.append(
        _event(
            "macro_research",
            "complete",
            f"Macro state {market.macro_state}. Not market timing.",
        )
    )

    events.append(_event("universe_research", "running", "Producing class-level candidates per sleeve"))
    candidates = mock_candidates()
    if not profile.international_opt_in:
        candidates = [c for c in candidates if c.category != "international"]
    events.append(
        _event(
            "universe_research",
            "complete",
            f"{len(candidates)} class-level candidates. Max five per sleeve.",
        )
    )

    portfolio_value = sum(h.current_value_inr for h in classified) or (
        profile.monthly_take_home_inr * 12
    )
    surplus = monthly_surplus(
        profile.monthly_take_home_inr,
        profile.essential_expenses_monthly_inr,
        profile.discretionary_expenses_monthly_inr,
        profile.insurance_premiums_monthly_inr,
        profile.rent_monthly_inr,
        sum(x.emi for x in profile.liabilities),
    )
    events.append(_event("construction", "running", "Constructing Protect / Balance / Grow"))
    scenarios = construct_scenarios(ips, portfolio_value, surplus, candidates)
    events.append(_event("construction", "complete", "Scenario recalculated. Weights owned by Python."))

    events.append(_event("risk_officer", "running", "Independent deterministic checks"))
    policy = evaluate_policy(profile, ips, classified, scenarios, candidates)
    rebuilt = False
    if policy.status == "VETO":
        events.append(
            _event(
                "risk_officer",
                "warning",
                "Risk rule veto. Returning findings to construction for one tighter retry.",
                vetoes=[v.model_dump() for v in policy.vetoes],
            )
        )
        scenarios = reconstruct_tighter(scenarios, ips)
        rebuilt = True
        policy = evaluate_policy(profile, ips, classified, scenarios, candidates)
        if policy.status == "VETO":
            events.append(
                _event(
                    "risk_officer",
                    "failed",
                    "Second Risk Officer pass still vetoed. NO_VALID_PLAN rather than bypass.",
                )
            )
        else:
            events.append(_event("risk_officer", "complete", "Retry passed under tighter constraints."))
    else:
        events.append(
            _event(
                "risk_officer",
                "complete",
                f"Risk Officer {policy.status}. Source coverage evaluated.",
            )
        )

    no_valid = policy.status == "VETO"
    if no_valid:
        # Safest educational fallback: keep Protect only, still labelled.
        scenarios = [s for s in scenarios if s.name == "protect"] or scenarios[:1]
        errors.append("NO_VALID_PLAN after retry. Showing safest educational scenario only.")

    events.append(_event("plan_critic", "running", "Evaluating surviving scenarios without endorsement"))
    critic = critique(profile, ips, scenarios, policy.findings)
    if llm.enabled:
        extra = llm.complete_json(
            "Summarise trade-offs without inventing numbers. " + json_safe(scenarios),
            "keys: summary",
        )
        if extra:
            critic["llm_summary"] = extra
    events.append(_event("plan_critic", "complete", "Critic recorded arguments for and against each scenario."))

    essential = profile.essential_expenses_monthly_inr + profile.rent_monthly_inr
    liquid = sum(h.current_value_inr for h in classified if h.category == "cash_safety" and not h.locked)
    target = ips.minimum_liquid_reserve_months * essential
    reserve_gap = max(0.0, target - liquid)
    selected_preview = scenarios[1] if len(scenarios) > 1 else scenarios[0]
    loan = home_loan_of(profile)
    home = None
    if loan:
        home = prepay_vs_invest(loan, min(surplus * 6, loan.outstanding_balance * 0.1 or 50_000))
    stress = run_stress(profile, ips, selected_preview, portfolio_value, liquid)
    actions = five_actions(
        profile,
        ips,
        selected_preview,
        reserve_gap,
        None,
        loan is not None,
    )
    tax_notes = tax_considerations(profile, ips, snapshot)
    warnings = ["MOCK_DATA / DEGRADED_DATA: fixture snapshot, not live retrieval."]
    if snapshot.conflicts:
        warnings.extend(snapshot.conflicts)
    if market.degraded:
        warnings.append("Market snapshot is degraded. No fabricated index level.")

    ist = now.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S IST")

    plan = FinalPlan(
        plan_id=f"plan-{uuid4().hex[:12]}",
        version=1,
        generated_at=now,
        generated_at_ist=ist,
        snapshot_id=snapshot.snapshot_id,
        rules_version=RULES_VERSION,
        model_name=settings.llm_model if llm.enabled else "deterministic-mock",
        prompt_version=PROMPT_VERSION,
        household=profile,
        ips=ips,
        holdings=classified,
        scenarios=scenarios,
        selected=None,
        risk_findings=policy.findings,
        vetoes=policy.vetoes,
        risk_status=policy.status,  # type: ignore[arg-type]
        sources=snapshot.sources + market.sources,
        actions=actions,
        stress=stress,
        tax_notes=tax_notes,
        protection_notes=protection_notes(profile),
        home_loan_analysis=home,
        emergency_reserve={
            "liquid_inr": liquid,
            "target_inr": target,
            "gap_inr": reserve_gap,
            "months_target": ips.minimum_liquid_reserve_months,
        },
        current_allocation=current_allocation(classified),
        data_quality_warnings=warnings,
        degraded=True,
        data_mode=settings.data_mode,
        critic=critic,
        events=events,
        meta=ApiMeta(
            disclaimer=DISCLAIMER,
            data_mode=settings.data_mode,
            degraded=True,
            rules_version=RULES_VERSION,
            snapshot_id=snapshot.snapshot_id,
        ),
        no_valid_plan=no_valid,
    )
    plan.critic["parser_version"] = PARSER_VERSION
    plan.critic["rebuilt"] = rebuilt
    log.info(
        "pipeline_complete",
        plan_id=plan.plan_id,
        risk_status=plan.risk_status,
        firecrawl_calls=0,
        llm_calls=llm.calls,
        rebuilt=rebuilt,
    )
    return plan


def json_safe(scenarios) -> str:
    return str([{"name": s.name, "equity": s.equity_pct} for s in scenarios])


def compile_graph():
    """LangGraph wrapper. Nodes call the same deterministic functions."""
    try:
        from langgraph.graph import END, START, StateGraph
    except Exception:  # noqa: BLE001
        return None

    def profile_node(state: PlanState) -> PlanState:
        return state

    graph = StateGraph(PlanState)
    graph.add_node("profile_analyst", profile_node)
    graph.add_node("holdings_analyst", profile_node)
    graph.add_node("regulatory_research", profile_node)
    graph.add_node("macro_research", profile_node)
    graph.add_node("universe_research", profile_node)
    graph.add_node("construction", profile_node)
    graph.add_node("risk_officer", profile_node)
    graph.add_node("plan_critic", profile_node)
    graph.add_edge(START, "profile_analyst")
    graph.add_edge("profile_analyst", "holdings_analyst")
    graph.add_edge("holdings_analyst", "regulatory_research")
    graph.add_edge("regulatory_research", "macro_research")
    graph.add_edge("macro_research", "universe_research")
    graph.add_edge("universe_research", "construction")
    graph.add_edge("construction", "risk_officer")
    graph.add_edge("risk_officer", "plan_critic")
    graph.add_edge("plan_critic", END)
    return graph.compile()


GRAPH = None


def get_graph():
    global GRAPH
    if GRAPH is None:
        GRAPH = compile_graph()
    return GRAPH
