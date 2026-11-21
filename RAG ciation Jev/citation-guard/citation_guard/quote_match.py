"""Check A: deterministic quote matching (no model), plus the passage window for Check B.

Both the quote and the document go through the same normalisation: Unicode NFKC,
curly->straight quotes, all dash variants -> "-", whitespace runs -> one space.
Matching is an exact, case-sensitive substring search on the normalised text.
rapidfuzz is used only to log the closest near-match for debugging; it never makes a
quote count as found.
"""

from __future__ import annotations

import re
import unicodedata
from enum import Enum
from functools import lru_cache

from pydantic import BaseModel
from rapidfuzz import fuzz

from .ingest import LOW_PRIORITY_SECTIONS, Document, Section

QUOTE_CHARS = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'", "′": "'", "`": "'",
    "´": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"', "″": '"',
    "«": '"', "»": '"',
}
DASH_CHARS = {c: "-" for c in "‐‑‒–—―−﹘﹣－"}
CHAR_MAP = {**QUOTE_CHARS, **DASH_CHARS}


class QuoteStatus(str, Enum):
    FOUND_IN_CITED_SECTION = "FOUND_IN_CITED_SECTION"
    FOUND_ELSEWHERE = "FOUND_ELSEWHERE"
    NOT_FOUND = "NOT_FOUND"
    QUOTE_TOO_SHORT = "QUOTE_TOO_SHORT"


class QuoteMatch(BaseModel):
    status: QuoteStatus
    start: int | None = None  # offset in the cleaned document
    end: int | None = None
    found_section_id: str | None = None
    occurrences: int = 0
    normalized_length: int = 0
    closest_fuzzy_score: float | None = None  # debug only, set when NOT_FOUND

    @property
    def found(self) -> bool:
        return self.start is not None


class Passage(BaseModel):
    text: str
    start: int
    end: int
    section_id: str | None


def normalize(text: str) -> tuple[str, list[int]]:
    """Normalise text and return (normalised, index_map).

    index_map[i] is the index in `text` of the character that produced normalised char i,
    with one extra trailing entry equal to len(text) so end offsets map cleanly.
    """
    out: list[str] = []
    idx: list[int] = []
    pending_space = False
    for i, ch in enumerate(text):
        ch = CHAR_MAP.get(ch, ch)
        for c in unicodedata.normalize("NFKC", ch):
            c = CHAR_MAP.get(c, c)
            if c.isspace():
                pending_space = bool(out)
                continue
            if pending_space:
                out.append(" ")
                idx.append(i)
                pending_space = False
            out.append(c)
            idx.append(i)
    idx.append(len(text))
    return "".join(out), idx


def normalize_text(text: str) -> str:
    return normalize(text)[0]


@lru_cache(maxsize=32)
def _normalized_doc(doc_id: str, clean_text: str) -> tuple[str, tuple[int, ...]]:
    norm, idx = normalize(clean_text)
    return norm, tuple(idx)


def _find_all(hay: str, needle: str) -> list[int]:
    hits, start = [], 0
    while True:
        k = hay.find(needle, start)
        if k < 0:
            return hits
        hits.append(k)
        start = k + 1


def match_quote(doc: Document, quote: str, section_id: str | None, min_chars: int = 20) -> QuoteMatch:
    q = normalize_text(quote)
    norm, idx = _normalized_doc(doc.doc_id, doc.clean_text)
    hits = _find_all(norm, q) if q else []

    if not hits:
        score = None
        if q:
            score = round(fuzz.partial_ratio(q, norm), 1)
        return QuoteMatch(status=QuoteStatus.NOT_FOUND, normalized_length=len(q), closest_fuzzy_score=score)

    # Map normalised hits back to cleaned-document offsets.
    spans = [(idx[h], idx[h + len(q) - 1] + 1) for h in hits]
    cited = doc.section(section_id) if section_id else None

    def in_section(span: tuple[int, int], sec: Section) -> bool:
        return sec.start <= span[0] and span[1] <= sec.end

    chosen = None
    status = QuoteStatus.FOUND_ELSEWHERE
    if cited is not None:
        for sp in spans:
            if in_section(sp, cited):
                chosen, status = sp, QuoteStatus.FOUND_IN_CITED_SECTION
                break
    if chosen is None:
        # Prefer a hit outside low-priority sections such as the table of contents.
        ranked = sorted(spans, key=lambda sp: (getattr(doc.section_at(sp[0]), "section_id", "") in LOW_PRIORITY_SECTIONS, sp[0]))
        chosen = ranked[0]
    found_sec = doc.section_at(chosen[0])
    if len(q) < min_chars:
        status = QuoteStatus.QUOTE_TOO_SHORT
    return QuoteMatch(
        status=status,
        start=chosen[0],
        end=chosen[1],
        found_section_id=found_sec.section_id if found_sec else None,
        occurrences=len(spans),
        normalized_length=len(q),
    )


# --------------------------------------------------------------------------- passage window

# A sentence ends with . ! or ? (optionally followed by a closing quote/bracket) and whitespace.
SENTENCE_END_RE = re.compile(r"[.!?][\"')\]]?(?=\s)")


def passage_window(doc: Document, start: int, end: int, window: int = 1500) -> Passage:
    """About `window` chars on each side of [start, end), snapped to sentence boundaries,
    clipped to the section that contains the match."""
    text = doc.clean_text
    sec = doc.section_at(start)
    sec_start, sec_end = (sec.start, sec.end) if sec else (0, len(text))
    lo = max(sec_start, start - window)
    hi = min(sec_end, end + window)

    # Snap the left edge forward to the start of the next sentence (never past the quote).
    if lo > sec_start:
        region = text[lo:start]
        m = SENTENCE_END_RE.search(region)
        if m:
            k = lo + m.end()
            while k < start and text[k].isspace():
                k += 1
            lo = k
    # Snap the right edge back to the end of the last full sentence (never before the quote).
    if hi < sec_end:
        region = text[end:hi]
        ends = [m.end() for m in SENTENCE_END_RE.finditer(region)]
        if ends:
            hi = end + ends[-1]
    return Passage(text=text[lo:hi].strip(), start=lo, end=hi, section_id=sec.section_id if sec else None)


def offsets_for_log(doc: Document, m: QuoteMatch) -> dict | None:
    if not m.found:
        return None
    return {
        "start": m.start,
        "end": m.end,
        "section_id": m.found_section_id,
        "raw_line": doc.raw_line_at(m.start),  # 1-based line in the raw download
    }
