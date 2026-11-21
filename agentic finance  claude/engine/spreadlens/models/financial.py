"""Taxonomy, mapping proposals, normalized observations, spreads (statement sets) and calculations."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from spreadlens.models.base import MONEY, RATIO, Base, created_col, id_col


class CanonicalLineItem(Base):
    __tablename__ = "canonical_line_items"
    __table_args__ = (UniqueConstraint("taxonomy_version", "code"),)
    id: Mapped[str] = id_col()
    taxonomy_version: Mapped[str] = mapped_column(String(40))
    code: Mapped[str] = mapped_column(String(80))
    label: Mapped[str] = mapped_column(String(200))
    statement_type: Mapped[str] = mapped_column(String(20))
    unit_type: Mapped[str] = mapped_column(String(20))
    period_type: Mapped[str] = mapped_column(String(20))  # instant | duration
    sign: Mapped[str] = mapped_column(String(20))  # positive | signed
    is_total: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    definition: Mapped[str] = mapped_column(Text, default="")


class Spread(Base):
    """The review unit: one reporting entity + consolidation scope + currency for a company.

    Standalone and consolidated data, and different currencies, never share a spread.
    """

    __tablename__ = "spreads"
    __table_args__ = (UniqueConstraint("entity_id", "currency"),)
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    entity_id: Mapped[str] = mapped_column(ForeignKey("reporting_entities.id", ondelete="CASCADE"), index=True)
    scope: Mapped[str] = mapped_column(String(20))
    currency: Mapped[str] = mapped_column(String(3))
    display_scale: Mapped[str] = mapped_column(String(20), default="crores")
    current_version_no: Mapped[int] = mapped_column(Integer, default=0)
    review_status: Mapped[str] = mapped_column(String(30), default="in_preparation")
    # in_preparation | submitted_for_review | approved | reopened
    created_at: Mapped[datetime] = created_col()


class SpreadVersion(Base):
    """Immutable statement-set version. Bumped whenever an input or decision changes figures."""

    __tablename__ = "spread_versions"
    __table_args__ = (UniqueConstraint("spread_id", "version_no"),)
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    spread_id: Mapped[str] = mapped_column(ForeignKey("spreads.id", ondelete="CASCADE"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(String(200))
    statement_hashes: Mapped[dict] = mapped_column(JSON, default=dict)  # statement_type -> hash (statement versions)
    created_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = created_col()


class MappingProposal(Base):
    __tablename__ = "mapping_proposals"
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    row_id: Mapped[str] = mapped_column(ForeignKey("extracted_rows.id", ondelete="CASCADE"), index=True)
    taxonomy_version: Mapped[str] = mapped_column(String(40))
    proposed_code: Mapped[str | None] = mapped_column(String(80), nullable=True)  # None = unmapped
    original_label: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text)
    confidence: Mapped[str] = mapped_column(String(10))  # high | medium | low | none
    score: Mapped[Decimal | None] = mapped_column(RATIO, nullable=True)
    alternatives: Mapped[list] = mapped_column(JSON, default=list)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="proposed")  # proposed | accepted | changed | rejected | unresolved
    decided_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    agent_execution_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = created_col()


class Observation(Base):
    """A normalized financial observation. Original fields are immutable; corrections live in
    `current_value` + `analyst_adjustments` with full before/after history."""

    __tablename__ = "observations"
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    spread_id: Mapped[str] = mapped_column(ForeignKey("spreads.id", ondelete="CASCADE"), index=True)
    document_version_id: Mapped[str] = mapped_column(ForeignKey("document_versions.id", ondelete="CASCADE"), index=True)
    source_sha256: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[str] = mapped_column(String(32), index=True)
    statement_id: Mapped[str] = mapped_column(String(32), index=True)
    row_id: Mapped[str] = mapped_column(String(32), index=True)
    cell_id: Mapped[str] = mapped_column(String(32), index=True)
    statement_type: Mapped[str] = mapped_column(String(20))
    scope: Mapped[str] = mapped_column(String(20))
    framework: Mapped[str] = mapped_column(String(40), default="unknown")
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date] = mapped_column(Date)
    duration: Mapped[str] = mapped_column(String(20))
    original_label: Mapped[str] = mapped_column(Text)
    canonical_code: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    mapping_proposal_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    unit_type: Mapped[str] = mapped_column(String(20), default="monetary")
    raw_text: Mapped[str] = mapped_column(Text)
    value_state: Mapped[str] = mapped_column(String(20))
    parsed_value: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)
    source_decimals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    original_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    original_scale: Mapped[str | None] = mapped_column(String(20), nullable=True)
    normalized_value: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)  # base units, canonical sign
    normalized_scale: Mapped[str] = mapped_column(String(20), default="units")
    current_value: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)  # after analyst adjustments
    current_state: Mapped[str] = mapped_column(String(20))
    origin: Mapped[str] = mapped_column(String(20), default="reported")  # reported | derived | adjusted
    version_kind: Mapped[str] = mapped_column(String(20), default="original")  # original | restated | comparative
    is_preferred: Mapped[bool] = mapped_column(Boolean, default=True)  # chosen value when several documents report the same item
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox: Mapped[list | None] = mapped_column(JSON, nullable=True)
    sheet: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cell_ref: Mapped[str | None] = mapped_column(String(20), nullable=True)
    extraction_method: Mapped[str] = mapped_column(String(30))
    confidence: Mapped[dict] = mapped_column(JSON, default=dict)
    review_status: Mapped[str] = mapped_column(String(20), default="unreviewed")  # unreviewed | accepted | corrected | rejected | unresolved
    transformations: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = created_col()


class CalculationResult(Base):
    """Validation rule outcome or metric. Always tied to a spread version (immutable)."""

    __tablename__ = "calculation_results"
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    spread_id: Mapped[str] = mapped_column(ForeignKey("spreads.id", ondelete="CASCADE"), index=True)
    spread_version_no: Mapped[int] = mapped_column(Integer, index=True)
    kind: Mapped[str] = mapped_column(String(20))  # validation | metric
    rule_id: Mapped[str] = mapped_column(String(80))
    rule_version: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    statement_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    input_observation_ids: Mapped[list] = mapped_column(JSON, default=list)
    expression: Mapped[str] = mapped_column(Text)
    expected: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)
    observed: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)
    difference: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)
    value: Mapped[Decimal | None] = mapped_column(RATIO, nullable=True)  # metric value
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    tolerance: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)
    tolerance_basis: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="info")  # critical | warning | info
    status: Mapped[str] = mapped_column(String(40))  # pass | fail | not_applicable | insufficient_data | requires_review | computed | special_interpretation
    explanation: Mapped[str] = mapped_column(Text, default="")
    limitations: Mapped[list] = mapped_column(JSON, default=list)
    source_refs: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = created_col()


class ValidationException(Base):
    """An item in the analyst review queue."""

    __tablename__ = "validation_exceptions"
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    company_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    spread_id: Mapped[str | None] = mapped_column(ForeignKey("spreads.id", ondelete="CASCADE"), index=True, nullable=True)
    document_version_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    fingerprint: Mapped[str] = mapped_column(String(64), index=True)  # stable identity across versions
    category: Mapped[str] = mapped_column(String(40))
    # validation | unreadable_cell | unmapped_row | ambiguous_mapping | metadata | duplicate | unit_conflict
    # | missing_statement | restatement | prompt_injection | unsupported_entity | extraction_failure
    severity: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(300))
    detail: Mapped[str] = mapped_column(Text)
    calculation_result_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    observation_ids: Mapped[list] = mapped_column(JSON, default=list)
    row_ids: Mapped[list] = mapped_column(JSON, default=list)
    suggested_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open | explained | resolved | superseded
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_seen_version: Mapped[int] = mapped_column(Integer, default=0)
    last_seen_version: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = created_col()


class AnalystAdjustment(Base):
    __tablename__ = "analyst_adjustments"
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    spread_id: Mapped[str] = mapped_column(ForeignKey("spreads.id", ondelete="CASCADE"), index=True)
    observation_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    row_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    action: Mapped[str] = mapped_column(String(40))
    # correct_value | change_mapping | accept_mapping | reject_mapping | confirm_unit | confirm_period
    # | mark_unresolved | add_adjustment | accept_exception | request_reextraction
    field: Mapped[str | None] = mapped_column(String(60), nullable=True)
    before: Mapped[dict] = mapped_column(JSON, default=dict)
    after: Mapped[dict] = mapped_column(JSON, default=dict)
    reason: Mapped[str] = mapped_column(Text)
    user_id: Mapped[str] = mapped_column(String(32))
    spread_version_before: Mapped[int] = mapped_column(Integer)
    spread_version_after: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = created_col()


class ReviewDecision(Base):
    __tablename__ = "review_decisions"
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    spread_id: Mapped[str] = mapped_column(ForeignKey("spreads.id", ondelete="CASCADE"), index=True)
    spread_version_no: Mapped[int] = mapped_column(Integer)
    decision: Mapped[str] = mapped_column(String(30))  # submit_for_review | approve | reopen
    user_id: Mapped[str] = mapped_column(String(32))
    role: Mapped[str] = mapped_column(String(20))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_stale: Mapped[bool] = mapped_column(Boolean, default=False)
    stale_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    snapshot_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = created_col()


class ExportSnapshot(Base):
    __tablename__ = "export_snapshots"
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    spread_id: Mapped[str] = mapped_column(ForeignKey("spreads.id", ondelete="CASCADE"), index=True)
    spread_version_no: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20))  # draft | approved
    content_hash: Mapped[str] = mapped_column(String(64))
    snapshot: Mapped[dict] = mapped_column(JSON)
    xlsx_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pdf_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    render_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | ok | failed
    render_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = created_col()
