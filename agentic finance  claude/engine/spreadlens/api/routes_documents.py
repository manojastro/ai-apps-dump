"""Workspace dashboard, companies, uploads, documents, source evidence, metadata questions, runs."""

from __future__ import annotations

import io

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from spreadlens.api.deps import J, scoped
from spreadlens.config import get_settings
from spreadlens.db import get_db
from spreadlens.extraction.integrity import check_upload
from spreadlens.models import (
    AgentExecution,
    AnalystAdjustment,
    Company,
    Document,
    DocumentVersion,
    ExportSnapshot,
    MetadataQuestion,
    Observation,
    Spread,
    Statement,
    ValidationException,
    WorkflowRun,
    WorkflowTask,
    Workspace,
    utcnow,
)
from spreadlens.security.auth import Principal, get_principal, require_member
from spreadlens.services.audit import audit, metric
from spreadlens.storage.base import get_storage, key_belongs_to, make_key
from spreadlens.workflow.coordinator import resume_gate, retry_failed_stage, start_run

router = APIRouter(prefix="/api", tags=["documents"])


@router.get("/workspaces/{ws_id}/dashboard")
def dashboard(ws_id: str, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    role = require_member(db, p, ws_id)
    ws = db.get(Workspace, ws_id)
    companies = list(db.scalars(select(Company).where(Company.workspace_id == ws_id).order_by(Company.created_at.desc())))
    spreads = list(db.scalars(select(Spread).where(Spread.workspace_id == ws_id)))
    open_ex = db.execute(select(ValidationException.severity, func.count()).where(
        ValidationException.workspace_id == ws_id, ValidationException.status == "open").group_by(ValidationException.severity)).all()
    runs = db.execute(select(WorkflowRun.status, func.count()).where(WorkflowRun.workspace_id == ws_id).group_by(WorkflowRun.status)).all()
    obs_n = db.scalar(select(func.count()).select_from(Observation).where(Observation.workspace_id == ws_id)) or 0
    corrected = db.scalar(select(func.count()).select_from(Observation).where(Observation.workspace_id == ws_id,
                                                                              Observation.review_status == "corrected")) or 0
    cost = db.execute(select(func.coalesce(func.sum(AgentExecution.cost_usd), 0), func.coalesce(func.sum(AgentExecution.tokens_in), 0),
                             func.coalesce(func.sum(AgentExecution.tokens_out), 0)).where(AgentExecution.workspace_id == ws_id)).one()
    recent = db.scalars(select(WorkflowRun).where(WorkflowRun.workspace_id == ws_id).order_by(WorkflowRun.created_at.desc()).limit(8))
    by_company = {}
    for sp in spreads:
        by_company.setdefault(sp.company_id, []).append({"id": sp.id, "scope": sp.scope, "currency": sp.currency,
                                                         "version": sp.current_version_no, "review_status": sp.review_status})
    return J({
        "workspace": {"id": ws.id, "name": ws.name, "role": role, "retention_days": ws.retention_days},  # type: ignore[union-attr]
        "agent_mode": get_settings().agent_mode,
        "companies": [{"id": c.id, "name": c.name, "industry": c.industry, "supported": c.supported,
                       "unsupported_reason": c.unsupported_reason, "spreads": by_company.get(c.id, [])} for c in companies],
        "open_exceptions": {s: n for s, n in open_ex}, "runs": {s: n for s, n in runs},
        "correction_rate": (corrected / obs_n) if obs_n else 0.0, "observations": obs_n,
        "cost": {"usd": float(cost[0]), "tokens_in": int(cost[1]), "tokens_out": int(cost[2])},
        "recent_runs": [{"id": r.id, "status": r.status, "state": r.state, "mode": r.agent_mode, "created_at": r.created_at,
                         "document_version_id": r.document_version_id} for r in recent],
    })


class CompanyIn(BaseModel):
    name: str
    industry: str | None = None


@router.post("/workspaces/{ws_id}/companies")
def create_company(ws_id: str, body: CompanyIn, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    require_member(db, p, ws_id, "analyst", "company.create")
    c = Company(workspace_id=ws_id, name=body.name.strip()[:300], industry=(body.industry or "")[:120] or None, created_by=p.id)
    db.add(c)
    db.flush()
    audit(db, ws_id, p.id, "company.create", "company", c.id)
    return J({"id": c.id, "name": c.name}, 201)


@router.get("/companies/{company_id}")
def company_detail(company_id: str, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    c, role = scoped(db, Company, company_id, p)
    docs = []
    for d in db.scalars(select(Document).where(Document.company_id == c.id).order_by(Document.created_at.desc())):
        versions = []
        for dv in db.scalars(select(DocumentVersion).where(DocumentVersion.document_id == d.id).order_by(DocumentVersion.version_no.desc())):
            run = db.scalar(select(WorkflowRun).where(WorkflowRun.document_version_id == dv.id).order_by(WorkflowRun.created_at.desc()))
            open_q = db.scalar(select(func.count()).select_from(MetadataQuestion).where(MetadataQuestion.document_version_id == dv.id,
                                                                                        MetadataQuestion.answer.is_(None))) or 0
            versions.append({"id": dv.id, "version_no": dv.version_no, "filename": dv.filename, "kind": dv.file_kind,
                             "size": dv.size_bytes, "pages": dv.page_count, "sha256": dv.sha256, "status": dv.processing_status,
                             "integrity": dv.integrity_status, "duplicate_of": dv.duplicate_of_id, "created_at": dv.created_at,
                             "open_questions": open_q,
                             "run": {"id": run.id, "status": run.status, "state": run.state, "mode": run.agent_mode, "error": run.error} if run else None})
        docs.append({"id": d.id, "title": d.title, "versions": versions})
    spreads = [{"id": s.id, "scope": s.scope, "currency": s.currency, "version": s.current_version_no, "review_status": s.review_status,
                "display_scale": s.display_scale} for s in db.scalars(select(Spread).where(Spread.company_id == c.id))]
    return J({"company": {"id": c.id, "name": c.name, "industry": c.industry, "supported": c.supported,
                          "unsupported_reason": c.unsupported_reason, "workspace_id": c.workspace_id},
              "role": role, "documents": docs, "spreads": spreads})


@router.post("/companies/{company_id}/documents")
async def upload(company_id: str, file: UploadFile = File(...), title: str | None = Form(default=None),
                 p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    settings = get_settings()
    company, _ = scoped(db, Company, company_id, p, "analyst", "document.upload")
    data = await file.read(settings.max_upload_bytes + 1)
    filename = (file.filename or "upload").replace("\\", "/").split("/")[-1][:300]
    res = check_upload(filename, data, settings)
    if not res.ok:
        audit(db, company.workspace_id, p.id, "document.upload", "company", company.id, outcome="denied",
              details={"reason": res.detail, "size": res.size})
        metric(db, company.workspace_id, "upload.rejected", 1)
        db.commit()
        raise HTTPException(422, res.detail)
    title = (title or filename).strip()[:300]
    doc = db.scalar(select(Document).where(Document.company_id == company.id, Document.title == title))
    if doc is None:
        doc = Document(workspace_id=company.workspace_id, company_id=company.id, title=title, created_by=p.id)
        db.add(doc)
        db.flush()
    last_no = db.scalar(select(func.max(DocumentVersion.version_no)).where(DocumentVersion.document_id == doc.id)) or 0
    dup = db.scalar(select(DocumentVersion).join(Document, Document.id == DocumentVersion.document_id)
                    .where(Document.company_id == company.id, DocumentVersion.sha256 == res.sha256,
                           DocumentVersion.duplicate_of_id.is_(None)))
    key = make_key(company.workspace_id, "documents", res.sha256, f"source.{res.file_kind}")
    storage = get_storage(settings)
    if not storage.exists(key):
        storage.put(key, data, res.media_type or "application/octet-stream")
    dv = DocumentVersion(workspace_id=company.workspace_id, document_id=doc.id, version_no=last_no + 1, filename=filename,
                         media_type=res.media_type or "", file_kind=res.file_kind or "", size_bytes=res.size, sha256=res.sha256,
                         storage_key=key, page_count=res.page_count, integrity_status="ok",
                         integrity_detail="; ".join(res.warnings or []) or "ok", duplicate_of_id=dup.id if dup else None,
                         uploaded_by=p.id)
    db.add(dv)
    db.flush()
    run = start_run(db, settings, dv, p.id)
    audit(db, company.workspace_id, p.id, "document.upload", "document_version", dv.id,
          details={"size": res.size, "kind": res.file_kind, "duplicate": bool(dup), "revision": last_no + 1})
    return J({"document_version_id": dv.id, "document_id": doc.id, "version_no": dv.version_no, "run_id": run.id,
              "duplicate_of": dv.duplicate_of_id, "warnings": res.warnings or []}, 201)


@router.get("/documents/{dv_id}")
def document_detail(dv_id: str, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    dv, role = scoped(db, DocumentVersion, dv_id, p)
    doc = db.get(Document, dv.document_id)
    runs = list(db.scalars(select(WorkflowRun).where(WorkflowRun.document_version_id == dv.id).order_by(WorkflowRun.created_at.desc())))
    qs = list(db.scalars(select(MetadataQuestion).where(MetadataQuestion.document_version_id == dv.id).order_by(MetadataQuestion.created_at)))
    stmts = [{"id": s.id, "type": s.statement_type, "title": s.title, "scope": s.scope, "currency": s.currency, "scale": s.scale,
              "pages": s.pages, "sheet": s.sheet, "columns": s.columns, "method": s.extraction_method, "framework": s.framework}
             for s in db.scalars(select(Statement).where(Statement.document_version_id == dv.id))]
    excs = [{"id": e.id, "category": e.category, "severity": e.severity, "title": e.title, "detail": e.detail, "status": e.status}
            for e in db.scalars(select(ValidationException).where(ValidationException.document_version_id == dv.id,
                                                                  ValidationException.spread_id.is_(None)))]
    return J({"id": dv.id, "document_id": dv.document_id, "title": doc.title if doc else dv.filename, "company_id": doc.company_id if doc else None,
              "filename": dv.filename, "kind": dv.file_kind, "pages": dv.page_count, "sha256": dv.sha256, "size": dv.size_bytes,
              "version_no": dv.version_no, "status": dv.processing_status, "integrity": dv.integrity_status,
              "integrity_detail": dv.integrity_detail, "duplicate_of": dv.duplicate_of_id, "role": role,
              "runs": [_run_summary(db, r) for r in runs], "questions": [
                  {"id": q.id, "field": q.field, "statement_key": q.statement_key, "question": q.question, "options": q.options,
                   "evidence": q.evidence, "answer": q.answer, "answered_at": q.answered_at} for q in qs],
              "statements": stmts, "document_exceptions": excs})


def _run_summary(db: Session, r: WorkflowRun) -> dict:
    tasks = list(db.scalars(select(WorkflowTask).where(WorkflowTask.run_id == r.id).order_by(WorkflowTask.created_at)))
    return {"id": r.id, "kind": r.run_kind, "mode": r.agent_mode, "state": r.state, "status": r.status, "error": r.error,
            "usage": r.usage, "budget": r.budget, "created_at": r.created_at, "finished_at": r.finished_at,
            "correlation_id": r.correlation_id,
            "tasks": [{"id": t.id, "stage": t.stage, "status": t.status, "attempts": t.attempts, "max_attempts": t.max_attempts,
                       "duration_ms": t.duration_ms, "error": t.last_error} for t in tasks]}


@router.get("/runs/{run_id}")
def run_trace(run_id: str, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    r, _ = scoped(db, WorkflowRun, run_id, p)
    exes = [{"id": e.id, "agent": e.agent, "mode": e.mode, "model": e.model, "status": e.status, "tools": e.tools_used,
             "input_artifacts": e.input_artifact_ids, "output_artifact": e.output_artifact_id, "retries": e.retries,
             "tokens_in": e.tokens_in, "tokens_out": e.tokens_out, "cost_usd": e.cost_usd, "duration_ms": e.duration_ms,
             "error": e.error, "created_at": e.created_at}
            for e in db.scalars(select(AgentExecution).where(AgentExecution.run_id == r.id).order_by(AgentExecution.created_at))]
    return J({**_run_summary(db, r), "agent_executions": exes})


@router.post("/runs/{run_id}/retry")
def retry_run(run_id: str, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    r, _ = scoped(db, WorkflowRun, run_id, p, "analyst", "run.retry")
    try:
        t = retry_failed_stage(db, r, p.id)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return J({"retried_stage": t.stage, "run_id": r.id})


class AnswerIn(BaseModel):
    answer: str


@router.post("/questions/{q_id}/answer")
def answer_question(q_id: str, body: AnswerIn, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    q, _ = scoped(db, MetadataQuestion, q_id, p, "analyst", "metadata.confirm")
    ans = body.answer.strip()[:200]
    if q.field in ("scope", "scale", "currency") and q.options and ans not in q.options and q.field != "currency":
        raise HTTPException(422, f"Answer must be one of {q.options}")
    if q.field == "period":
        from datetime import date

        try:
            date.fromisoformat(ans)
        except ValueError as exc:
            raise HTTPException(422, "Period end must be an ISO date (YYYY-MM-DD)") from exc
    if q.field == "currency" and (len(ans) != 3 or not ans.isalpha()):
        raise HTTPException(422, "Currency must be a 3-letter ISO code")
    q.answer, q.answered_by, q.answered_at = (ans.upper() if q.field == "currency" else ans), p.id, utcnow()
    audit(db, q.workspace_id, p.id, "metadata.confirm", "question", q.id, details={"field": q.field})
    remaining = db.scalar(select(func.count()).select_from(MetadataQuestion).where(MetadataQuestion.run_id == q.run_id,
                                                                                   MetadataQuestion.answer.is_(None))) or 0
    if remaining == 0:
        run = db.get(WorkflowRun, q.run_id)
        if run:
            resume_gate(db, run)
    return J({"ok": True, "remaining": remaining})


@router.get("/documents/{dv_id}/file")
def document_file(dv_id: str, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    dv, _ = scoped(db, DocumentVersion, dv_id, p, "analyst", "document.read")
    if not key_belongs_to(dv.storage_key, dv.workspace_id):
        raise HTTPException(404, "Not found")
    audit(db, dv.workspace_id, p.id, "document.read", "document_version", dv.id)
    return Response(get_storage(get_settings()).get(dv.storage_key), media_type=dv.media_type,
                    headers={"Content-Disposition": f'inline; filename="{dv.filename}"', "Cache-Control": "private, no-store",
                             "X-Content-Type-Options": "nosniff"})


@router.get("/documents/{dv_id}/pages/{page_no}")
def document_page(dv_id: str, page_no: int, dpi: int = 110, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    """Server-rendered page image for the side-by-side source viewer (no PDF JS needed in the browser)."""
    dv, _ = scoped(db, DocumentVersion, dv_id, p, "analyst", "document.read")
    if dv.file_kind != "pdf" or not (1 <= page_no <= (dv.page_count or 0)):
        raise HTTPException(404, "Not found")
    import pypdfium2 as pdfium

    from spreadlens.extraction.ocr import _PDFIUM_LOCK

    data = get_storage(get_settings()).get(dv.storage_key)
    dpi = max(50, min(dpi, 200))
    with _PDFIUM_LOCK:
        pdf = pdfium.PdfDocument(io.BytesIO(data))
        try:
            page = pdf[page_no - 1]
            w, h = page.get_size()
            img = page.render(scale=dpi / 72).to_pil()
        finally:
            pdf.close()
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return Response(buf.getvalue(), media_type="image/png",
                    headers={"X-Page-Width-Pt": str(w), "X-Page-Height-Pt": str(h), "Cache-Control": "private, max-age=300",
                             "Access-Control-Expose-Headers": "X-Page-Width-Pt, X-Page-Height-Pt"})


@router.get("/documents/{dv_id}/sheet")
def document_sheet(dv_id: str, name: str, cell: str | None = None, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    """Worksheet cells around a reference, for spreadsheet source inspection (values only, no formulas executed)."""
    dv, _ = scoped(db, DocumentVersion, dv_id, p, "analyst", "document.read")
    if dv.file_kind != "xlsx":
        raise HTTPException(404, "Not found")
    from openpyxl import load_workbook
    from openpyxl.utils import column_index_from_string, coordinate_from_string, get_column_letter

    wb = load_workbook(io.BytesIO(get_storage(get_settings()).get(dv.storage_key)), data_only=True, read_only=True)
    if name not in wb.sheetnames:
        raise HTTPException(404, "Sheet not found")
    ws = wb[name]
    r0, c0 = 1, 1
    if cell:
        col, r = coordinate_from_string(cell)
        r0, c0 = max(1, r - 8), 1
        _ = column_index_from_string(col)
    rows = []
    for r in ws.iter_rows(min_row=r0, max_row=r0 + 22, min_col=c0, max_col=min(c0 + 7, ws.max_column or 8), values_only=False):
        rows.append([{"ref": f"{get_column_letter(c.column)}{c.row}", "value": None if c.value is None else str(c.value)}
                     for c in r if hasattr(c, "column")])
    return J({"sheet": name, "focus": cell, "rows": rows, "sheets": wb.sheetnames})


@router.delete("/documents/{dv_id}")
def delete_document(dv_id: str, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    """Admin deletion (retention): removes the file and all derived records for this document version."""
    dv, _ = scoped(db, DocumentVersion, dv_id, p, "admin", "document.delete")
    spreads = {o.spread_id for o in db.scalars(select(Observation).where(Observation.document_version_id == dv.id))}
    others = db.scalar(select(func.count()).select_from(DocumentVersion).where(DocumentVersion.sha256 == dv.sha256,
                                                                                DocumentVersion.workspace_id == dv.workspace_id,
                                                                                DocumentVersion.id != dv.id)) or 0
    if others == 0:
        get_storage(get_settings()).delete(dv.storage_key)
    db.delete(dv)
    db.flush()
    from spreadlens.services.spread import recompute

    for sid in spreads:
        sp = db.get(Spread, sid)
        if sp:
            recompute(db, sp, f"document {dv.filename} deleted", p.id)
    audit(db, dv.workspace_id, p.id, "document.delete", "document_version", dv_id)
    return J({"deleted": dv_id})


@router.get("/workspaces/{ws_id}/audit")
def audit_log(ws_id: str, limit: int = 200, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    require_member(db, p, ws_id, "reviewer", "audit.read")
    from spreadlens.models import AuditEvent, User

    users = {u.id: u.display_name for u in db.scalars(select(User))}
    rows = db.scalars(select(AuditEvent).where(AuditEvent.workspace_id == ws_id).order_by(AuditEvent.created_at.desc()).limit(min(limit, 1000)))
    return J([{"at": a.created_at, "user": users.get(a.user_id or "", a.user_id), "action": a.action, "target": a.target_type,
               "target_id": a.target_id, "outcome": a.outcome, "details": a.details, "correlation_id": a.correlation_id} for a in rows])


@router.get("/workspaces/{ws_id}/exports")
def workspace_exports(ws_id: str, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    require_member(db, p, ws_id)
    out = []
    for e in db.scalars(select(ExportSnapshot).where(ExportSnapshot.workspace_id == ws_id).order_by(ExportSnapshot.created_at.desc()).limit(200)):
        sp = db.get(Spread, e.spread_id)
        out.append({"id": e.id, "spread_id": e.spread_id, "version": e.spread_version_no, "status": e.status, "hash": e.content_hash,
                    "render_status": e.render_status, "created_at": e.created_at,
                    "stale": sp is not None and sp.current_version_no != e.spread_version_no,
                    "company": (e.snapshot.get("company") or {}).get("name"), "scope": (e.snapshot.get("entity") or {}).get("scope")})
    return J(out)


@router.get("/workspaces/{ws_id}/adjustments")
def workspace_adjustments(ws_id: str, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    require_member(db, p, ws_id)
    from spreadlens.models import User

    users = {u.id: u.display_name for u in db.scalars(select(User))}
    rows = db.scalars(select(AnalystAdjustment).where(AnalystAdjustment.workspace_id == ws_id).order_by(AnalystAdjustment.created_at.desc()).limit(500))
    return J([{"id": a.id, "spread_id": a.spread_id, "action": a.action, "field": a.field, "before": a.before, "after": a.after,
               "reason": a.reason, "user": users.get(a.user_id), "at": a.created_at, "version_before": a.spread_version_before,
               "version_after": a.spread_version_after, "observation_id": a.observation_id} for a in rows])
