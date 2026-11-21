"""Deterministic tools the agents call. Idempotent: same inputs -> same artifact (cached)."""

from __future__ import annotations

from sqlalchemy import select

from spreadlens.agents.runtime import AgentContext, digest
from spreadlens.config import PARSER_VERSION
from spreadlens.extraction.pipeline import extract_tables_pdf, extract_tables_xlsx, inventory_pdf
from spreadlens.extraction.types import group_lines
from spreadlens.models import Artifact, DocumentVersion, ExtractionCache
from spreadlens.services.artifacts import save_raw_artifact
from spreadlens.services.audit import metric
from spreadlens.storage.base import get_storage


def extraction_config_hash(ctx: AgentContext, force_ocr_pages: list[int] | None, dpi: int | None) -> str:
    return digest({"ocr": ctx.settings.ocr_provider, "dpi": dpi or ctx.settings.ocr_dpi,
                   "force": sorted(force_ocr_pages or []), "lowconf": ctx.settings.ocr_low_confidence})


def run_extraction(ctx: AgentContext, dv: DocumentVersion, force_ocr_pages: list[int] | None = None,
                   dpi: int | None = None) -> tuple[Artifact, bool]:
    """Read the document and return the raw extraction artifact. Cached by (sha256, parser, config)."""
    cfg = extraction_config_hash(ctx, force_ocr_pages, dpi)
    hit = ctx.db.scalar(select(ExtractionCache).where(ExtractionCache.workspace_id == ctx.workspace_id,
                                                      ExtractionCache.sha256 == dv.sha256,
                                                      ExtractionCache.parser_version == PARSER_VERSION,
                                                      ExtractionCache.config_hash == cfg))
    if hit:
        art = ctx.db.get(Artifact, hit.artifact_id)
        if art is not None:
            metric(ctx.db, ctx.workspace_id, "extraction.cache_hit", 1, document_version_id=dv.id)
            return art, True
    data = get_storage(ctx.settings).get(dv.storage_key)
    if dv.file_kind == "xlsx":
        res = extract_tables_xlsx(data)
        page_texts = []
        for st in res.statements:
            page_texts.append({"sheet": st.sheet, "text": "\n".join(f.split(":", 1)[1] for f in st.flags if f.startswith("title_context:"))
                               + "\n" + "\n".join(r.label for r in st.rows)})
        for n in res.notes:
            page_texts.append({"sheet": n.sheet, "text": f"{n.note_ref}. {n.title}\n{n.text}"})
        ocr_pages = 0
    else:
        inv = inventory_pdf(data, ctx.settings, ocr_dpi=dpi, force_ocr_pages=force_ocr_pages)
        res = extract_tables_pdf(inv, ctx.settings)
        page_texts = [{"page": p.page, "method": p.method,
                       "text": "\n".join(" ".join(w.text for w in line) for line in group_lines(p.words))} for p in inv.pages]
        ocr_pages = sum(1 for p in inv.pages if p.method != "pdf_text")
        if ctx.run is not None and ocr_pages:
            u = dict(ctx.run.usage or {})
            u["ocr_pages"] = u.get("ocr_pages", 0) + ocr_pages
            ctx.run.usage = u
        if inv.ocr_provider:
            res.warnings.append(f"OCR provider: {inv.ocr_provider} (runs locally; no document data leaves this machine)")
    payload = res.to_dict()
    payload["page_texts"] = page_texts
    payload["parser_version"] = PARSER_VERSION
    payload["config_hash"] = cfg
    art = save_raw_artifact(ctx.db, ctx.workspace_id, ctx.run_id, "raw_extraction", payload, "tool:extract_document")
    ctx.db.add(ExtractionCache(workspace_id=ctx.workspace_id, sha256=dv.sha256, parser_version=PARSER_VERSION, config_hash=cfg, artifact_id=art.id))
    metric(ctx.db, ctx.workspace_id, "extraction.ocr_pages", ocr_pages, document_version_id=dv.id)
    return art, False
