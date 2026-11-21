"""Extraction tools used by the Document Understanding and Table Extraction agents.

These are deterministic tools. The agents decide *which* tool to run on *which* pages
(e.g. OCR for scanned pages, a higher-DPI retry for a low-confidence page); the tools never
invent a cell that is not in the source.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from spreadlens.config import Settings
from spreadlens.extraction.layout import parse_pages
from spreadlens.extraction.notes import extract_notes
from spreadlens.extraction.ocr import OcrUnavailable, get_ocr_provider
from spreadlens.extraction.pdf_text import is_scanned, read_pdf_pages
from spreadlens.extraction.types import ExtractionResult, PageText
from spreadlens.extraction.xlsx import read_xlsx


@dataclass
class PageInventory:
    pages: list[PageText]
    scanned: list[int]
    ocr_used: bool
    ocr_provider: str | None
    warnings: list[str]


def inventory_pdf(data: bytes, settings: Settings, ocr_dpi: int | None = None, force_ocr_pages: list[int] | None = None) -> PageInventory:
    """Read the text layer; OCR pages that have none (in parallel, bounded)."""
    pages = read_pdf_pages(data, settings.max_pdf_pages)
    scanned = [p.page for p in pages if is_scanned(p)]
    targets = sorted(set(scanned) | set(force_ocr_pages or []))
    warnings: list[str] = []
    provider_name = None
    if targets:
        if len(targets) > settings.budget_max_ocr_pages:
            warnings.append(f"OCR budget allows {settings.budget_max_ocr_pages} pages; {len(targets)} needed. Extra pages skipped.")
            targets = targets[: settings.budget_max_ocr_pages]
        try:
            provider = get_ocr_provider(settings.ocr_provider)
            provider_name = provider.name
            chunks = [targets[i::max(1, min(settings.worker_concurrency, len(targets)))] for i in range(max(1, min(settings.worker_concurrency, len(targets))))]
            dpi = ocr_dpi or settings.ocr_dpi
            with ThreadPoolExecutor(max_workers=len(chunks)) as pool:
                results = list(pool.map(lambda ch: provider.recognise(data, ch, dpi), [c for c in chunks if c]))
            ocr_pages = {p.page: p for chunk in results for p in chunk}
            pages = [ocr_pages.get(p.page, p) for p in pages]
        except OcrUnavailable as exc:
            warnings.append(str(exc))
    return PageInventory(pages=pages, scanned=scanned, ocr_used=bool(targets) and provider_name is not None,
                         ocr_provider=provider_name, warnings=warnings)


def extract_tables_pdf(inv: PageInventory, settings: Settings) -> ExtractionResult:
    statements, note_pages = parse_pages(inv.pages, low_conf=settings.ocr_low_confidence)
    notes = extract_notes(inv.pages, note_pages)
    methods = sorted({p.method for p in inv.pages})
    return ExtractionResult(
        statements=statements, notes=notes,
        pages=[{"page": p.page, "method": p.method, "words": len(p.words), "ocr_conf": p.ocr_conf,
                "scanned": p.page in inv.scanned, "width": p.width, "height": p.height} for p in inv.pages],
        method_summary="+".join(methods), warnings=list(inv.warnings),
    )


def extract_tables_xlsx(data: bytes) -> ExtractionResult:
    statements, notes, pages, warnings = read_xlsx(data)
    return ExtractionResult(statements=statements, notes=notes, pages=pages, method_summary="xlsx_cells", warnings=warnings)
