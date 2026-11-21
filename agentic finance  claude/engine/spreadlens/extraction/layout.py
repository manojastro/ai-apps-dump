"""Turn positioned words (digital PDF text or OCR) into statement tables.

Algorithm (ordinary code, no AI):
 1. group words into lines by vertical position;
 2. find statement titles, scope and unit declarations;
 3. find the column header line (period labels) and record each column's right edge;
 4. for each line, peel numeric tokens from the right and assign them to the nearest column by
    right-edge distance; what remains on the left is the row label; a small integer under the
    'Note' header is a note reference;
 5. a statement continues on the next page when that page has no new title but the same columns
    (or says "continued");
 6. stop at signature blocks / notes.
Every cell keeps its page and bounding box so the UI can highlight the exact source.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from spreadlens.extraction.classify import (
    NOTES_TITLE,
    STOP_MARKERS,
    classify_title,
    detect_scope,
    is_subtotal_like,
    unit_type_for,
)
from spreadlens.extraction.hierarchy import assign_hierarchy
from spreadlens.extraction.periods import PERIOD_PATTERNS, YEAR
from spreadlens.extraction.types import PageText, RawCell, RawColumn, RawRow, RawStatement, Word, group_lines
from spreadlens.numeric.parse import looks_numeric
from spreadlens.numeric.scale import detect_currency, detect_scale

NOTE_REF = re.compile(r"^\d{1,2}(\.\d{1,2})?[a-z]?$")
COLUMN_TOLERANCE = 45.0  # points between a value's right edge and its column's right edge


@dataclass
class _Header:
    columns: list[RawColumn]
    note_x: tuple[float, float] | None
    line_top: float
    page: int


def _line_text(line: list[Word]) -> str:
    return " ".join(w.text for w in line)


def _find_header(lines: list[list[Word]], page: int) -> tuple[int, _Header] | None:
    for li, line in enumerate(lines[:40]):
        text = _line_text(line)
        # character offsets of each word in the joined text
        offsets, pos = [], 0
        for w in line:
            offsets.append((pos, pos + len(w.text), w))
            pos += len(w.text) + 1
        spans = []
        for pat in PERIOD_PATTERNS:
            for m in pat.finditer(text):
                spans.append((m.start(), m.end()))
        if len(spans) < 2:
            # bare years: "2025  2024"
            years = [(m.start(), m.end()) for m in YEAR.finditer(text)]
            if len(years) >= 2 and len(text) < 80:
                spans = years
        # remove overlapping spans (keep longest)
        spans = sorted(set(spans), key=lambda s: (s[0], -(s[1] - s[0])))
        merged: list[tuple[int, int]] = []
        for s in spans:
            if merged and s[0] < merged[-1][1]:
                continue
            merged.append(s)
        if len(merged) < 2:
            continue
        cols = []
        for i, (a, b) in enumerate(merged):
            ws = [w for (s, e, w) in offsets if s < b and e > a]
            if not ws:
                continue
            raw = text[a:b]
            # include a trailing "(Restated)" marker in the header text
            tail = text[b:b + 14]
            if "restated" in tail.lower():
                raw += " (Restated)"
            cols.append(RawColumn(index=i, header_raw=raw, period_end=None, x1=max(w.x1 for w in ws)))
        # Restated markers can also sit on the next line under a column
        if li + 1 < len(lines):
            for w in lines[li + 1]:
                if "restated" in w.text.lower():
                    near = min(cols, key=lambda c: abs((c.x1 or 0) - w.x1))
                    if "restated" not in near.header_raw.lower():
                        near.header_raw += " (Restated)"
        note_x = None
        for w in line:
            if w.text.lower().strip(".") in ("note", "notes", "note no", "note no."):
                note_x = (w.x0 - 10, w.x1 + 10)
        if len(cols) >= 2:
            return li, _Header(cols, note_x, line[0].top, page)
    return None


def _parse_line(line: list[Word], header: _Header) -> tuple[str, list[RawCell], str | None, list[float], list[str]]:
    flags: list[str] = []
    values: list[tuple[int, Word]] = []
    note_ref = None
    words = list(line)
    # peel numeric tokens from the right
    rest: list[Word] = []
    i = len(words) - 1
    while i >= 0:
        w = words[i]
        tok = w.text.strip()
        if w.conf is not None and tok.endswith((".", ",")) and looks_numeric(tok.rstrip(".,")):
            # OCR noise: a stray trailing period/comma after a figure. Removed and flagged.
            tok = tok.rstrip(".,")
            w = Word(tok, w.x0, w.top, w.x1, w.bottom, w.page, w.conf)
            flags.append("ocr_trailing_punctuation_removed")
        is_num = looks_numeric(tok) or tok.lower() in ("n/a", "na", "nil")
        if not is_num and any(ch.isdigit() for ch in tok) and len(tok) <= 18 and " " not in tok:
            # garbled figure right-aligned under a value column: keep it as a cell (it will parse as unreadable)
            near = min(header.columns, key=lambda c: abs((c.x1 or 0) - w.x1))
            is_num = abs((near.x1 or 0) - w.x1) <= COLUMN_TOLERANCE / 3
        if is_num:
            if header.note_x and header.note_x[0] <= w.x0 <= header.note_x[1] and NOTE_REF.match(tok):
                note_ref = tok
                i -= 1
                continue
            col = min(header.columns, key=lambda c: abs((c.x1 or 0) - w.x1))
            if abs((col.x1 or 0) - w.x1) <= COLUMN_TOLERANCE:
                values.append((col.index, w))
                i -= 1
                continue
            # numeric token not under any column: part of the label (e.g. "Note 5" text, year in label)
        rest = words[: i + 1]
        break
    else:
        rest = []
    label_words = rest
    # a note ref written right after the label without a Note column header
    if not note_ref and label_words and NOTE_REF.match(label_words[-1].text) and header.note_x is None and len(label_words) > 1:
        gap = header.columns[0].x1 - 120 if header.columns[0].x1 else 0
        if label_words[-1].x0 > gap:
            note_ref = label_words[-1].text
            label_words = label_words[:-1]
    label = " ".join(w.text for w in label_words).strip()
    if label_words and label_words[0].conf is not None and label.endswith("."):
        label = label.rstrip(".")
        flags.append("ocr_trailing_punctuation_removed")
    seen: dict[int, RawCell] = {}
    for idx, w in values:
        if idx in seen:
            flags.append("multiple_values_in_column")
            seen[idx].raw_text = w.text + " " + seen[idx].raw_text  # keep raw; parser will mark unreadable
            continue
        seen[idx] = RawCell(column_index=idx, raw_text=w.text, page=w.page,
                            bbox=[round(w.x0, 2), round(w.top, 2), round(w.x1, 2), round(w.bottom, 2)],
                            ocr_confidence=w.conf)
    cells = [seen[k] for k in sorted(seen)]
    bbox = [min(w.x0 for w in line), min(w.top for w in line), max(w.x1 for w in line), max(w.bottom for w in line)]
    return label, cells, note_ref, [round(b, 2) for b in bbox], flags


def _column_signature(h: _Header) -> tuple[str, ...]:
    return tuple(re.sub(r"\s+", " ", c.header_raw.lower()) for c in h.columns)


def parse_pages(pages: list[PageText], low_conf: float = 0.8) -> tuple[list[RawStatement], list[int]]:
    """Return statements and the list of pages that look like notes."""
    statements: list[RawStatement] = []
    notes_pages: list[int] = []
    current: RawStatement | None = None
    current_header: _Header | None = None
    in_notes = False
    for pg in pages:
        lines = group_lines(pg.words)
        if not lines:
            continue
        top_text = "\n".join(_line_text(line) for line in lines[:8])
        kind = None
        title_line = None
        for line in lines[:8]:
            t = _line_text(line)
            k = classify_title(t)
            if k and len(t) < 140:
                kind, title_line = k, t
                break
        if NOTES_TITLE.search(top_text) and not kind:
            in_notes = True
        if in_notes and not kind:
            notes_pages.append(pg.page)
            current = None
            continue
        found = _find_header(lines, pg.page)
        continuing = (
            kind is None and current is not None and found is not None and current_header is not None
            and (_column_signature(found[1]) == _column_signature(current_header) or "continued" in top_text.lower())
        )
        if kind is None and not continuing:
            if current is not None and found is None:
                current = None
            continue
        in_notes = False
        if kind is not None and not (current and "continued" in (title_line or "").lower() and current.statement_type == kind):
            if found is None:
                statements.append(RawStatement(key=f"{kind}:p{pg.page}", statement_type=kind, title=title_line or kind,
                                               scope=detect_scope(top_text), method=pg.method, pages=[pg.page],
                                               flags=["no_period_header_found"]))
                current = None
                continue
            current = RawStatement(key=f"{kind}:p{pg.page}", statement_type=kind, title=title_line or kind,
                                   scope=detect_scope(top_text), method=pg.method, pages=[pg.page],
                                   columns=found[1].columns)
            sc = detect_scale(top_text + "\n" + "\n".join(_line_text(line) for line in lines[: found[0] + 1]))
            current.scale = sc.value
            current.scale_text = sc.evidence + ([f"conflict: {','.join(sc.conflicts)}"] if sc.conflicts else [])
            cur = detect_currency(top_text + "\n" + "\n".join(_line_text(line) for line in lines[: found[0] + 1]))
            current.currency = cur.value
            if sc.conflicts:
                current.flags.append("conflicting_units")
            current.flags.append(f"title_context:{top_text[:300]}")
            statements.append(current)
            current_header = found[1]
        else:
            assert current is not None
            current.pages.append(pg.page)
            if found is not None:
                current_header = found[1]
        assert current is not None and current_header is not None
        start = (found[0] + 1) if found else 0
        for line in lines[start:]:
            t = _line_text(line)
            if STOP_MARKERS.search(t):
                break
            if classify_title(t) and line[0].top > current_header.line_top + 5:
                break  # another statement begins on the same page (rare)
            label, cells, note_ref, bbox, flags = _parse_line(line, current_header)
            if re.search(r"restated", label, re.I) and not cells:
                continue
            if not label and not cells:
                continue
            if not label and cells:
                # values without a label: continuation of the previous label line (wrapped label)
                if current.rows and not current.rows[-1].cells:
                    prev = current.rows[-1]
                    prev.cells = cells
                    prev.is_header = False
                    prev.flags.append("label_wrapped")
                    continue
                flags.append("values_without_label")
            if current.rows and not cells and current.rows[-1].cells == [] and not current.rows[-1].is_header and line[0].x0 > current.rows[-1].bbox[0] + 2:  # type: ignore[index]
                current.rows[-1].label += " " + label
                continue
            if any(c.ocr_confidence is not None and c.ocr_confidence < low_conf for c in cells):
                flags.append("low_ocr_confidence")
            row = RawRow(row_index=len(current.rows), label=label, cells=cells, note_ref=note_ref, page=pg.page,
                         bbox=bbox, flags=flags, is_header=not cells,
                         is_total=is_subtotal_like(label) if cells else False)
            current.rows.append(row)
    for st in statements:
        _finalize(st)
    return statements, notes_pages


def _finalize(st: RawStatement) -> None:
    # Indentation level from the label's left edge
    xs = sorted({round(r.bbox[0]) for r in st.rows if r.bbox})
    base = xs[0] if xs else 0
    for r in st.rows:
        if r.bbox:
            r.level = int(max(0, (r.bbox[0] - base) // 8))
        # a heading that is immediately followed by its own values is not a heading
    # Headers that are wrapped label fragments are fixed in parse_pages; build hierarchy now.
    assign_hierarchy(st.rows)
    for r in st.rows:
        r.unit_type = unit_type_for(r.label, r.section_path)
