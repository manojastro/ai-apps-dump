"""OCR provider adapter. Local default: RapidOCR (ONNX Runtime, runs on this machine, no network).

A managed OCR provider can be added by implementing `OcrProvider.recognise`. Processing records
which provider ran, so the UI can say whether content left the machine.
"""

from __future__ import annotations

import io
import threading
import unicodedata
from functools import lru_cache
from typing import Protocol

from spreadlens.extraction.types import PageText, Word


class OcrUnavailable(RuntimeError):
    pass


class OcrProvider(Protocol):
    name: str
    is_external: bool

    def recognise(self, data: bytes, page_numbers: list[int], dpi: int) -> list[PageText]: ...


_PDFIUM_LOCK = threading.Lock()  # pdfium is not thread-safe; OCR inference itself runs in parallel


def _render(data: bytes, page_numbers: list[int], dpi: int):
    import pypdfium2 as pdfium

    rendered = []
    with _PDFIUM_LOCK:
        pdf = pdfium.PdfDocument(io.BytesIO(data))
        try:
            for n in page_numbers:
                page = pdf[n - 1]
                w_pt, h_pt = page.get_size()
                rendered.append((n, w_pt, h_pt, page.render(scale=dpi / 72.0).to_pil()))
        finally:
            pdf.close()
    yield from rendered


def _split_segment(text: str, x0: float, x1: float, top: float, bottom: float, page: int, conf: float) -> list[Word]:
    """OCR returns phrases; split into word tokens with x positions proportional to characters."""
    tokens = text.split()
    if len(tokens) <= 1:
        return [Word(text.strip(), x0, top, x1, bottom, page, conf)]
    total = len(text)
    out, pos = [], 0
    for tok in tokens:
        start = text.find(tok, pos)
        end = start + len(tok)
        pos = end
        out.append(Word(tok, x0 + (x1 - x0) * start / total, top, x0 + (x1 - x0) * end / total, bottom, page, conf))
    return out


class LocalRapidOcr:
    name = "rapidocr-onnxruntime (local)"
    is_external = False

    def __init__(self) -> None:
        try:
            from rapidocr_onnxruntime import RapidOCR  # noqa: F401
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise OcrUnavailable("Install the 'ocr' extra: uv sync --extra ocr") from exc

    @staticmethod
    @lru_cache(maxsize=1)
    def _engine():
        from rapidocr_onnxruntime import RapidOCR

        return RapidOCR()

    def recognise(self, data: bytes, page_numbers: list[int], dpi: int) -> list[PageText]:
        import numpy as np

        engine = self._engine()
        pages = []
        for n, w_pt, h_pt, img in _render(data, page_numbers, dpi):
            scale = 72.0 / dpi
            result, _ = engine(np.array(img.convert("RGB")), return_word_box=True, use_cls=False)
            words: list[Word] = []
            confs = []
            for item in result or []:
                box, text, score = item[0], unicodedata.normalize("NFKC", str(item[1])), float(item[2])
                confs.append(score)
                char_boxes = item[3] if len(item) > 3 else None
                chars = item[4] if len(item) > 4 else None
                char_scores = item[5] if len(item) > 5 else None
                if char_boxes and chars and len(char_boxes) == len(chars):
                    words.extend(_words_from_chars(char_boxes, chars, char_scores, n, scale))
                else:
                    xs = [p[0] for p in box]
                    ys = [p[1] for p in box]
                    words.extend(_split_segment(text, min(xs) * scale, max(xs) * scale, min(ys) * scale,
                                                max(ys) * scale, n, score))
            pages.append(PageText(page=n, width=w_pt, height=h_pt, words=words, method="ocr_local",
                                  ocr_conf=(sum(confs) / len(confs)) if confs else None))
        return pages


def _words_from_chars(char_boxes, chars, char_scores, page: int, scale: float) -> list[Word]:
    """Build word tokens from per-character boxes.

    Numeric segments stay whole (each figure is its own OCR segment). Alphabetic text is split by
    dictionary segmentation because the recognition model does not emit spaces; characters are
    never changed, only the spacing."""
    from spreadlens.extraction.ocr_words import split_spaceless
    from spreadlens.numeric.parse import looks_numeric

    text = "".join(unicodedata.normalize("NFKC", str(c)) for c in chars)
    boxes = [(min(p[0] for p in b), max(p[0] for p in b), min(p[1] for p in b), max(p[1] for p in b)) for b in char_boxes]
    if len(text) != len(boxes):
        return [Word(text, min(b[0] for b in boxes) * scale, min(b[2] for b in boxes) * scale,
                     max(b[1] for b in boxes) * scale, max(b[3] for b in boxes) * scale, page,
                     min(float(x) for x in char_scores) if char_scores else None)]
    if looks_numeric(text.replace(" ", "")):
        spans = [(0, len(text))]
    else:
        spans = []
        pos = 0
        for part in text.split(" "):
            if part:
                spans.extend((pos + a, pos + b) for a, b in split_spaceless(part))
            pos += len(part) + 1
    out = []
    for a, b in spans:
        idx = [i for i in range(a, b) if text[i] != " "]
        if not idx:
            continue
        w = text[a:b].strip()
        conf = min(float(char_scores[i]) for i in idx) if char_scores else None
        out.append(Word(w, min(boxes[i][0] for i in idx) * scale, min(boxes[i][2] for i in idx) * scale,
                        max(boxes[i][1] for i in idx) * scale, max(boxes[i][3] for i in idx) * scale, page, conf))
    return out


class NoOcr:
    name = "none"
    is_external = False

    def recognise(self, data: bytes, page_numbers: list[int], dpi: int) -> list[PageText]:
        raise OcrUnavailable("OCR is disabled (SPREADLENS_OCR_PROVIDER=none); scanned pages cannot be read.")


def get_ocr_provider(name: str) -> OcrProvider:
    if name == "local":
        return LocalRapidOcr()
    return NoOcr()
