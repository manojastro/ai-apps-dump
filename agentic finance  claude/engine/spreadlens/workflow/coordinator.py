"""Bounded workflow coordinator.

How one uploaded document moves through the application:
  upload (integrity checked synchronously) -> run created -> tasks, one stage at a time:
    integrity -> understand -> extract -> map -> await_metadata (gate) -> normalize -> reconcile -> done
  Each stage is a durable task row. Only the transitions in NEXT are allowed. A gate blocks the
  run (status awaiting_input) until the analyst answers metadata questions. Independent
  documents run in parallel because each has its own tasks; OCR pages run in parallel inside
  the extraction tool (bounded).

How durable execution recovers after interruption:
  * a worker claims a task with SELECT ... FOR UPDATE SKIP LOCKED and a lease;
  * the stage's writes, the task's success and the next task's insert commit in ONE transaction,
    so a crash before commit leaves no partial state; the expired lease lets another worker
    claim the task again (attempts + 1, bounded by max_attempts);
  * enqueueing uses a unique idempotency key, so replaying a stage never duplicates its successor;
  * stage handlers are idempotent (they replace their own previous output for the document version).
"""

from __future__ import annotations

import time
from datetime import timedelta

from sqlalchemy import delete, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from spreadlens.agents import document_understanding, financial_mapping, reconciliation, table_extraction
from spreadlens.agents.contracts import DocumentUnderstanding
from spreadlens.agents.runtime import AgentContext
from spreadlens.config import Settings
from spreadlens.extraction.integrity import sha256_bytes
from spreadlens.models import (
    Artifact,
    Company,
    Document,
    DocumentVersion,
    ExtractedRow,
    MetadataQuestion,
    Spread,
    Statement,
    ValidationException,
    WorkflowRun,
    WorkflowTask,
    new_id,
    utcnow,
)
from spreadlens.services.audit import audit, metric
from spreadlens.services.normalize import normalize_document
from spreadlens.storage.base import get_storage

NEXT = {"integrity": "understand", "understand": "extract", "extract": "map", "map": "await_metadata",
        "await_metadata": "normalize", "normalize": "reconcile", "reconcile": None, "reextract": None}
DOC_STATUS = {"integrity": "checking", "understand": "understanding", "extract": "extracting", "map": "mapping",
              "await_metadata": "awaiting_confirmation", "normalize": "normalizing", "reconcile": "reconciling"}


class Blocked(Exception):
    """Stage cannot proceed until a person acts (not a failure, not retried)."""


class Halt(Exception):
    """Stop the run successfully without further stages (e.g. duplicate or unsupported entity)."""


def enqueue(db: Session, run: WorkflowRun, stage: str, payload: dict, key: str | None = None, max_attempts: int = 3) -> None:
    key = key or f"{run.id}:{stage}"
    db.execute(insert(WorkflowTask).values(
        id=new_id(), workspace_id=run.workspace_id, run_id=run.id, stage=stage, idempotency_key=key, payload=payload,
        status="queued", attempts=0, max_attempts=max_attempts, created_at=utcnow(),
    ).on_conflict_do_nothing(index_elements=["idempotency_key"]))


def start_run(db: Session, settings: Settings, dv: DocumentVersion, user_id: str | None, kind: str = "initial",
              first_stage: str = "integrity", payload: dict | None = None) -> WorkflowRun:
    from spreadlens.observability import correlation_id

    run = WorkflowRun(workspace_id=dv.workspace_id, document_version_id=dv.id, run_kind=kind, agent_mode=settings.agent_mode,
                      state=first_stage, status="running", correlation_id=correlation_id.get(), started_by=user_id,
                      budget={"max_model_calls": settings.budget_max_model_calls, "max_cost_usd": settings.budget_max_cost_usd,
                              "max_ocr_pages": settings.budget_max_ocr_pages}, usage={})
    db.add(run)
    db.flush()
    enqueue(db, run, first_stage, payload or {}, max_attempts=settings.task_max_attempts)
    audit(db, dv.workspace_id, user_id, "workflow.start", "run", run.id, details={"kind": kind, "mode": run.agent_mode})
    return run


def _ctx(db: Session, settings: Settings, run: WorkflowRun, task: WorkflowTask) -> AgentContext:
    return AgentContext(db=db, settings=settings, workspace_id=run.workspace_id, run=run, task_id=task.id, mode=run.agent_mode)


def _doc_exception(db: Session, dv: DocumentVersion, company_id: str, fp: str, category: str, severity: str, title: str, detail: str) -> None:
    e = db.scalar(select(ValidationException).where(ValidationException.document_version_id == dv.id, ValidationException.fingerprint == fp))
    if e is None:
        db.add(ValidationException(workspace_id=dv.workspace_id, company_id=company_id, document_version_id=dv.id, fingerprint=fp,
                                   category=category, severity=severity, title=title[:300], detail=detail, status="open"))


# ------------------------------------------------------------------ stage handlers

def h_integrity(db: Session, settings: Settings, run: WorkflowRun, task: WorkflowTask, dv: DocumentVersion) -> dict:
    data = get_storage(settings).get(dv.storage_key)
    if sha256_bytes(data) != dv.sha256:
        raise RuntimeError("stored file does not match its recorded hash")
    doc = db.get(Document, dv.document_id)
    if dv.duplicate_of_id:
        _doc_exception(db, dv, doc.company_id, "duplicate", "duplicate", "info", "Duplicate upload",  # type: ignore[union-attr]
                       "This file is byte-identical to an earlier upload for this company; it was not processed again.")
        raise Halt("duplicate upload")
    return {}


def h_understand(db: Session, settings: Settings, run: WorkflowRun, task: WorkflowTask, dv: DocumentVersion) -> dict:
    ctx = _ctx(db, settings, run, task)
    du, du_art, raw_art = document_understanding.run(ctx, dv)
    doc = db.get(Document, dv.document_id)
    company = db.get(Company, doc.company_id)  # type: ignore[union-attr]
    db.execute(delete(MetadataQuestion).where(MetadataQuestion.run_id == run.id))
    for q in du.questions:
        db.add(MetadataQuestion(workspace_id=dv.workspace_id, document_version_id=dv.id, run_id=run.id, field=q.field,
                                statement_key=q.statement_key, question=q.question, options=q.options,
                                evidence=[e.model_dump() for e in q.evidence]))
    for i, f in enumerate(du.security_findings):
        _doc_exception(db, dv, company.id, f"injection:{i}", "prompt_injection", "critical",  # type: ignore[union-attr]
                       "Document contains instructions aimed at automated agents",
                       f"Treated as data and ignored. Excerpt: {f[:400]}. A reviewer must acknowledge this before approval.")
    if du.unsupported_entity:
        company.supported, company.unsupported_reason = False, du.unsupported_reason  # type: ignore[union-attr]
        _doc_exception(db, dv, company.id, "unsupported", "unsupported_entity", "critical",  # type: ignore[union-attr]
                       "Unsupported entity type for automatic spreading",
                       f"{du.unsupported_reason}. Banks, insurers and other specialised financial institutions are not supported in this version.")
        raise Halt("unsupported entity")
    if not du.statements:
        _doc_exception(db, dv, company.id, "no_statements", "extraction_failure", "warning", "No financial statements found",  # type: ignore[union-attr]
                       "No balance sheet, income statement or cash flow statement title with period columns was recognised.")
        raise Halt("no statements found")
    return {"du_artifact_id": du_art.id, "raw_artifact_id": raw_art.id}


def _du(db: Session, task: WorkflowTask) -> DocumentUnderstanding:
    art = db.get(Artifact, task.payload["du_artifact_id"])
    return DocumentUnderstanding.model_validate(art.payload)  # type: ignore[union-attr]


def h_extract(db: Session, settings: Settings, run: WorkflowRun, task: WorkflowTask, dv: DocumentVersion) -> dict:
    db.execute(delete(Statement).where(Statement.document_version_id == dv.id))  # idempotent replay
    du = _du(db, task)
    raw = db.get(Artifact, task.payload["raw_artifact_id"])
    summary, art = table_extraction.run(_ctx(db, settings, run, task), dv, du, raw)  # type: ignore[arg-type]
    return {**task.payload, "extraction_summary_id": art.id}


def h_map(db: Session, settings: Settings, run: WorkflowRun, task: WorkflowTask, dv: DocumentVersion) -> dict:
    art = db.get(Artifact, task.payload["extraction_summary_id"])
    _, mart = financial_mapping.run(_ctx(db, settings, run, task), dv, art)
    return {**task.payload, "mapping_artifact_id": mart.id}


def apply_answers(db: Session, dv: DocumentVersion, run_id: str) -> list[MetadataQuestion]:
    qs = list(db.scalars(select(MetadataQuestion).where(MetadataQuestion.run_id == run_id)))
    stmts = list(db.scalars(select(Statement).where(Statement.document_version_id == dv.id)))
    key_to_stmt = {}
    for st in stmts:
        key = f"{st.statement_type}:" + (f"p{st.pages[0]}" if st.pages else str(st.sheet))
        key_to_stmt[key] = st
    meta = dict(dv.metadata_json or {})
    for q in qs:
        if q.answer is None:
            continue
        if q.field == "entity_name":
            meta["entity_name"] = q.answer
            continue
        base_key, _, col = (q.statement_key or "").partition("#col")
        targets = [key_to_stmt[base_key]] if base_key in key_to_stmt else stmts
        for st in targets:
            if q.field == "period" and col:
                cols = [dict(c) for c in st.columns]
                for c in cols:
                    if str(c["column_index"]) == col:
                        c["period_end"] = q.answer
                        c["how"] = "confirmed by analyst"
                st.columns = cols
            elif q.field in ("scope", "currency", "scale"):
                setattr(st, q.field, q.answer)
    dv.metadata_json = meta
    return qs


def h_await_metadata(db: Session, settings: Settings, run: WorkflowRun, task: WorkflowTask, dv: DocumentVersion) -> dict:
    qs = apply_answers(db, dv, run.id)
    open_q = [q for q in qs if q.answer is None]
    if open_q:
        raise Blocked(f"{len(open_q)} metadata question(s) awaiting analyst confirmation")
    return task.payload


def h_normalize(db: Session, settings: Settings, run: WorkflowRun, task: WorkflowTask, dv: DocumentVersion) -> dict:
    du = _du(db, task)
    if dv.metadata_json.get("entity_name"):
        du.entity_name = dv.metadata_json["entity_name"]
    doc = db.get(Document, dv.document_id)
    company = db.get(Company, doc.company_id)  # type: ignore[union-attr]
    spread_ids = normalize_document(db, dv, du, company)  # type: ignore[arg-type]
    return {**task.payload, "spread_ids": spread_ids}


def h_reconcile(db: Session, settings: Settings, run: WorkflowRun, task: WorkflowTask, dv: DocumentVersion) -> dict:
    ctx = _ctx(db, settings, run, task)
    retries: list[str] = []
    for sid in task.payload.get("spread_ids", []):
        spread = db.get(Spread, sid)
        _, _, rows = reconciliation.run(ctx, spread, f"processed {dv.filename}")  # type: ignore[arg-type]
        retries.extend(rows)
    if retries and run.run_kind != "reextraction":
        pages = sorted({r.page for r in db.scalars(select(ExtractedRow).where(ExtractedRow.id.in_(retries))) if r.page})
        if pages:
            enqueue(db, run, "reextract", {"pages": pages, "row_ids": retries, "reason": "low OCR confidence on failed check inputs"},
                    key=f"{run.id}:reextract:auto", max_attempts=1)
    return {**task.payload}


def h_reextract(db: Session, settings: Settings, run: WorkflowRun, task: WorkflowTask, dv: DocumentVersion) -> dict:
    """Targeted re-extraction: re-read pages with forced OCR at higher DPI and report differences.
    It never overwrites a figure; differences become review items for the analyst to accept."""
    from spreadlens.agents.runtime import ExecutionRecorder
    from spreadlens.agents.table_extraction import RETRY_DPI
    from spreadlens.agents.tools import run_extraction
    from spreadlens.models import ExtractedCell, Observation

    ctx = _ctx(db, settings, run, task)
    rec = ExecutionRecorder(ctx, "table_extraction")
    pages = task.payload.get("pages") or []
    art, _ = rec.tool("reextract_pages", run_extraction, ctx, dv, pages if dv.file_kind == "pdf" else None, RETRY_DPI)
    diffs = []
    rows = list(db.scalars(select(ExtractedRow).where(ExtractedRow.id.in_(task.payload.get("row_ids") or []))))
    for row in rows:
        old_cells = {c.column_index: c for c in db.scalars(select(ExtractedCell).where(ExtractedCell.row_id == row.id))}
        for st in art.payload.get("statements", []):
            for r in st.get("rows", []):
                if r["label"].strip().lower() == row.label.strip().lower() and (r.get("page") == row.page or row.page is None):
                    for c in r.get("cells", []):
                        old = old_cells.get(c["column_index"])
                        if old is not None and old.raw_text != c["raw_text"]:
                            diffs.append((row, old, c["raw_text"]))
    for row, old, new in diffs:
        obs = db.scalar(select(Observation).where(Observation.cell_id == old.id))
        db.add(ValidationException(workspace_id=dv.workspace_id, company_id=None, spread_id=obs.spread_id if obs else None,
                                   document_version_id=dv.id, fingerprint=f"reextract:{old.id}:{new}", category="reextraction_result",
                                   severity="warning", title=f"Re-extraction differs: '{row.label}'",
                                   detail=f"Original read '{old.raw_text}', targeted re-read '{new}' (page {row.page}). "
                                          "Not applied automatically: correct the value if the source confirms it.",
                                   observation_ids=[obs.id] if obs else [], row_ids=[row.id], status="open"))
    rec.finish("succeeded", art.id)
    return {"differences": len(diffs)}


HANDLERS = {"integrity": h_integrity, "understand": h_understand, "extract": h_extract, "map": h_map,
            "await_metadata": h_await_metadata, "normalize": h_normalize, "reconcile": h_reconcile, "reextract": h_reextract}


# ------------------------------------------------------------------ execution

def claim(db: Session, worker_id: str, lease_s: int) -> str | None:
    row = db.execute(text("""
        UPDATE workflow_tasks SET status='running', lease_owner=:w, lease_until=now() + make_interval(secs => :lease),
               attempts = attempts + 1, updated_at = now()
        WHERE id = (
            SELECT id FROM workflow_tasks
            WHERE (status='queued' AND (available_at IS NULL OR available_at <= now()))
               OR (status='running' AND lease_until < now())
            ORDER BY created_at
            FOR UPDATE SKIP LOCKED LIMIT 1)
        RETURNING id"""), {"w": worker_id, "lease": lease_s}).first()
    return row[0] if row else None


def execute_task(session_factory, settings: Settings, task_id: str, worker_id: str) -> str:
    """Run one claimed task. Returns the outcome string."""
    from spreadlens.observability import correlation_id

    t0 = time.monotonic()
    db: Session = session_factory()
    try:
        task = db.get(WorkflowTask, task_id)
        if task is None or task.status != "running" or task.lease_owner != worker_id:
            return "skipped"
        run = db.get(WorkflowRun, task.run_id)
        dv = db.get(DocumentVersion, run.document_version_id)  # type: ignore[union-attr]
        correlation_id.set(run.correlation_id)  # type: ignore[union-attr]
        if task.attempts > task.max_attempts:
            raise RuntimeError(f"attempts exhausted ({task.max_attempts})")
        run.state = task.stage  # type: ignore[union-attr]
        if task.stage in DOC_STATUS:
            dv.processing_status = DOC_STATUS[task.stage]  # type: ignore[union-attr]
        out = HANDLERS[task.stage](db, settings, run, task, dv)  # type: ignore[arg-type]
        task.status, task.output_artifact_id = "succeeded", (out or {}).get("du_artifact_id")
        task.duration_ms = int((time.monotonic() - t0) * 1000)
        task.updated_at = utcnow()
        nxt = NEXT.get(task.stage)
        if nxt:
            enqueue(db, run, nxt, out or {}, max_attempts=settings.task_max_attempts)  # type: ignore[arg-type]
            run.state, run.status = nxt, "running"  # type: ignore[union-attr]
        elif task.stage == "reconcile" or task.stage == "reextract":
            pending = db.scalar(select(WorkflowTask).where(WorkflowTask.run_id == run.id, WorkflowTask.id != task.id,  # type: ignore[union-attr]
                                                           WorkflowTask.status.in_(["queued", "running"])))
            if pending is None:
                run.state, run.status, run.finished_at = "completed", "completed", utcnow()  # type: ignore[union-attr]
                dv.processing_status = "ready_for_review"  # type: ignore[union-attr]
        metric(db, run.workspace_id, "stage.duration_ms", task.duration_ms, stage=task.stage, mode=run.agent_mode)  # type: ignore[union-attr]
        db.commit()
        return "succeeded"
    except Blocked as b:
        # keep the handler's side effects (answers applied so far) and park the task
        task.status, task.last_error, task.updated_at = "blocked", str(b), utcnow()
        run.status, run.state = "awaiting_input", task.stage  # type: ignore[union-attr]
        dv.processing_status = "awaiting_confirmation"  # type: ignore[union-attr]
        db.commit()
        return "blocked"
    except Halt as h:
        # keep the handler's durable side effects (doc-level exceptions) and finish the run
        task.status, task.last_error, task.updated_at = "succeeded", f"halted: {h}", utcnow()
        run.status, run.state, run.finished_at, run.error = "completed", "halted", utcnow(), str(h)  # type: ignore[union-attr]
        dv.processing_status = {"duplicate upload": "duplicate", "unsupported entity": "unsupported"}.get(str(h), "no_statements")  # type: ignore[union-attr]
        db.commit()
        return "halted"
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        with session_factory() as s2:
            task = s2.get(WorkflowTask, task_id)
            run = s2.get(WorkflowRun, task.run_id)
            dv = s2.get(DocumentVersion, run.document_version_id)
            msg = f"{type(exc).__name__}: {exc}"[:1000]
            task.last_error, task.updated_at = msg, utcnow()
            from spreadlens.models import AgentExecution
            s2.add(AgentExecution(workspace_id=run.workspace_id, run_id=run.id, task_id=task.id, agent=f"stage:{task.stage}",
                                  mode=run.agent_mode, status="failed", error=msg, retries=task.attempts - 1))
            if task.attempts >= task.max_attempts:
                task.status = "failed"
                has_output = s2.scalar(select(Statement).where(Statement.document_version_id == dv.id)) is not None
                run.status = "partial" if has_output and task.stage in ("map", "normalize", "reconcile", "reextract") else "failed"
                run.error = f"stage {task.stage} failed: {msg}"
                dv.processing_status = "failed" if run.status == "failed" else "partial"
                metric(s2, run.workspace_id, "stage.failure", 1, stage=task.stage)
            else:
                task.status = "queued"
                task.available_at = utcnow() + timedelta(seconds=min(30, 2 ** task.attempts))
                metric(s2, run.workspace_id, "stage.retry", 1, stage=task.stage)
            s2.commit()
        return "failed"
    finally:
        db.close()


def retry_failed_stage(db: Session, run: WorkflowRun, user_id: str) -> WorkflowTask:
    """Safe retry of a failed stage: same run, same inputs (a retry, not a new document revision)."""
    task = db.scalar(select(WorkflowTask).where(WorkflowTask.run_id == run.id, WorkflowTask.status == "failed")
                     .order_by(WorkflowTask.created_at.desc()))
    if task is None:
        raise ValueError("no failed stage")
    task.status, task.attempts, task.available_at, task.last_error = "queued", 0, None, None
    run.status, run.error = "running", None
    audit(db, run.workspace_id, user_id, "workflow.retry_stage", "run", run.id, details={"stage": task.stage})
    return task


def resume_gate(db: Session, run: WorkflowRun) -> None:
    task = db.scalar(select(WorkflowTask).where(WorkflowTask.run_id == run.id, WorkflowTask.stage == "await_metadata"))
    if task is not None and task.status == "blocked":
        task.status, task.attempts = "queued", 0
        run.status = "running"
