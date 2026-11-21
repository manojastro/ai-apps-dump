"""Typed API responses."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class Health(BaseModel):
    status: str
    database: str
    version: str


class LoginRequest(BaseModel):
    email: str = Field(max_length=200)
    password: str = Field(max_length=200)


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    team_id: int | None
    team_name: str | None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class AccountRow(BaseModel):
    id: int
    name: str
    domain: str | None
    industry: str | None
    region: str
    segment: str
    arr: float
    status: str
    churned_at: date | None
    health_score: int | None
    health_status: str | None
    owner_name: str | None
    p_churn: float | None
    churn_band: str | None
    cite: str


class Reason(BaseModel):
    feature: str
    value: float
    impact: float
    direction: str
    text: str


class AccountDeal(BaseModel):
    id: int
    name: str
    amount: float
    stage: str
    type: str
    created_at: date
    close_date: date | None
    closed_at: date | None
    outcome: str | None
    discount_pct: float | None
    p_win: float | None
    risk_band: str | None
    cite: str


class ContactRow(BaseModel):
    id: int
    full_name: str
    title: str | None
    is_executive: bool
    is_champion: bool
    last_seen: date | None
    cite: str


class SubscriptionRow(BaseModel):
    id: int
    start: date
    end: date | None
    mrr: float
    seats: int
    status: str
    renewal_date: date | None
    cite: str


class InvoiceRow(BaseModel):
    id: int
    amount: float
    issued_date: date
    due_date: date
    paid_date: date | None
    status: str
    cite: str


class TicketRow(BaseModel):
    id: int
    opened_at: date
    resolved_at: date | None
    severity: int
    subject: str
    body_text: str | None
    cite: str


class UsagePoint(BaseModel):
    week: date
    active_users: float
    key_feature_events: int
    seats: int


class Risk(BaseModel):
    type: str
    text: str
    cite: str


class TimelineEvent(BaseModel):
    date: date
    kind: str
    text: str
    cite: str


class Account360(BaseModel):
    account: AccountRow
    deals: list[AccountDeal]
    contacts: list[ContactRow]
    subscriptions: list[SubscriptionRow]
    invoices: list[InvoiceRow]
    tickets: list[TicketRow]
    usage_trend: list[UsagePoint]
    open_risks: list[Risk]
    churn_reasons: list[Reason]
    timeline: list[TimelineEvent]


class DealRow(BaseModel):
    id: int
    name: str
    account_id: int
    account_name: str
    owner_name: str | None
    team_id: int | None
    amount: float
    stage: str
    type: str
    created_at: date
    close_date: date | None
    closed_at: date | None
    outcome: str | None
    discount_pct: float | None
    p_win: float | None
    risk_band: str | None
    value_at_risk: float | None
    reasons: list[Reason]
    cite: str


class DealExplain(DealRow):
    model_version: str | None
    model_algorithm: str | None
    prediction_cite: str | None


class ForecastFigures(BaseModel):
    low: float
    expected: float
    high: float
    closed_won_to_date: float
    rep_commit: float
    stage_weighted: float
    open_deals: int
    open_pipeline: float


class TeamForecast(ForecastFigures):
    team: str


class RegionForecast(ForecastFigures):
    region: str


class ForecastDeal(BaseModel):
    id: int
    name: str
    amount: float
    stage: str
    p_win: float
    expected_value: float
    cite: str


class Forecast(ForecastFigures):
    quarter: str
    as_of: date
    simulations: int
    by_team: list[TeamForecast]
    by_region: list[RegionForecast]
    top_deals: list[ForecastDeal]
    cite: str


class ChangeItem(BaseModel):
    deal_id: int
    name: str
    category: str
    delta_expected: float
    detail: str
    cite: str


class ForecastChanges(BaseModel):
    available: bool
    quarter: str | None = None
    previous_date: date | None = None
    current_date: date | None = None
    expected_previous: float | None = None
    expected_current: float | None = None
    total_change: float | None = None
    categories: dict[str, dict[str, float]] = {}
    items: list[ChangeItem] = []
    cite: str | None = None


class RetentionRow(BaseModel):
    account_id: int
    name: str
    segment: str
    region: str
    owner_name: str | None
    arr: float
    p_churn: float
    band: str | None
    expected_arr_loss: float
    renewal_date: date | None
    reasons: list[Reason]
    cite: str
    prediction_cite: str


class RetentionSummary(BaseModel):
    as_of: date
    scored_accounts: int
    total_arr: float
    at_risk_arr: float
    at_risk_accounts: int
    watch_arr: float
    watch_accounts: int
    expected_arr_loss: float
    at_risk_account_ids: list[int]


class ChurnExplain(BaseModel):
    account_id: int
    name: str
    arr: float
    status: str
    p_churn: float | None
    band: str | None
    reasons: list[Reason]
    cite: str


class ExpansionRow(BaseModel):
    account_id: int
    name: str
    arr: float
    seat_utilization: float
    user_growth: float
    seats: int
    triggers: list[str]
    cite: str


class ChatTurn(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(max_length=8000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(default=[], max_length=12)


class ChatResponse(BaseModel):
    answer: str
    tools_called: list[dict[str, Any]]
    citations: list[str]
    invalid_citations: list[str]
    ungrounded_numbers: list[str]
    audit_id: int | None
    latency_ms: int


class SourceRecord(BaseModel):
    table: str
    id: int
    record: dict[str, Any]


class BriefOut(BaseModel):
    brief_date: date
    content: dict[str, Any]


class AuditRow(BaseModel):
    id: int
    user_id: int
    user_email: str
    question: str
    tools_called: Any
    answer: str
    cited_sources: Any
    created_at: datetime


class ModelRow(BaseModel):
    model_name: str
    version: str
    algorithm: str
    trained_at: datetime
    is_active: bool
    metrics: dict[str, Any]


class DataHealth(BaseModel):
    run_at: datetime | None
    summary: dict[str, Any]
    load_rejects: int
    row_counts: dict[str, int]
