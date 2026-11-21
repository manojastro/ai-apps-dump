"""Typed artifacts exchanged between agents. These — not chat transcripts — are the system of record.

Model (live) outputs are validated against these schemas, then against the source document
(evidence quotes must exist, candidate codes must be from the offered set, referenced IDs must exist).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

StatementType = Literal["balance_sheet", "income_statement", "cash_flow"]
Scope = Literal["standalone", "consolidated"]
Scale = Literal["units", "thousands", "lakhs", "millions", "crores", "billions"]


class Evidence(BaseModel):
    quote: str = Field(description="Exact text copied from the document")
    page: int | None = None
    sheet: str | None = None


class Question(BaseModel):
    field: Literal["entity_name", "currency", "scale", "period", "scope"]
    statement_key: str | None = None
    question: str
    options: list[str] = []
    evidence: list[Evidence] = []


class PeriodColumn(BaseModel):
    column_index: int
    header_raw: str
    period_end: str | None = Field(None, description="ISO date or null when the header does not establish it")
    duration: Literal["annual", "point_in_time", "quarterly", "ytd", "unknown"] = "unknown"
    restated: bool = False
    how: str = ""


class StatementLocation(BaseModel):
    key: str
    statement_type: StatementType
    title: str
    scope: Scope | None
    pages: list[int] = []
    sheet: str | None = None
    currency: str | None = None
    scale: Scale | None = None
    columns: list[PeriodColumn] = []
    evidence: list[Evidence] = []


class DocumentUnderstanding(BaseModel):
    artifact_type: Literal["document_understanding"] = "document_understanding"
    schema_version: Literal["1"] = "1"
    entity_name: str | None
    entity_evidence: list[Evidence] = []
    document_type: Literal["annual_report", "financial_statements", "workbook", "unknown"] = "unknown"
    framework: str = "unknown"
    fiscal_year_end: str | None = None  # "MM-DD"
    statements: list[StatementLocation] = []
    missing_statements: list[StatementType] = []
    notes_present: bool = False
    note_refs: list[str] = []
    digital_pages: list[int] = []
    scanned_pages: list[int] = []
    dash_means_zero: bool = False
    unsupported_entity: bool = False
    unsupported_reason: str | None = None
    questions: list[Question] = []
    security_findings: list[str] = []


class TableExtractionSummary(BaseModel):
    artifact_type: Literal["table_extraction"] = "table_extraction"
    schema_version: Literal["1"] = "1"
    extraction_artifact_id: str
    statements: list[dict] = []  # {key, statement_id, rows, cells, unreadable, low_confidence}
    retried_pages: list[int] = []
    cache_hit: bool = False
    method: str = ""
    warnings: list[str] = []


class MappingCandidate(BaseModel):
    code: str
    score: str
    reason: str


class MappingDecision(BaseModel):
    row_id: str
    proposed_code: str | None
    score: str | None = None
    confidence: Literal["high", "medium", "low", "none"]
    rationale: str
    alternatives: list[MappingCandidate] = []


class MappingResult(BaseModel):
    artifact_type: Literal["mapping"] = "mapping"
    schema_version: Literal["1"] = "1"
    taxonomy_version: str
    decisions: list[MappingDecision]


class ReconciliationNote(BaseModel):
    calculation_result_id: str
    possible_causes: list[str]
    suggested_action: str
    reextract_row_ids: list[str] = []


class ReconciliationResult(BaseModel):
    artifact_type: Literal["reconciliation"] = "reconciliation"
    schema_version: Literal["1"] = "1"
    spread_id: str
    spread_version_no: int
    notes: list[ReconciliationNote] = []
    exceptions_created: int = 0
    retries_requested: int = 0


class PackClaim(BaseModel):
    text: str
    refs: list[str] = Field(description="IDs of observations or calculation results that support every number in text")


class PackSection(BaseModel):
    heading: Literal["Financial trends", "Data completeness", "Validation exceptions", "Analyst adjustments",
                     "Comparability limitations", "Questions requiring review"]
    claims: list[PackClaim]


class AnalystPack(BaseModel):
    artifact_type: Literal["analyst_pack"] = "analyst_pack"
    schema_version: Literal["1"] = "1"
    sections: list[PackSection]
    rejected_claims: list[str] = []
