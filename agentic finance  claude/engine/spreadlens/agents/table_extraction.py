"""B. Table Extraction Agent.

Why it exists: turns located statements into rows and cells that keep their exact source text,
page/bounding box (or worksheet/cell) and extraction method, so every later figure can be traced.

AI vs code: extraction is ordinary code. The agent decides on targeted retries (e.g. re-OCR a
low-confidence page at higher resolution, bounded by budget). In live mode an eve agent may flag
layout problems (wrapped labels, merged rows) as row flags; it can never add or change a cell.
"""

from __future__ import annotations

import json

from pydantic import BaseModel

from spreadlens.agents.contracts import DocumentUnderstanding, TableExtractionSummary
from spreadlens.agents.runtime import AgentContext, ExecutionRecorder
from spreadlens.agents.tools import run_extraction
from spreadlens.config import PARSER_VERSION
from spreadlens.models import Artifact, DocumentVersion, ExtractedCell, ExtractedRow, NoteSection, Statement
from spreadlens.numeric.parse import UNREADABLE, ParseContext, parse_number
from spreadlens.security.sanitize import wrap_untrusted
from spreadlens.services.artifacts import save_artifact

NAME = "table_extraction"
RETRY_DPI = 220


class LayoutFlag(BaseModel):
    row_index: int
    issue: str


class LayoutReview(BaseModel):
    statement_key: str
    flags: list[LayoutFlag] = []


def _quality(raw: dict) -> tuple[int, int]:
    unreadable = low = 0
    for st in raw.get("statements", []):
        for r in st.get("rows", []):
            if "low_ocr_confidence" in r.get("flags", []):
                low += 1
            for c in r.get("cells", []):
                if parse_number(c["raw_text"]).state == UNREADABLE:
                    unreadable += 1
    return unreadable, low


def _low_conf_pages(raw: dict) -> list[int]:
    pages = set()
    for st in raw.get("statements", []):
        for r in st.get("rows", []):
            if "low_ocr_confidence" in r.get("flags", []) and r.get("page"):
                pages.add(r["page"])
    return sorted(pages)


def persist(ctx: AgentContext, dv: DocumentVersion, raw: dict, du: DocumentUnderstanding) -> list[dict]:
    pctx = ParseContext(dash_means_zero=du.dash_means_zero)
    loc = {s.key: s for s in du.statements}
    out = []
    for st in raw.get("statements", []):
        meta = loc.get(st["key"])
        cols = [c.model_dump() for c in meta.columns] if meta else []
        stmt = Statement(workspace_id=ctx.workspace_id, document_version_id=dv.id, statement_type=st["statement_type"],
                         scope=meta.scope if meta else st.get("scope"), title=st["title"],
                         currency=meta.currency if meta else st.get("currency"),
                         scale=meta.scale if meta else st.get("scale"), framework=du.framework,
                         pages=st.get("pages") or [], sheet=st.get("sheet"), columns=cols,
                         extraction_method=st["method"], parser_version=PARSER_VERSION,
                         status="extracted" if st.get("rows") else "no_rows")
        ctx.db.add(stmt)
        ctx.db.flush()
        row_ids: dict[int, str] = {}
        rows: list[ExtractedRow] = []
        n_cells = n_unreadable = n_low = 0
        for r in st.get("rows", []):
            row = ExtractedRow(workspace_id=ctx.workspace_id, statement_id=stmt.id, row_index=r["row_index"], label=r["label"],
                               section_path=r.get("section_path", []), level=r.get("level", 0), is_header=r.get("is_header", False),
                               is_total=r.get("is_total", False), note_ref=r.get("note_ref"), unit_type=r.get("unit_type", "monetary"),
                               page=r.get("page"), bbox=r.get("bbox"), flags=r.get("flags", []))
            ctx.db.add(row)
            rows.append(row)
            ctx.db.flush()
            row_ids[r["row_index"]] = row.id
            if "low_ocr_confidence" in row.flags:
                n_low += 1
            for c in r.get("cells", []):
                p = parse_number(c["raw_text"], pctx)
                decimals = p.decimals
                if c.get("number_format_decimals") is not None and p.has_number:
                    decimals = c["number_format_decimals"]
                ctx.db.add(ExtractedCell(workspace_id=ctx.workspace_id, statement_id=stmt.id, row_id=row.id,
                                         column_index=c["column_index"], raw_text=c["raw_text"], value_state=p.state,
                                         parsed_value=p.value, decimals=decimals, parse_notes=p.notes, page=c.get("page"),
                                         bbox=c.get("bbox"), sheet=c.get("sheet"), cell_ref=c.get("cell_ref"),
                                         extraction_method=st["method"], ocr_confidence=c.get("ocr_confidence")))
                n_cells += 1
                n_unreadable += p.state == UNREADABLE
        for r, row in zip(st.get("rows", []), rows):
            if r.get("parent_total_index") is not None:
                row.parent_total_row_id = row_ids.get(r["parent_total_index"])
        out.append({"key": st["key"], "statement_id": stmt.id, "rows": len(rows), "cells": n_cells,
                    "unreadable": n_unreadable, "low_confidence_rows": n_low})
    for n in raw.get("notes", []):
        ctx.db.add(NoteSection(workspace_id=ctx.workspace_id, document_version_id=dv.id, note_ref=n["note_ref"],
                               title=n["title"], text=n["text"][:20000], page=n.get("page"), sheet=n.get("sheet"), scope=n.get("scope")))
    ctx.db.flush()
    return out


def run(ctx: AgentContext, dv: DocumentVersion, du: DocumentUnderstanding, raw_art: Artifact) -> tuple[TableExtractionSummary, Artifact]:
    rec = ExecutionRecorder(ctx, NAME)
    rec.input_artifact_ids.append(raw_art.id)
    try:
        raw, chosen, retried = raw_art.payload, raw_art, []
        low_pages = _low_conf_pages(raw)
        ocr_used = (ctx.run.usage or {}).get("ocr_pages", 0) if ctx.run else 0
        if low_pages and ctx.settings.ocr_max_retries > 0 and ocr_used + len(low_pages) <= ctx.settings.budget_max_ocr_pages:
            retry_art, _ = rec.tool("reocr_pages", run_extraction, ctx, dv, low_pages, RETRY_DPI)
            if _quality(retry_art.payload) < _quality(raw):
                chosen, raw = retry_art, retry_art.payload
            retried = low_pages
        warnings = list(raw.get("warnings", []))
        if ctx.mode == "live":
            for st in raw.get("statements", []):
                suspicious = [r for r in st.get("rows", []) if set(r.get("flags", [])) & {"values_without_label", "multiple_values_in_column", "low_ocr_confidence", "label_wrapped"}]
                if not suspicious:
                    continue
                msg = ("Review these extracted rows for layout problems (wrapped labels, merged or split rows, values in the wrong "
                       "column). Report issues only; do not supply or change any value.\n"
                       + wrap_untrusted(json.dumps([{"row_index": r["row_index"], "label": r["label"],
                                                     "cells": [c["raw_text"] for c in r.get("cells", [])]} for r in suspicious])[:12000]))
                review = rec.live(msg, LayoutReview, {"statement_key": st["key"]})
                valid = {r["row_index"] for r in suspicious}
                for f in review.flags:
                    if f.row_index in valid:
                        row = next(r for r in st["rows"] if r["row_index"] == f.row_index)
                        row.setdefault("flags", []).append(f"layout_review:{f.issue[:120]}")
        stats = rec.tool("persist_rows_and_cells", persist, ctx, dv, raw, du)
        summary = TableExtractionSummary(extraction_artifact_id=chosen.id, statements=stats, retried_pages=retried,
                                         cache_hit=chosen.id == raw_art.id and bool(raw_art.payload.get("_cached")),
                                         method=raw.get("method_summary", ""), warnings=warnings)
        art = save_artifact(ctx.db, ctx.workspace_id, ctx.run_id, summary, NAME)
        rec.finish("succeeded", art.id)
        return summary, art
    except Exception as exc:
        rec.finish("failed", error=f"{type(exc).__name__}: {exc}"[:500])
        raise
