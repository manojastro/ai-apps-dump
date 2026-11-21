"""Statement grid, evidence, validation queue, review actions, sign-off and exports."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from spreadlens.api.deps import J, scoped
from spreadlens.config import get_settings
from spreadlens.db import get_db
from spreadlens.exports.snapshot import display
from spreadlens.models import (
    AnalystAdjustment,
    CalculationResult,
    Company,
    DocumentVersion,
    ExportSnapshot,
    ExtractedCell,
    ExtractedRow,
    MappingProposal,
    NoteSection,
    Observation,
    ReportingEntity,
    ReviewDecision,
    Spread,
    SpreadVersion,
    Statement,
    User,
    ValidationException,
)
from spreadlens.numeric.decimal_utils import dstr
from spreadlens.numeric.scale import SCALE_FACTORS
from spreadlens.security.auth import Principal, get_principal
from spreadlens.services import review
from spreadlens.services.audit import audit
from spreadlens.storage.base import get_storage, key_belongs_to
from spreadlens.taxonomy.loader import load_taxonomy

router = APIRouter(prefix="/api", tags=["spreads"])


def _users(db: Session) -> dict[str, str]:
    return {u.id: u.display_name for u in db.scalars(select(User))}


@router.get("/spreads/{spread_id}")
def spread_detail(spread_id: str, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    sp, role = scoped(db, Spread, spread_id, p)
    company = db.get(Company, sp.company_id)
    ent = db.get(ReportingEntity, sp.entity_id)
    users = _users(db)
    versions = [{"version": v.version_no, "reason": v.reason, "hash": v.content_hash[:16], "statement_hashes": v.statement_hashes,
                 "by": users.get(v.created_by or ""), "at": v.created_at}
                for v in db.scalars(select(SpreadVersion).where(SpreadVersion.spread_id == sp.id).order_by(SpreadVersion.version_no.desc()))]
    decisions = [{"id": d.id, "decision": d.decision, "user": users.get(d.user_id), "role": d.role, "version": d.spread_version_no,
                  "comment": d.comment, "stale": d.is_stale, "stale_reason": d.stale_reason, "at": d.created_at, "snapshot_id": d.snapshot_id}
                 for d in db.scalars(select(ReviewDecision).where(ReviewDecision.spread_id == sp.id).order_by(ReviewDecision.created_at.desc()))]
    docs = sorted({o for (o,) in db.execute(select(Observation.document_version_id).where(Observation.spread_id == sp.id).distinct())})
    return J({"id": sp.id, "company": {"id": company.id, "name": company.name} if company else None,
              "entity": {"id": ent.id, "name": ent.name} if ent else None, "scope": sp.scope, "currency": sp.currency,
              "display_scale": sp.display_scale, "version": sp.current_version_no, "review_status": sp.review_status, "role": role,
              "versions": versions, "decisions": decisions, "blocking": review.blocking_reasons(db, sp), "document_version_ids": docs,
              "agent_mode": get_settings().agent_mode})


@router.get("/spreads/{spread_id}/grid")
def grid(spread_id: str, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    sp, _ = scoped(db, Spread, spread_id, p)
    tax = load_taxonomy().by_code()
    obs = list(db.scalars(select(Observation).where(Observation.spread_id == sp.id)))
    periods = sorted({o.period_end for o in obs if o.duration in ("annual", "point_in_time")}, reverse=True)
    calcs = list(db.scalars(select(CalculationResult).where(CalculationResult.spread_id == sp.id,
                                                            CalculationResult.spread_version_no == sp.current_version_no,
                                                            CalculationResult.kind == "validation")))
    obs_status: dict[str, list[dict]] = {}
    for c in calcs:
        for oid in c.input_observation_ids:
            obs_status.setdefault(oid, []).append({"rule": c.rule_id, "status": c.status, "id": c.id})
    props = {x.row_id: x for x in db.scalars(select(MappingProposal).where(MappingProposal.row_id.in_({o.row_id for o in obs}),
                                                                           MappingProposal.is_current.is_(True)))}
    rows_meta = {r.id: r for r in db.scalars(select(ExtractedRow).where(ExtractedRow.id.in_({o.row_id for o in obs})))}
    stmts = {s.id: s for s in db.scalars(select(Statement).where(Statement.id.in_({o.statement_id for o in obs})))}
    dvs = {d.id: d for d in db.scalars(select(DocumentVersion).where(DocumentVersion.id.in_({o.document_version_id for o in obs})))}
    out: dict[str, list] = {"balance_sheet": [], "income_statement": [], "cash_flow": []}
    by_row: dict[tuple[str, str], dict] = {}
    for o in sorted(obs, key=lambda o: (stmts[o.statement_id].document_version_id if o.statement_id in stmts else "",
                                        rows_meta[o.row_id].row_index if o.row_id in rows_meta else 0)):
        key = (o.statement_type, o.row_id if o.origin != "adjusted" else f"adj:{o.id}")
        r = by_row.get(key)
        if r is None:
            row = rows_meta.get(o.row_id)
            prop = props.get(o.row_id)
            item = tax.get(o.canonical_code or "")
            st = stmts.get(o.statement_id)
            r = {"row_id": o.row_id, "original_label": o.original_label, "canonical_code": o.canonical_code,
                 "canonical_label": item.label if item else None, "order": item.order if item else 9000 + (row.row_index if row else 0),
                 "is_total": bool(row.is_total) if row else False, "level": row.level if row else 0, "unit_type": o.unit_type,
                 "origin": o.origin, "document": dvs[o.document_version_id].filename if o.document_version_id in dvs else None,
                 "document_version_id": o.document_version_id, "statement_title": st.title if st else None,
                 "scale": o.original_scale, "currency": o.original_currency,
                 "mapping": {"status": prop.status, "confidence": prop.confidence, "rationale": prop.rationale,
                             "alternatives": prop.alternatives, "proposed_code": prop.proposed_code} if prop else None,
                 "cells": {}}
            by_row[key] = r
            out.setdefault(o.statement_type, []).append(r)
        r["cells"][o.period_end.isoformat()] = {
            "observation_id": o.id, "display": display(o, sp.display_scale), "raw_text": o.raw_text, "state": o.current_state,
            "original_state": o.value_state, "review_status": o.review_status, "preferred": o.is_preferred, "version_kind": o.version_kind,
            "duration": o.duration, "confidence": o.confidence, "validation": obs_status.get(o.id, []),
            "corrected": o.review_status == "corrected", "original_display": None if o.normalized_value is None else
            dstr(o.normalized_value / SCALE_FACTORS[sp.display_scale] if o.unit_type == "monetary" else o.normalized_value)}
    for k in out:
        out[k].sort(key=lambda r: (r["canonical_code"] is None, r["order"], r["document"] or ""))
    metrics = [{"id": c.id, "metric": c.rule_id, "title": c.title, "period_end": c.period_end, "value": dstr(c.value), "unit": c.unit,
                "status": c.status, "formula": c.expression, "explanation": c.explanation, "limitations": c.limitations,
                "inputs": c.input_observation_ids}
               for c in db.scalars(select(CalculationResult).where(CalculationResult.spread_id == sp.id,
                                                                   CalculationResult.spread_version_no == sp.current_version_no,
                                                                   CalculationResult.kind == "metric"))]
    return J({"spread_id": sp.id, "version": sp.current_version_no, "currency": sp.currency, "display_scale": sp.display_scale,
              "scope": sp.scope, "periods": [x.isoformat() for x in periods], "statements": out, "metrics": metrics,
              "taxonomy": [{"code": i.code, "label": i.label, "statement": i.statement} for i in load_taxonomy().items]})


@router.get("/observations/{obs_id}")
def evidence(obs_id: str, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    o, _ = scoped(db, Observation, obs_id, p)
    cell = db.get(ExtractedCell, o.cell_id)
    row = db.get(ExtractedRow, o.row_id)
    st = db.get(Statement, o.statement_id)
    dv = db.get(DocumentVersion, o.document_version_id)
    prop = db.get(MappingProposal, o.mapping_proposal_id) if o.mapping_proposal_id else None
    note = None
    if row and row.note_ref:
        n = db.scalar(select(NoteSection).where(NoteSection.document_version_id == o.document_version_id, NoteSection.note_ref == row.note_ref))
        if n:
            note = {"ref": n.note_ref, "title": n.title, "text": n.text[:3000], "page": n.page}
    users = _users(db)
    adjs = [{"action": a.action, "before": a.before, "after": a.after, "reason": a.reason, "user": users.get(a.user_id), "at": a.created_at,
             "version_before": a.spread_version_before, "version_after": a.spread_version_after}
            for a in db.scalars(select(AnalystAdjustment).where((AnalystAdjustment.observation_id == o.id) | (AnalystAdjustment.row_id == o.row_id))
                                .order_by(AnalystAdjustment.created_at))]
    others = [{"id": x.id, "document": x.document_version_id, "value": dstr(x.current_value), "version_kind": x.version_kind,
               "preferred": x.is_preferred, "raw_text": x.raw_text}
              for x in db.scalars(select(Observation).where(Observation.spread_id == o.spread_id, Observation.canonical_code == o.canonical_code,
                                                            Observation.period_end == o.period_end, Observation.id != o.id))] if o.canonical_code else []
    audit(db, o.workspace_id, p.id, "evidence.view", "observation", o.id)
    return J({
        "observation": {"id": o.id, "label": o.original_label, "code": o.canonical_code, "period_end": o.period_end, "period_start": o.period_start,
                        "duration": o.duration, "statement_type": o.statement_type, "scope": o.scope, "framework": o.framework,
                        "raw_text": o.raw_text, "value_state": o.value_state, "parsed_value": dstr(o.parsed_value), "source_decimals": o.source_decimals,
                        "original_currency": o.original_currency, "original_scale": o.original_scale,
                        "normalized_value": dstr(o.normalized_value), "normalized_scale": o.normalized_scale,
                        "current_value": dstr(o.current_value), "current_state": o.current_state, "origin": o.origin,
                        "version_kind": o.version_kind, "preferred": o.is_preferred, "review_status": o.review_status,
                        "extraction_method": o.extraction_method, "confidence": o.confidence, "transformations": o.transformations,
                        "source_sha256": o.source_sha256, "unit_type": o.unit_type},
        "source": {"document_version_id": o.document_version_id, "filename": dv.filename if dv else None, "kind": dv.file_kind if dv else None,
                   "page": o.page, "bbox": o.bbox, "row_bbox": row.bbox if row else None, "sheet": o.sheet, "cell_ref": o.cell_ref,
                   "label_cell": None, "statement_title": st.title if st else None, "statement_pages": st.pages if st else [],
                   "parse_notes": cell.parse_notes if cell else [], "ocr_confidence": cell.ocr_confidence if cell else None},
        "row": {"id": row.id, "section_path": row.section_path, "note_ref": row.note_ref, "is_total": row.is_total, "flags": row.flags} if row else None,
        "mapping": {"id": prop.id, "proposed_code": prop.proposed_code, "decided_code": prop.decided_code, "status": prop.status,
                    "confidence": prop.confidence, "rationale": prop.rationale, "alternatives": prop.alternatives} if prop else None,
        "note": note, "adjustments": adjs, "other_sources": others})


@router.get("/spreads/{spread_id}/validations")
def validations(spread_id: str, version: int | None = None, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    sp, _ = scoped(db, Spread, spread_id, p)
    v = version or sp.current_version_no
    rows = db.scalars(select(CalculationResult).where(CalculationResult.spread_id == sp.id, CalculationResult.spread_version_no == v,
                                                      CalculationResult.kind == "validation").order_by(CalculationResult.period_end.desc(), CalculationResult.rule_id))
    return J({"version": v, "results": [{"id": c.id, "rule_id": c.rule_id, "rule_version": c.rule_version, "title": c.title,
                                         "statement_type": c.statement_type, "period_end": c.period_end, "inputs": c.input_observation_ids,
                                         "expression": c.expression, "expected": dstr(c.expected), "observed": dstr(c.observed),
                                         "difference": dstr(c.difference), "tolerance": dstr(c.tolerance), "tolerance_basis": c.tolerance_basis,
                                         "severity": c.severity, "status": c.status, "explanation": c.explanation, "source_refs": c.source_refs}
                                        for c in rows]})


@router.get("/spreads/{spread_id}/exceptions")
def exceptions(spread_id: str, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    sp, _ = scoped(db, Spread, spread_id, p)
    dv_ids = {o for (o,) in db.execute(select(Observation.document_version_id).where(Observation.spread_id == sp.id).distinct())}
    q = select(ValidationException).where((ValidationException.spread_id == sp.id) |
                                          ((ValidationException.document_version_id.in_(dv_ids)) & (ValidationException.spread_id.is_(None))))
    users = _users(db)
    rank = {"critical": 0, "warning": 1, "info": 2}
    items = sorted(db.scalars(q), key=lambda e: (e.status not in ("open",), rank.get(e.severity, 3), e.title))
    return J([{"id": e.id, "category": e.category, "severity": e.severity, "title": e.title, "detail": e.detail, "status": e.status,
               "observation_ids": e.observation_ids, "row_ids": e.row_ids, "calculation_result_id": e.calculation_result_id,
               "suggested_action": e.suggested_action, "agent_explanation": e.agent_explanation, "resolution_note": e.resolution_note,
               "resolved_by": users.get(e.resolved_by or ""), "first_seen_version": e.first_seen_version,
               "last_seen_version": e.last_seen_version, "document_level": e.spread_id is None} for e in items])


class ActionIn(BaseModel):
    action: Literal["correct_value", "change_mapping", "accept_mapping", "reject_mapping", "confirm_unit", "confirm_period",
                    "mark_unresolved", "add_adjustment", "accept_exception", "request_reextraction"]
    reason: str
    observation_id: str | None = None
    row_id: str | None = None
    statement_id: str | None = None
    exception_id: str | None = None
    value: str | None = None
    code: str | None = None
    scale: str | None = None
    period_end: str | None = None
    column_index: int | None = None


@router.post("/spreads/{spread_id}/actions")
def action(spread_id: str, body: ActionIn, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    sp, role = scoped(db, Spread, spread_id, p, "analyst", f"review.{body.action}")
    if sp.review_status == "approved" and body.action not in ("request_reextraction",):
        raise HTTPException(409, "This version is approved. A reviewer must reopen it before changes.")

    def obs_in_spread() -> Observation:
        o = db.get(Observation, body.observation_id or "")
        if o is None or o.spread_id != sp.id:
            raise HTTPException(404, "Observation not found in this spread")
        return o

    def row_in_spread() -> ExtractedRow:
        r = db.get(ExtractedRow, body.row_id or "")
        if r is None or not db.scalar(select(Observation.id).where(Observation.row_id == r.id, Observation.spread_id == sp.id).limit(1)):
            raise HTTPException(404, "Row not found in this spread")
        return r

    def stmt_in_spread() -> Statement:
        s = db.get(Statement, body.statement_id or "")
        if s is None or not db.scalar(select(Observation.id).where(Observation.statement_id == s.id, Observation.spread_id == sp.id).limit(1)):
            raise HTTPException(404, "Statement not found in this spread")
        return s

    a = body.action
    version = sp.current_version_no
    if a == "correct_value":
        version = review.correct_value(db, sp, obs_in_spread(), body.value or "", body.reason, p.id)
    elif a in ("change_mapping", "accept_mapping", "reject_mapping"):
        version = review.set_mapping(db, sp, row_in_spread(), body.code, a, body.reason, p.id)
    elif a == "confirm_unit":
        version = review.confirm_unit(db, sp, stmt_in_spread(), body.scale or "", body.reason, p.id)
    elif a == "confirm_period":
        version = review.confirm_period(db, sp, stmt_in_spread(), body.column_index or 0, body.period_end or "", body.reason, p.id)
    elif a == "mark_unresolved":
        version = review.mark_unresolved(db, sp, obs_in_spread(), body.reason, p.id)
    elif a == "add_adjustment":
        version = review.add_adjustment(db, sp, body.code or "", body.period_end or "", body.value or "", body.reason, p.id, obs_in_spread())
    elif a == "accept_exception":
        e = db.get(ValidationException, body.exception_id or "")
        if e is None or e.workspace_id != sp.workspace_id:
            raise HTTPException(404, "Exception not found")
        review.accept_exception(db, sp, e, body.reason, p.id)
    elif a == "request_reextraction":
        r = row_in_spread()
        st = db.get(Statement, r.statement_id)
        dv = db.get(DocumentVersion, st.document_version_id)  # type: ignore[union-attr]
        from spreadlens.workflow.coordinator import start_run

        run = start_run(db, get_settings(), dv, p.id, kind="reextraction", first_stage="reextract",  # type: ignore[arg-type]
                        payload={"pages": [r.page] if r.page else [], "row_ids": [r.id], "reason": body.reason[:300]})
        review._adjust(db, sp, p.id, "request_reextraction", body.reason, {}, {"run_id": run.id, "page": r.page}, row_id=r.id)
        return J({"ok": True, "run_id": run.id, "version": version})
    return J({"ok": True, "version": version, "review_status": sp.review_status})


class DecisionIn(BaseModel):
    comment: str | None = None
    version: int | None = None


@router.post("/spreads/{spread_id}/submit")
def submit(spread_id: str, body: DecisionIn, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    sp, role = scoped(db, Spread, spread_id, p, "analyst", "review.submit")
    review.submit_for_review(db, sp, p.id, role, body.comment)
    return J({"ok": True, "review_status": sp.review_status, "version": sp.current_version_no})


@router.post("/spreads/{spread_id}/approve")
def approve(spread_id: str, body: DecisionIn, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    sp, role = scoped(db, Spread, spread_id, p, "reviewer", "review.approve")
    d, snap = review.approve(db, get_settings(), sp, p.id, role, body.comment, body.version if body.version is not None else -1)
    return J({"ok": True, "review_status": sp.review_status, "snapshot_id": snap.id, "version": sp.current_version_no,
              "render_status": snap.render_status})


@router.post("/spreads/{spread_id}/reopen")
def reopen(spread_id: str, body: DecisionIn, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    sp, role = scoped(db, Spread, spread_id, p, "reviewer", "review.reopen")
    review.reopen(db, sp, p.id, role, body.comment)
    return J({"ok": True, "review_status": sp.review_status})


@router.post("/spreads/{spread_id}/exports")
def create_draft_export(spread_id: str, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    sp, _ = scoped(db, Spread, spread_id, p, "analyst", "export.create")
    if sp.current_version_no == 0:
        raise HTTPException(409, "No data to export yet")
    snap = review.create_export(db, get_settings(), sp, p.id, status="approved" if sp.review_status == "approved" and _approved_snapshot_current(db, sp) else "draft")
    return J({"id": snap.id, "status": snap.status, "version": snap.spread_version_no, "render_status": snap.render_status,
              "error": snap.render_error}, 201)


def _approved_snapshot_current(db: Session, sp: Spread) -> bool:
    return db.scalar(select(ReviewDecision).where(ReviewDecision.spread_id == sp.id, ReviewDecision.decision == "approve",
                                                  ReviewDecision.spread_version_no == sp.current_version_no,
                                                  ReviewDecision.is_stale.is_(False))) is not None


@router.get("/spreads/{spread_id}/exports")
def list_exports(spread_id: str, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    sp, _ = scoped(db, Spread, spread_id, p)
    users = _users(db)
    return J([{"id": e.id, "version": e.spread_version_no, "status": e.status, "hash": e.content_hash, "render_status": e.render_status,
               "error": e.render_error, "created_at": e.created_at, "by": users.get(e.created_by),
               "stale": e.spread_version_no != sp.current_version_no}
              for e in db.scalars(select(ExportSnapshot).where(ExportSnapshot.spread_id == sp.id).order_by(ExportSnapshot.created_at.desc()))])


@router.get("/exports/{export_id}")
def export_detail(export_id: str, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    e, _ = scoped(db, ExportSnapshot, export_id, p)
    return J({"id": e.id, "status": e.status, "version": e.spread_version_no, "hash": e.content_hash, "snapshot": e.snapshot})


@router.get("/exports/{export_id}/download/{fmt}")
def download(export_id: str, fmt: Literal["xlsx", "pdf"], p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    e, _ = scoped(db, ExportSnapshot, export_id, p, "analyst", "export.download")
    key = e.xlsx_key if fmt == "xlsx" else e.pdf_key
    if not key or not key_belongs_to(key, e.workspace_id) or e.render_status != "ok":
        raise HTTPException(404, "Export file not available")
    audit(db, e.workspace_id, p.id, "export.download", "export", e.id, details={"format": fmt})
    sp = db.get(Spread, e.spread_id)
    name = f"spreadlens_{(e.snapshot.get('company') or {}).get('name', 'company').replace(' ', '_')}_v{e.spread_version_no}_{e.status}.{fmt}"
    media = "application/pdf" if fmt == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return Response(get_storage(get_settings()).get(key), media_type=media,
                    headers={"Content-Disposition": f'attachment; filename="{name}"', "X-Snapshot-Hash": e.content_hash,
                             "X-Snapshot-Stale": str(sp is not None and sp.current_version_no != e.spread_version_no).lower(),
                             "Cache-Control": "private, no-store"})


@router.get("/spreads/{spread_id}/adjustments")
def spread_adjustments(spread_id: str, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    sp, _ = scoped(db, Spread, spread_id, p)
    users = _users(db)
    rows = db.scalars(select(AnalystAdjustment).where(AnalystAdjustment.spread_id == sp.id).order_by(AnalystAdjustment.created_at.desc()))
    return J([{"id": a.id, "action": a.action, "field": a.field, "before": a.before, "after": a.after, "reason": a.reason,
               "user": users.get(a.user_id), "at": a.created_at, "version_before": a.spread_version_before,
               "version_after": a.spread_version_after, "observation_id": a.observation_id} for a in rows])
