"""Analyst review actions, preparer/reviewer sign-off and snapshot exports.

Every action records user, time, reason and before/after values in `analyst_adjustments`, and
any action that changes a figure, mapping or unit triggers deterministic recalculation.
Original extracted values stay untouched in `extracted_cells` and `observations.parsed_value`.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from spreadlens.agents import analyst_pack
from spreadlens.agents.runtime import AgentContext
from spreadlens.config import Settings, TAXONOMY_VERSION
from spreadlens.exports.excel import render_workbook
from spreadlens.exports.pdf import render_pdf
from spreadlens.exports.snapshot import build_snapshot
from spreadlens.models import (
    AnalystAdjustment,
    ExportSnapshot,
    ExtractedRow,
    MappingProposal,
    Observation,
    ReviewDecision,
    Spread,
    Statement,
    ValidationException,
    utcnow,
)
from spreadlens.numeric.decimal_utils import dstr
from spreadlens.numeric.parse import parse_number
from spreadlens.numeric.scale import SCALE_FACTORS
from spreadlens.services.artifacts import content_hash
from spreadlens.services.audit import audit, metric
from spreadlens.services.spread import doc_level_critical, open_critical, recompute
from spreadlens.storage.base import get_storage, make_key
from spreadlens.taxonomy.loader import load_taxonomy


def _adjust(db: Session, spread: Spread, user_id: str, action: str, reason: str, before: dict, after: dict,
            observation_id: str | None = None, row_id: str | None = None, field: str | None = None) -> AnalystAdjustment:
    if not reason or len(reason.strip()) < 3:
        raise HTTPException(422, "A reason is required")
    a = AnalystAdjustment(workspace_id=spread.workspace_id, spread_id=spread.id, observation_id=observation_id, row_id=row_id,
                          action=action, field=field, before=before, after=after, reason=reason.strip()[:2000], user_id=user_id,
                          spread_version_before=spread.current_version_no)
    db.add(a)
    db.flush()
    return a


def _finish(db: Session, spread: Spread, adj: AnalystAdjustment, reason: str, user_id: str) -> int:
    v = recompute(db, spread, f"{adj.action}: {reason}"[:200], user_id)
    adj.spread_version_after = v
    audit(db, spread.workspace_id, user_id, f"review.{adj.action}", "spread", spread.id,
          details={"adjustment_id": adj.id, "version": v})
    metric(db, spread.workspace_id, "review.correction", 1, action=adj.action)
    return v


def correct_value(db: Session, spread: Spread, obs: Observation, new_value: str, reason: str, user_id: str) -> int:
    p = parse_number(new_value)
    if not p.has_number or p.value is None:
        raise HTTPException(422, "Enter a number as shown in the source (e.g. 1,234.50 or (12.00))")
    factor = SCALE_FACTORS[obs.original_scale] if obs.unit_type == "monetary" and obs.original_scale in SCALE_FACTORS else Decimal(1)
    new_norm = p.value * factor
    if any(t.get("step") == "sign_flip" for t in obs.transformations or []):
        new_norm = -new_norm
    before = {"value_units": dstr(obs.current_value), "state": obs.current_state, "raw_text": obs.raw_text}
    obs.current_value, obs.current_state = new_norm, "zero" if new_norm == 0 else "value"
    obs.review_status = "corrected"
    obs.transformations = [*obs.transformations, {"step": "analyst_correction", "entered": new_value, "value": format(new_norm, "f"),
                                                   "reason": reason[:300], "user": user_id, "at": utcnow().isoformat()}]
    adj = _adjust(db, spread, user_id, "correct_value", reason, before,
                  {"value_units": dstr(new_norm), "entered": new_value, "scale": obs.original_scale}, observation_id=obs.id, field="value")
    return _finish(db, spread, adj, reason, user_id)


def _row_obs(db: Session, row_id: str) -> list[Observation]:
    return list(db.scalars(select(Observation).where(Observation.row_id == row_id)))


def set_mapping(db: Session, spread: Spread, row: ExtractedRow, code: str | None, action: str, reason: str, user_id: str) -> int:
    tax = load_taxonomy().by_code()
    st = db.get(Statement, row.statement_id)
    if code is not None and (code not in tax or tax[code].statement != st.statement_type):  # type: ignore[union-attr]
        raise HTTPException(422, "Unknown canonical item for this statement type")
    prop = db.scalar(select(MappingProposal).where(MappingProposal.row_id == row.id, MappingProposal.is_current.is_(True)))
    before = {"code": (prop.decided_code or prop.proposed_code) if prop else None, "status": prop.status if prop else None}
    if prop is None:
        prop = MappingProposal(workspace_id=row.workspace_id, row_id=row.id, taxonomy_version=TAXONOMY_VERSION, proposed_code=None,
                               original_label=row.label, rationale="created by analyst", confidence="none", status="proposed")
        db.add(prop)
    if action == "accept_mapping":
        prop.status, prop.decided_code = "accepted", prop.proposed_code
        code = prop.proposed_code
    elif action == "reject_mapping":
        prop.status, prop.decided_code = "rejected", None
        code = None
    else:
        prop.status, prop.decided_code = "changed", code
    for o in _row_obs(db, row.id):
        o.canonical_code = code
        o.review_status = "accepted" if action == "accept_mapping" else o.review_status
    adj = _adjust(db, spread, user_id, action, reason, before, {"code": code, "status": prop.status}, row_id=row.id, field="mapping")
    return _finish(db, spread, adj, reason, user_id)


def confirm_unit(db: Session, spread: Spread, st: Statement, scale: str, reason: str, user_id: str) -> int:
    if scale not in SCALE_FACTORS:
        raise HTTPException(422, "Unknown scale")
    before = {"scale": st.scale}
    st.scale = scale
    for o in db.scalars(select(Observation).where(Observation.statement_id == st.id, Observation.unit_type == "monetary")):
        if o.parsed_value is None:
            continue
        sign = -1 if any(t.get("step") == "sign_flip" for t in o.transformations or []) else 1
        o.original_scale = scale
        o.normalized_value = o.parsed_value * SCALE_FACTORS[scale] * sign
        if o.review_status != "corrected":
            o.current_value = o.normalized_value
        o.transformations = [*o.transformations, {"step": "unit_confirmed", "scale": scale, "user": user_id, "value": format(o.normalized_value, "f")}]
    adj = _adjust(db, spread, user_id, "confirm_unit", reason, before, {"scale": scale}, field=f"statement:{st.id}:scale")
    return _finish(db, spread, adj, reason, user_id)


def confirm_period(db: Session, spread: Spread, st: Statement, column_index: int, period_end: str, reason: str, user_id: str) -> int:
    pe = date.fromisoformat(period_end)
    cols = [dict(c) for c in st.columns]
    col = next((c for c in cols if c["column_index"] == column_index), None)
    if col is None:
        raise HTTPException(404, "Column not found")
    before = {"period_end": col.get("period_end")}
    col["period_end"] = pe.isoformat()
    st.columns = cols
    from spreadlens.extraction.periods import period_start_for
    from spreadlens.models import ExtractedCell

    cell_ids = {c.id for c in db.scalars(select(ExtractedCell).where(ExtractedCell.statement_id == st.id,
                                                                    ExtractedCell.column_index == column_index))}
    for o in db.scalars(select(Observation).where(Observation.statement_id == st.id, Observation.cell_id.in_(cell_ids))):
        o.period_end = pe
        o.period_start = period_start_for(pe, o.duration) if o.statement_type != "balance_sheet" else None
        o.transformations = [*o.transformations, {"step": "period_confirmed", "period_end": pe.isoformat(), "user": user_id}]
    adj = _adjust(db, spread, user_id, "confirm_period", reason, before, {"period_end": pe.isoformat()}, field=f"statement:{st.id}:col{column_index}")
    return _finish(db, spread, adj, reason, user_id)


def mark_unresolved(db: Session, spread: Spread, obs: Observation, reason: str, user_id: str) -> int:
    before = {"review_status": obs.review_status}
    obs.review_status = "unresolved"
    adj = _adjust(db, spread, user_id, "mark_unresolved", reason, before, {"review_status": "unresolved"}, observation_id=obs.id)
    return _finish(db, spread, adj, reason, user_id)


def add_adjustment(db: Session, spread: Spread, code: str, period_end: str, value: str, reason: str, user_id: str,
                   template: Observation) -> int:
    """Analyst adjustment as a separate observation (origin='adjusted'); the reported figure stays visible."""
    tax = load_taxonomy().by_code()
    if code not in tax:
        raise HTTPException(422, "Unknown canonical item")
    p = parse_number(value)
    if not p.has_number or p.value is None:
        raise HTTPException(422, "Invalid number")
    scale = template.original_scale or "units"
    norm = p.value * SCALE_FACTORS.get(scale, Decimal(1))
    o = Observation(workspace_id=spread.workspace_id, spread_id=spread.id, document_version_id=template.document_version_id,
                    source_sha256=template.source_sha256, entity_id=spread.entity_id, statement_id=template.statement_id,
                    row_id=template.row_id, cell_id=template.cell_id, statement_type=tax[code].statement, scope=spread.scope,
                    framework=template.framework, period_end=date.fromisoformat(period_end), duration=template.duration,
                    original_label=f"Analyst adjustment: {tax[code].label}", canonical_code=code, unit_type="monetary",
                    raw_text=value, value_state="value", parsed_value=p.value, source_decimals=p.decimals,
                    original_currency=spread.currency, original_scale=scale, normalized_value=norm, current_value=norm,
                    current_state="zero" if norm == 0 else "value", origin="adjusted", version_kind="original",
                    extraction_method="analyst", confidence={"analyst": True}, review_status="corrected",
                    transformations=[{"step": "analyst_adjustment", "entered": value, "scale": scale, "reason": reason[:300], "user": user_id}])
    db.add(o)
    db.flush()
    adj = _adjust(db, spread, user_id, "add_adjustment", reason, {}, {"code": code, "period_end": period_end, "value": value, "scale": scale},
                  observation_id=o.id, field=code)
    return _finish(db, spread, adj, reason, user_id)


def accept_exception(db: Session, spread: Spread, exc: ValidationException, explanation: str, user_id: str) -> None:
    if not explanation or len(explanation.strip()) < 5:
        raise HTTPException(422, "An explanation is required to accept an exception")
    before = {"status": exc.status}
    exc.status, exc.resolution_note, exc.resolved_by, exc.resolved_at = "explained", explanation.strip()[:2000], user_id, utcnow()
    _adjust(db, spread, user_id, "accept_exception", explanation, before, {"status": "explained", "exception_id": exc.id}, field="exception")
    audit(db, spread.workspace_id, user_id, "review.accept_exception", "exception", exc.id)


def submit_for_review(db: Session, spread: Spread, user_id: str, role: str, comment: str | None) -> ReviewDecision:
    if spread.current_version_no == 0:
        raise HTTPException(409, "Nothing to review yet")
    spread.review_status = "submitted_for_review"
    d = ReviewDecision(workspace_id=spread.workspace_id, spread_id=spread.id, spread_version_no=spread.current_version_no,
                       decision="submit_for_review", user_id=user_id, role=role, comment=comment)
    db.add(d)
    audit(db, spread.workspace_id, user_id, "review.submit", "spread", spread.id, details={"version": spread.current_version_no})
    return d


def blocking_reasons(db: Session, spread: Spread) -> list[str]:
    reasons = [f"Critical exception open: {e.title}" for e in open_critical(db, spread)]
    reasons += [f"Critical document issue open: {e.title}" for e in doc_level_critical(db, spread)]
    return reasons


def approve(db: Session, settings: Settings, spread: Spread, user_id: str, role: str, comment: str | None,
            expected_version: int) -> tuple[ReviewDecision, ExportSnapshot]:
    if role not in ("reviewer", "admin"):
        raise HTTPException(403, "Only a reviewer can approve")
    if expected_version != spread.current_version_no:
        raise HTTPException(409, f"Version changed: you reviewed v{expected_version}, current is v{spread.current_version_no}")
    if spread.review_status != "submitted_for_review":
        raise HTTPException(409, "The preparer must submit this version for review first")
    sub = db.scalar(select(ReviewDecision).where(ReviewDecision.spread_id == spread.id, ReviewDecision.decision == "submit_for_review",
                                                 ReviewDecision.spread_version_no == spread.current_version_no,
                                                 ReviewDecision.is_stale.is_(False)).order_by(ReviewDecision.created_at.desc()))
    if sub is not None and sub.user_id == user_id:
        raise HTTPException(409, "The reviewer must be a different person from the preparer (four-eyes rule)")
    reasons = blocking_reasons(db, spread)
    if reasons:
        raise HTTPException(409, {"message": "Approval blocked", "reasons": reasons})
    d = ReviewDecision(workspace_id=spread.workspace_id, spread_id=spread.id, spread_version_no=spread.current_version_no,
                       decision="approve", user_id=user_id, role=role, comment=comment)
    db.add(d)
    db.flush()
    spread.review_status = "approved"
    snap = create_export(db, settings, spread, user_id, status="approved")
    d.snapshot_id = snap.id
    audit(db, spread.workspace_id, user_id, "review.approve", "spread", spread.id,
          details={"version": spread.current_version_no, "snapshot_id": snap.id})
    return d, snap


def reopen(db: Session, spread: Spread, user_id: str, role: str, comment: str | None) -> ReviewDecision:
    if role not in ("reviewer", "admin"):
        raise HTTPException(403, "Only a reviewer can reopen")
    spread.review_status = "reopened"
    for d in db.scalars(select(ReviewDecision).where(ReviewDecision.spread_id == spread.id, ReviewDecision.is_stale.is_(False))):
        d.is_stale, d.stale_reason = True, f"Reopened: {comment or 'no comment'}"
    d = ReviewDecision(workspace_id=spread.workspace_id, spread_id=spread.id, spread_version_no=spread.current_version_no,
                       decision="reopen", user_id=user_id, role=role, comment=comment)
    db.add(d)
    audit(db, spread.workspace_id, user_id, "review.reopen", "spread", spread.id)
    return d


def create_export(db: Session, settings: Settings, spread: Spread, user_id: str, status: str = "draft") -> ExportSnapshot:
    """Freeze a snapshot, generate the narrative from it, render XLSX and PDF from the same frozen dict."""
    snap = build_snapshot(db, spread, user_id)
    if status == "draft":
        snap["approval"] = None
        snap["review_status"] = "unreviewed_draft"
    ctx = AgentContext(db=db, settings=settings, workspace_id=spread.workspace_id, run=None, mode=settings.agent_mode)
    pack = analyst_pack.run(ctx, snap).model_dump(mode="json")
    snap["narrative"] = pack
    snap["content_hash"] = content_hash({k: v for k, v in snap.items() if k != "content_hash"})
    rec = ExportSnapshot(workspace_id=spread.workspace_id, spread_id=spread.id, spread_version_no=spread.current_version_no,
                         status=status, content_hash=snap["content_hash"], snapshot=snap, created_by=user_id)
    db.add(rec)
    db.flush()
    storage = get_storage(settings)
    try:
        xlsx = render_workbook(snap, pack, status)
        pdf = render_pdf(snap, pack, status)
        rec.xlsx_key = make_key(spread.workspace_id, "exports", rec.id, "review-pack.xlsx")
        rec.pdf_key = make_key(spread.workspace_id, "exports", rec.id, "review-pack.pdf")
        storage.put(rec.xlsx_key, xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        storage.put(rec.pdf_key, pdf, "application/pdf")
        rec.render_status = "ok"
    except Exception as exc:  # noqa: BLE001
        rec.render_status, rec.render_error = "failed", f"{type(exc).__name__}: {exc}"[:500]
        metric(db, spread.workspace_id, "export.failure", 1, spread_id=spread.id)
    audit(db, spread.workspace_id, user_id, "export.create", "export", rec.id, details={"status": status, "version": spread.current_version_no})
    return rec
