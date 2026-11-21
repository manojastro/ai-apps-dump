"""Read-only tool endpoints that eve agent tools call back into.

Two checks: the service bearer token (the caller is our agent runtime) AND a signed scope token
(X-SpreadLens-Scope) that names the workspace. The workspace is taken from the signature, never from
model-supplied input. No endpoint here writes data: agents propose; the coordinator persists.
"""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from spreadlens.api.deps import J
from spreadlens.db import get_db
from spreadlens.models import Artifact, CalculationResult, ExtractedCell, ExtractedRow, NoteSection, Statement
from spreadlens.numeric.decimal_utils import dstr
from spreadlens.security.auth import require_service_token
from spreadlens.security.scope import scope_dependency
from spreadlens.taxonomy.loader import load_taxonomy

router = APIRouter(prefix="/internal/tools", tags=["agent-tools"], dependencies=[Depends(require_service_token)])


@router.get("/taxonomy/{statement_type}")
def taxonomy(statement_type: str):
    items = load_taxonomy().for_statement(statement_type)
    return J([{"code": i.code, "label": i.label, "section": i.section, "is_total": i.total, "unit": i.unit} for i in items])


@router.get("/rows/{row_id}")
def row_context(row_id: str, scope: dict = Depends(scope_dependency), db: Session = Depends(get_db)):
    r = db.get(ExtractedRow, row_id)
    if r is None or r.workspace_id != scope["ws"]:
        raise HTTPException(404, "Not found")
    st = db.get(Statement, r.statement_id)
    neighbours = list(db.scalars(select(ExtractedRow).where(ExtractedRow.statement_id == r.statement_id,
                                                            ExtractedRow.row_index.between(r.row_index - 3, r.row_index + 3))
                                 .order_by(ExtractedRow.row_index)))
    cells = list(db.scalars(select(ExtractedCell).where(ExtractedCell.row_id == r.id)))
    return J({"statement_type": st.statement_type if st else None, "label": r.label, "section_path": r.section_path,
              "is_total": r.is_total, "note_ref": r.note_ref, "document_version_id": st.document_version_id if st else None,
              "cells": [{"column": c.column_index, "raw_text": c.raw_text, "state": c.value_state} for c in cells],
              "neighbours": [{"row_index": n.row_index, "label": n.label, "is_total": n.is_total} for n in neighbours]})


@router.get("/notes/{document_version_id}/{note_ref}")
def note(document_version_id: str, note_ref: str, scope: dict = Depends(scope_dependency), db: Session = Depends(get_db)):
    n = db.scalar(select(NoteSection).where(NoteSection.document_version_id == document_version_id, NoteSection.note_ref == note_ref,
                                            NoteSection.workspace_id == scope["ws"]))
    if n is None:
        raise HTTPException(404, "Not found")
    return J({"ref": n.note_ref, "title": n.title, "text": n.text[:4000]})


@router.get("/calculations/{calc_id}")
def calculation(calc_id: str, scope: dict = Depends(scope_dependency), db: Session = Depends(get_db)):
    c = db.get(CalculationResult, calc_id)
    if c is None or c.workspace_id != scope["ws"]:
        raise HTTPException(404, "Not found")
    return J({"rule_id": c.rule_id, "title": c.title, "expression": c.expression, "expected": dstr(c.expected),
              "observed": dstr(c.observed), "difference": dstr(c.difference), "tolerance": dstr(c.tolerance),
              "status": c.status, "inputs": c.input_observation_ids, "explanation": c.explanation})


class QuoteIn(BaseModel):
    document_version_id: str
    quote: str


@router.post("/quotes/check")
def check_quote(body: QuoteIn, scope: dict = Depends(scope_dependency), db: Session = Depends(get_db)):
    """Lets the Document Understanding agent verify that an evidence quote really occurs in the document."""
    art = db.scalar(select(Artifact).where(Artifact.workspace_id == scope["ws"], Artifact.artifact_type == "raw_extraction",
                                           Artifact.run_id == scope.get("run")).order_by(Artifact.created_at.desc()))
    if art is None:
        raise HTTPException(404, "Not found")
    norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()  # noqa: E731
    text = norm("\n".join(p.get("text", "") for p in art.payload.get("page_texts", [])))
    q = norm(body.quote)
    return J({"found": bool(q) and q in text})
