from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

TaxRegime = Literal["new", "old", "unknown"]
GoalPriority = Literal["must_have", "important", "optional"]
MaritalStatus = Literal["single", "married", "widowed", "divorced", "other"]
Scale5 = Literal[1, 2, 3, 4, 5]
ConstraintFlag = Literal[
    "no_direct_stocks",
    "no_crypto",
    "no_international",
    "only_regulated_mutual_funds",
    "esg_preference",
    "shariah_aware",
    "preserve_epf",
    "preserve_ppf",
    "existing_home_loan",
    "avoid_illiquid",
    "no_chit_funds",
    "no_unlisted",
]


class Goal(BaseModel):
    name: str
    target_amount_inr: float = Field(ge=0)
    target_year: int = Field(ge=2024, le=2100)
    priority: GoalPriority = "important"


class Liability(BaseModel):
    type: Literal["home_loan", "vehicle_loan", "education_loan", "personal_loan", "credit_card", "other"]
    outstanding_balance: float = Field(ge=0)
    interest_rate: float = Field(ge=0, le=100)
    emi: float = Field(ge=0)
    remaining_tenure_months: int = Field(ge=0)


class Holding(BaseModel):
    name: str
    category: str
    vehicle_type: str = ""
    current_value_inr: float = Field(ge=0)
    locked: bool = False
    notes: str = ""
    source_ids: list[str] = Field(default_factory=list)


class RiskInputs(BaseModel):
    emotional_tolerance: Scale5
    financial_capacity: Scale5
    income_stability: Scale5
    investment_experience: Scale5
    liquidity_need: Scale5
    goal_horizon_years: int | None = None


class HouseholdProfile(BaseModel):
    first_name: str
    age: int = Field(ge=18, le=100)
    city: str = ""
    state: str = ""
    marital_status: MaritalStatus = "single"
    dependents: int = Field(ge=0, default=0)
    earners: int = Field(ge=1, default=1)
    monthly_take_home_inr: float = Field(ge=0)
    annual_gross_inr: float | None = Field(default=None, ge=0)
    variable_income_monthly_inr: float = Field(default=0, ge=0)
    employer_retirement_contribution_monthly_inr: float = Field(default=0, ge=0)
    essential_expenses_monthly_inr: float = Field(ge=0)
    discretionary_expenses_monthly_inr: float = Field(default=0, ge=0)
    insurance_premiums_monthly_inr: float = Field(default=0, ge=0)
    rent_monthly_inr: float = Field(default=0, ge=0)
    liabilities: list[Liability] = Field(default_factory=list)
    goals: list[Goal] = Field(default_factory=list)
    risk: RiskInputs
    constraints: list[ConstraintFlag] = Field(default_factory=list)
    tax_regime: TaxRegime = "unknown"
    international_opt_in: bool = False
    direct_equity_opt_in: bool = False
    vda_opt_in: bool = False
    existing_holdings: list[Holding] = Field(default_factory=list)
    fixture_id: str | None = None

    @field_validator("first_name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("first name is required")
        return cleaned


class IPS(BaseModel):
    risk_score: float
    risk_band: Literal["conservative", "moderate", "growth"]
    capacity_for_loss: Literal["low", "moderate", "high"]
    equity_ceiling_pct: float
    minimum_liquid_reserve_months: float
    required_debt_floor_pct: float
    goals: list[Goal]
    constraints: list[ConstraintFlag]
    tax_regime: TaxRegime
    international_opt_in: bool = False
    direct_equity_opt_in: bool = False
    vda_opt_in: bool = False
    age: int
    first_name: str
    notes: list[str] = Field(default_factory=list)
    rules_version: str = ""
