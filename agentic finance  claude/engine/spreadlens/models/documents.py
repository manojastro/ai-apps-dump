"""Company, reporting entity, document, document version, statement, extracted rows/cells, notes."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, Date, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from spreadlens.models.base import MONEY, Base, created_col, id_col


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(300))
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # Banks, insurers and other specialised financial institutions are unsupported for automatic spreading.
    supported: Mapped[bool] = mapped_column(Boolean, default=True)
    unsupported_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = created_col()


class ReportingEntity(Base):
    __tablename__ = "reporting_entities"
    __table_args__ = (UniqueConstraint("company_id", "name", "scope"),)
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(300))
    scope: Mapped[str] = mapped_column(String(20))  # standalone | consolidated
    created_at: Mapped[datetime] = created_col()


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    created_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = created_col()


class DocumentVersion(Base):
    """An uploaded file. A new upload of the same document is a new revision (version_no + 1)."""

    __tablename__ = "document_versions"
    __table_args__ = (UniqueConstraint("document_id", "version_no"),)
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    version_no: Mapped[int] = mapped_column(Integer, default=1)
    filename: Mapped[str] = mapped_column(String(300))
    media_type: Mapped[str] = mapped_column(String(100))
    file_kind: Mapped[str] = mapped_column(String(10))  # pdf | xlsx
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    storage_key: Mapped[str] = mapped_column(String(500))
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    integrity_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | ok | rejected
    integrity_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    duplicate_of_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(30), default="uploaded")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)  # confirmed document-level metadata
    uploaded_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = created_col()


class Statement(Base):
    """One financial statement located in one document version (immutable extraction output)."""

    __tablename__ = "statements"
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    document_version_id: Mapped[str] = mapped_column(ForeignKey("document_versions.id", ondelete="CASCADE"), index=True)
    entity_id: Mapped[str | None] = mapped_column(ForeignKey("reporting_entities.id"), nullable=True, index=True)
    statement_type: Mapped[str] = mapped_column(String(20))  # balance_sheet | income_statement | cash_flow
    scope: Mapped[str | None] = mapped_column(String(20), nullable=True)
    title: Mapped[str] = mapped_column(String(300))
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    scale: Mapped[str | None] = mapped_column(String(20), nullable=True)
    framework: Mapped[str] = mapped_column(String(40), default="unknown")
    pages: Mapped[list] = mapped_column(JSON, default=list)
    sheet: Mapped[str | None] = mapped_column(String(100), nullable=True)
    columns: Mapped[list] = mapped_column(JSON, default=list)  # [{index, header_raw, period_end, period_start, duration, restated}]
    sign_convention: Mapped[dict] = mapped_column(JSON, default=dict)
    extraction_method: Mapped[str] = mapped_column(String(30))  # pdf_text | ocr_local | xlsx_cells
    parser_version: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default="extracted")
    created_at: Mapped[datetime] = created_col()


class ExtractedRow(Base):
    __tablename__ = "extracted_rows"
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    statement_id: Mapped[str] = mapped_column(ForeignKey("statements.id", ondelete="CASCADE"), index=True)
    row_index: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(Text)  # original source text, never edited
    section_path: Mapped[list] = mapped_column(JSON, default=list)  # headings above this row
    level: Mapped[int] = mapped_column(Integer, default=0)
    is_header: Mapped[bool] = mapped_column(Boolean, default=False)
    is_total: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_total_row_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    note_ref: Mapped[str | None] = mapped_column(String(20), nullable=True)
    unit_type: Mapped[str] = mapped_column(String(20), default="monetary")  # monetary | eps | percent | shares
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox: Mapped[list | None] = mapped_column(JSON, nullable=True)
    flags: Mapped[list] = mapped_column(JSON, default=list)


class ExtractedCell(Base):
    """Immutable raw extraction. Corrections never modify this table."""

    __tablename__ = "extracted_cells"
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    statement_id: Mapped[str] = mapped_column(ForeignKey("statements.id", ondelete="CASCADE"), index=True)
    row_id: Mapped[str] = mapped_column(ForeignKey("extracted_rows.id", ondelete="CASCADE"), index=True)
    column_index: Mapped[int] = mapped_column(Integer)
    raw_text: Mapped[str] = mapped_column(Text)
    value_state: Mapped[str] = mapped_column(String(20))  # value | zero | missing | unreadable | not_applicable | dash_ambiguous
    parsed_value: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)
    decimals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parse_notes: Mapped[list] = mapped_column(JSON, default=list)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox: Mapped[list | None] = mapped_column(JSON, nullable=True)  # [x0, top, x1, bottom] in PDF points
    sheet: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cell_ref: Mapped[str | None] = mapped_column(String(20), nullable=True)
    extraction_method: Mapped[str] = mapped_column(String(30))
    ocr_confidence: Mapped[float | None] = mapped_column(nullable=True)


class NoteSection(Base):
    __tablename__ = "note_sections"
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    document_version_id: Mapped[str] = mapped_column(ForeignKey("document_versions.id", ondelete="CASCADE"), index=True)
    note_ref: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(300))
    text: Mapped[str] = mapped_column(Text)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sheet: Mapped[str | None] = mapped_column(String(100), nullable=True)
    scope: Mapped[str | None] = mapped_column(String(20), nullable=True)


class ExtractionCache(Base):
    """Extraction output cached by (document hash, parser version, configuration hash)."""

    __tablename__ = "extraction_cache"
    __table_args__ = (UniqueConstraint("workspace_id", "sha256", "parser_version", "config_hash"),)
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)  # never shared across tenants
    sha256: Mapped[str] = mapped_column(String(64))
    parser_version: Mapped[str] = mapped_column(String(40))
    config_hash: Mapped[str] = mapped_column(String(64))
    artifact_id: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = created_col()


class ReportingPeriod(Base):
    __tablename__ = "reporting_periods"
    __table_args__ = (UniqueConstraint("entity_id", "period_end", "duration"),)
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    entity_id: Mapped[str] = mapped_column(ForeignKey("reporting_entities.id", ondelete="CASCADE"), index=True)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date] = mapped_column(Date)
    duration: Mapped[str] = mapped_column(String(20))  # annual | point_in_time | quarterly | ytd
    label: Mapped[str] = mapped_column(String(40))
