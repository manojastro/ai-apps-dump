"""Normalization (ordinary code): immutable extracted cells -> normalized observations.

Rules: preserve source values; convert scales with exact decimal factors; record every sign change;
keep EPS / percent / share counts out of monetary scaling; never combine currencies (a spread is
single-currency); keep standalone and consolidated apart (a spread is single-scope).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from spreadlens.agents.contracts import DocumentUnderstanding
from spreadlens.extraction.periods import period_start_for
from spreadlens.models import (
    Company,
    DocumentVersion,
    ExtractedCell,
    ExtractedRow,
    MappingProposal,
    Observation,
    ReportingEntity,
    ReportingPeriod,
    Spread,
    Statement,
)
from spreadlens.numeric.scale import SCALE_FACTORS
from spreadlens.taxonomy.loader import load_taxonomy

NON_MONETARY_SCALE = {"eps": "per_share", "percent": "percent", "shares": "count"}


class MetadataIncomplete(Exception):
    pass


def current_code(db: Session, row_id: str) -> tuple[str | None, str | None]:
    p = db.scalar(select(MappingProposal).where(MappingProposal.row_id == row_id, MappingProposal.is_current.is_(True)))
    if p is None:
        return None, None
    if p.status == "rejected":
        return None, p.id
    return (p.decided_code or p.proposed_code), p.id


def get_or_create_spread(db: Session, company: Company, entity_name: str, scope: str, currency: str) -> Spread:
    # serialise entity/spread creation per company (parallel documents of one company)
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": f"entity:{company.id}"})
    ent = db.scalar(select(ReportingEntity).where(ReportingEntity.company_id == company.id, ReportingEntity.scope == scope))
    if ent is None:
        ent = ReportingEntity(workspace_id=company.workspace_id, company_id=company.id, name=entity_name, scope=scope)
        db.add(ent)
        db.flush()
    sp = db.scalar(select(Spread).where(Spread.entity_id == ent.id, Spread.currency == currency))
    if sp is None:
        sp = Spread(workspace_id=company.workspace_id, company_id=company.id, entity_id=ent.id, scope=scope, currency=currency,
                    display_scale="crores" if currency == "INR" else "millions")
        db.add(sp)
        db.flush()
    return sp


def _expense_negative_convention(rows: list[ExtractedRow], cells: dict[str, list[ExtractedCell]]) -> bool:
    tax = load_taxonomy().by_code()
    neg = pos = 0
    for r in rows:
        sec = " ".join(r.section_path).lower()
        if "expense" not in sec:
            continue
        for c in cells.get(r.id, []):
            if c.parsed_value is not None and c.parsed_value != 0:
                neg += c.parsed_value < 0
                pos += c.parsed_value > 0
    _ = tax
    return neg > 0 and neg >= 0.6 * (neg + pos)


def normalize_document(db: Session, dv: DocumentVersion, du: DocumentUnderstanding, company: Company) -> list[str]:
    """Create observations for every non-header row/cell of the document. Returns spread ids touched."""
    tax = load_taxonomy().by_code()
    touched: set[str] = set()
    stmts = list(db.scalars(select(Statement).where(Statement.document_version_id == dv.id)))
    # idempotent: remove observations from a previous attempt for this document version
    for o in db.scalars(select(Observation).where(Observation.document_version_id == dv.id)):
        db.delete(o)
    db.flush()
    for st in stmts:
        if not st.scope or not st.currency:
            raise MetadataIncomplete(f"statement {st.title!r} lacks confirmed scope/currency")
        rows = list(db.scalars(select(ExtractedRow).where(ExtractedRow.statement_id == st.id).order_by(ExtractedRow.row_index)))
        cells_by_row: dict[str, list[ExtractedCell]] = {}
        for c in db.scalars(select(ExtractedCell).where(ExtractedCell.statement_id == st.id)):
            cells_by_row.setdefault(c.row_id, []).append(c)
        needs_scale = any(r.unit_type == "monetary" and cells_by_row.get(r.id) for r in rows)
        if needs_scale and not st.scale:
            raise MetadataIncomplete(f"statement {st.title!r} lacks a confirmed scale")
        spread = get_or_create_spread(db, company, du.entity_name or company.name, st.scope, st.currency)
        st.entity_id = spread.entity_id
        touched.add(spread.id)
        expenses_negative = st.statement_type == "income_statement" and _expense_negative_convention(rows, cells_by_row)
        st.sign_convention = {"expenses_presented_negative": expenses_negative}
        cols = {c["column_index"]: c for c in st.columns}
        latest = max((date.fromisoformat(c["period_end"]) for c in st.columns if c.get("period_end")), default=None)
        for c in st.columns:
            if c.get("period_end"):
                pe = date.fromisoformat(c["period_end"])
                dur = c.get("duration") or "unknown"
                if not db.scalar(select(ReportingPeriod).where(ReportingPeriod.entity_id == spread.entity_id,
                                                               ReportingPeriod.period_end == pe, ReportingPeriod.duration == dur)):
                    db.add(ReportingPeriod(workspace_id=dv.workspace_id, entity_id=spread.entity_id, period_end=pe, duration=dur,
                                           period_start=period_start_for(pe, dur), label=f"FY{pe.year}" if dur in ("annual", "point_in_time") else pe.isoformat()))
                    db.flush()
        for r in rows:
            if r.is_header:
                continue
            code, proposal_id = current_code(db, r.id)
            item = tax.get(code) if code else None
            for cell in cells_by_row.get(r.id, []):
                col = cols.get(cell.column_index)
                if not col or not col.get("period_end"):
                    continue
                pe = date.fromisoformat(col["period_end"])
                dur = col.get("duration") or "unknown"
                transformations = [{"step": "parse", "raw": cell.raw_text, "state": cell.value_state,
                                    "value": None if cell.parsed_value is None else format(cell.parsed_value, "f"), "notes": cell.parse_notes}]
                norm: Decimal | None = None
                if cell.parsed_value is not None:
                    if r.unit_type == "monetary":
                        factor = SCALE_FACTORS[st.scale]  # type: ignore[index]
                        norm = cell.parsed_value * factor
                        transformations.append({"step": "scale", "from": st.scale, "to": "units", "factor": format(factor, "f"),
                                                "value": format(norm, "f")})
                    else:
                        norm = cell.parsed_value
                        transformations.append({"step": "unit", "unit_type": r.unit_type, "note": "not scaled (non-monetary unit)"})
                    if item is not None and item.sign == "positive" and norm < 0 and expenses_negative and "expense" in " ".join(r.section_path).lower():
                        norm = -norm
                        transformations.append({"step": "sign_flip", "reason": "statement presents expenses as negative figures; canonical sign is positive",
                                                "value": format(norm, "f")})
                restated = bool(col.get("restated"))
                version_kind = "restated" if restated else ("comparative" if latest and pe < latest else "original")
                conf = {"mapping": None, "ocr": cell.ocr_confidence, "parse": "exact" if cell.value_state in ("value", "zero") else cell.value_state}
                if proposal_id:
                    p = db.get(MappingProposal, proposal_id)
                    conf["mapping"] = p.confidence if p else None
                db.add(Observation(
                    workspace_id=dv.workspace_id, spread_id=spread.id, document_version_id=dv.id, source_sha256=dv.sha256,
                    entity_id=spread.entity_id, statement_id=st.id, row_id=r.id, cell_id=cell.id, statement_type=st.statement_type,
                    scope=st.scope, framework=st.framework or "unknown", period_start=period_start_for(pe, dur) if st.statement_type != "balance_sheet" else None,
                    period_end=pe, duration=dur, original_label=r.label, canonical_code=code, mapping_proposal_id=proposal_id,
                    unit_type=r.unit_type, raw_text=cell.raw_text, value_state=cell.value_state, parsed_value=cell.parsed_value,
                    source_decimals=cell.decimals, original_currency=st.currency,
                    original_scale=st.scale if r.unit_type == "monetary" else NON_MONETARY_SCALE.get(r.unit_type),
                    normalized_value=norm, normalized_scale="units" if r.unit_type == "monetary" else NON_MONETARY_SCALE.get(r.unit_type, "units"),
                    current_value=norm, current_state=cell.value_state, origin="reported", version_kind=version_kind,
                    page=cell.page, bbox=cell.bbox, sheet=cell.sheet, cell_ref=cell.cell_ref, extraction_method=cell.extraction_method,
                    confidence=conf, review_status="unreviewed", transformations=transformations,
                ))
    db.flush()
    return sorted(touched)


def presented_sign(o: Observation) -> int:
    return -1 if any(t.get("step") == "sign_flip" for t in (o.transformations or [])) else 1
