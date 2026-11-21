"""Digital PDF text with word coordinates (pdfplumber), plus scanned-page detection."""

from __future__ import annotations

import io

import pdfplumber

from spreadlens.extraction.types import PageText, Word

MIN_WORDS_FOR_TEXT_LAYER = 8


def read_pdf_pages(data: bytes, max_pages: int) -> list[PageText]:
    out: list[PageText] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for i, page in enumerate(pdf.pages[:max_pages], start=1):
            words = page.extract_words(x_tolerance=1.5, y_tolerance=2, keep_blank_chars=False, use_text_flow=False)
            out.append(PageText(
                page=i, width=float(page.width), height=float(page.height),
                words=[Word(text=w["text"], x0=float(w["x0"]), top=float(w["top"]), x1=float(w["x1"]),
                            bottom=float(w["bottom"]), page=i) for w in words],
                method="pdf_text",
            ))
    return out


def is_scanned(page: PageText) -> bool:
    return len(page.words) < MIN_WORDS_FOR_TEXT_LAYER
