"""Inputs and outputs of the deterministic rules engine (no database, no AI)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

PASS = "pass"
FAIL = "fail"
NOT_APPLICABLE = "not_applicable"
INSUFFICIENT = "insufficient_data"
REQUIRES_REVIEW = "requires_review"
STATUSES = (PASS, FAIL, NOT_APPLICABLE, INSUFFICIENT, REQUIRES_REVIEW)


@dataclass(frozen=True)
class Fact:
    id: str
    code: str | None
    period_end: date
    value: Decimal | None  # base units, canonical sign; None unless state is value/zero
    state: str
    decimals: int | None
    scale: str | None
    statement_type: str
    label: str
    document_version_id: str = ""
    version_kind: str = "original"
    restated_flag: bool = False
    source_ref: str = ""
    period_start: date | None = None

    @property
    def numeric(self) -> bool:
        return self.state in ("value", "zero") and self.value is not None


@dataclass(frozen=True)
class SubtotalGroup:
    """Rows printed under a subtotal in the source (one level; nested subtotals appear as one child)."""

    statement_type: str
    period_end: date
    total: Fact
    children: tuple[Fact, ...]
    sign_hint: str = "sum"  # "sum" or "net" (children carry their own signs)


@dataclass
class SpreadFacts:
    preferred: dict[tuple[str, date], Fact]
    all_facts: list[Fact]
    groups: list[SubtotalGroup] = field(default_factory=list)
    periods: list[date] = field(default_factory=list)  # ascending
    cash_reconciling_items: dict[date, list[tuple[str, Decimal]]] = field(default_factory=dict)
    present_codes: set[str] = field(default_factory=set)  # codes that appear in any statement (any state)

    def get(self, code: str, period: date) -> Fact | None:
        return self.preferred.get((code, period))


@dataclass
class RuleResult:
    rule_id: str
    rule_version: str
    title: str
    statement_type: str | None
    period_end: date | None
    input_ids: list[str]
    expression: str
    expected: Decimal | None
    observed: Decimal | None
    difference: Decimal | None
    tolerance: Decimal | None
    tolerance_basis: str | None
    severity: str
    status: str
    explanation: str
    source_refs: list[str] = field(default_factory=list)
    key: str = ""  # stable identity for exception fingerprinting


@dataclass
class MetricResult:
    metric_id: str
    version: str
    title: str
    period_end: date
    formula: str
    input_ids: list[str]
    value: Decimal | None
    unit: str  # ratio | percent | monetary
    status: str  # computed | insufficient_data | special_interpretation | not_applicable
    explanation: str
    limitations: list[str] = field(default_factory=list)
    prior_period_end: date | None = None
