from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.facts import ApiMeta, SourceRecord, SourcedValue
from app.models.profile import Holding, HouseholdProfile, IPS

ScenarioName = Literal["protect", "balance", "grow"]
RiskStatus = Literal["PASS", "PASS_WITH_CONDITIONS", "VETO", "INSUFFICIENT_DATA"]
JobStatus = Literal["queued", "running", "complete", "warning", "failed"]
AgentName = Literal[
    "profile_analyst",
    "holdings_analyst",
    "regulatory_research",
    "macro_research",
    "universe_research",
    "construction",
    "risk_officer",
    "plan_critic",
]


class SleeveWeight(BaseModel):
    sleeve: str
    weight_pct: float
    inr_amount: float = 0
    role: str = ""
    example_vehicles: list[str] = Field(default_factory=list)


class Candidate(BaseModel):
    name: str
    category: str
    vehicle_type: str
    role_in_portfolio: str
    risks: list[str] = Field(default_factory=list)
    liquidity: str = ""
    tax_notes: str = ""
    source_ids: list[str] = Field(default_factory=list)
    as_of: str = ""
    verification: str = "unverified"
    mock: bool = False


class Veto(BaseModel):
    code: str
    rule_id: str
    message: str
    hard: bool = True


class RiskFinding(BaseModel):
    rule_id: str
    status: RiskStatus
    title: str
    detail: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class MonthlyAction(BaseModel):
    title: str
    detail: str
    amount_inr: float | None = None
    kind: Literal["reserve", "contribute", "review", "avoid", "compare", "other"] = "other"


class StressResult(BaseModel):
    name: str
    hypothetical: bool = True
    description: str
    impact_summary: str
    metrics: dict[str, float] = Field(default_factory=dict)


class PlanScenario(BaseModel):
    name: ScenarioName
    label: str
    equity_pct: float
    fixed_income_pct: float
    cash_pct: float
    gold_pct: float
    alternatives_pct: float
    international_pct: float = 0
    weights: list[SleeveWeight] = Field(default_factory=list)
    estimated_volatility_class: Literal["low", "moderate", "higher"]
    liquidity: Literal["high", "moderate", "lower"]
    goal_fit: str
    rationale: str
    argument_for: str = ""
    argument_against: str = ""
    assumptions: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    what_would_change_conclusion: str = ""
    risk_flags: list[str] = Field(default_factory=list)
    source_coverage_pct: float = 100
    monthly_contribution_inr: float = 0
    do_not_do: list[str] = Field(default_factory=list)


class AgentEvent(BaseModel):
    agent: AgentName
    status: JobStatus
    message: str
    at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class FinalPlan(BaseModel):
    plan_id: str
    version: int = 1
    generated_at: datetime
    generated_at_ist: str
    snapshot_id: str
    rules_version: str
    model_name: str = "deterministic-mock"
    prompt_version: str = ""
    household: HouseholdProfile
    ips: IPS
    holdings: list[Holding]
    scenarios: list[PlanScenario]
    selected: ScenarioName | None = None
    risk_findings: list[RiskFinding] = Field(default_factory=list)
    vetoes: list[Veto] = Field(default_factory=list)
    risk_status: RiskStatus = "PASS"
    sources: list[SourceRecord] = Field(default_factory=list)
    actions: list[MonthlyAction] = Field(default_factory=list)
    stress: list[StressResult] = Field(default_factory=list)
    tax_notes: list[str] = Field(default_factory=list)
    protection_notes: list[str] = Field(default_factory=list)
    home_loan_analysis: dict[str, Any] | None = None
    emergency_reserve: dict[str, Any] = Field(default_factory=dict)
    current_allocation: dict[str, float] = Field(default_factory=dict)
    data_quality_warnings: list[str] = Field(default_factory=list)
    degraded: bool = False
    data_mode: str = "mock"
    critic: dict[str, Any] = Field(default_factory=dict)
    events: list[AgentEvent] = Field(default_factory=list)
    meta: ApiMeta = Field(default_factory=ApiMeta)
    no_valid_plan: bool = False


class PlanStatusPayload(BaseModel):
    plan_id: str
    status: JobStatus
    progress_pct: int = 0
    agents: list[AgentEvent] = Field(default_factory=list)
    message: str = ""
    meta: ApiMeta = Field(default_factory=ApiMeta)


class RegulatorySnapshot(BaseModel):
    snapshot_id: str
    generated_at: datetime
    assessment_year: SourcedValue
    tax_regimes: dict[str, Any]
    section_80c: SourcedValue
    section_80ccd_1b: SourcedValue
    section_80ccd_2: SourcedValue
    vda_tax: SourcedValue
    lrs: SourcedValue
    nps: dict[str, Any]
    market_data_restrictions: dict[str, Any]
    sources: list[SourceRecord] = Field(default_factory=list)
    degraded: bool = False
    data_mode: str = "mock"
    conflicts: list[str] = Field(default_factory=list)


class MarketSnapshot(BaseModel):
    snapshot_id: str
    generated_at: datetime
    macro_state: Literal["supportive", "neutral", "stress", "unclear"] = "neutral"
    notes: list[str] = Field(default_factory=list)
    observations: dict[str, SourcedValue] = Field(default_factory=dict)
    sources: list[SourceRecord] = Field(default_factory=list)
    degraded: bool = False
    data_mode: str = "mock"
    stale: bool = False
