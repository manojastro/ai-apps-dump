"""Intermediate extraction structures (plain data, serialisable into typed artifacts)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Word:
    text: str
    x0: float
    top: float
    x1: float
    bottom: float
    page: int
    conf: float | None = None  # OCR confidence (None for digital text)


@dataclass
class PageText:
    page: int
    width: float
    height: float
    words: list[Word]
    method: str  # pdf_text | ocr_local
    ocr_conf: float | None = None

    @property
    def text(self) -> str:
        return "\n".join(" ".join(w.text for w in line) for line in group_lines(self.words))


def group_lines(words: list[Word], tol: float = 3.0) -> list[list[Word]]:
    lines: list[list[Word]] = []
    for w in sorted(words, key=lambda w: (round(w.top, 1), w.x0)):
        if lines and abs(lines[-1][0].top - w.top) <= tol:
            lines[-1].append(w)
        else:
            lines.append([w])
    return [sorted(line, key=lambda w: w.x0) for line in lines]


@dataclass
class RawCell:
    column_index: int
    raw_text: str
    page: int | None = None
    bbox: list[float] | None = None
    sheet: str | None = None
    cell_ref: str | None = None
    ocr_confidence: float | None = None
    number_format_decimals: int | None = None


@dataclass
class RawRow:
    row_index: int
    label: str
    cells: list[RawCell]
    section_path: list[str] = field(default_factory=list)
    level: int = 0
    is_header: bool = False
    is_total: bool = False
    note_ref: str | None = None
    unit_type: str = "monetary"
    page: int | None = None
    bbox: list[float] | None = None
    sheet: str | None = None
    cell_ref: str | None = None
    flags: list[str] = field(default_factory=list)
    parent_total_index: int | None = None


@dataclass
class RawColumn:
    index: int
    header_raw: str
    period_end: str | None  # ISO date
    period_start: str | None = None
    duration: str = "unknown"  # annual | point_in_time | quarterly | ytd | unknown
    restated: bool = False
    x1: float | None = None


@dataclass
class RawStatement:
    key: str
    statement_type: str
    title: str
    scope: str | None
    method: str
    pages: list[int] = field(default_factory=list)
    sheet: str | None = None
    columns: list[RawColumn] = field(default_factory=list)
    rows: list[RawRow] = field(default_factory=list)
    scale_text: list[str] = field(default_factory=list)
    scale: str | None = None
    currency: str | None = None
    flags: list[str] = field(default_factory=list)


@dataclass
class RawNote:
    note_ref: str
    title: str
    text: str
    page: int | None = None
    sheet: str | None = None
    scope: str | None = None


@dataclass
class ExtractionResult:
    statements: list[RawStatement]
    notes: list[RawNote]
    pages: list[dict[str, Any]]
    method_summary: str
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
