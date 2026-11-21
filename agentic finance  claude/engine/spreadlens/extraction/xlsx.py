"""XLSX statements (multiple worksheets). openpyxl never executes macros; we read cached values only."""

from __future__ import annotations

import io
import re
from decimal import Decimal

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from spreadlens.extraction.classify import classify_title, detect_scope, is_subtotal_like, unit_type_for
from spreadlens.extraction.hierarchy import assign_hierarchy
from spreadlens.extraction.periods import is_period_header
from spreadlens.extraction.types import RawCell, RawColumn, RawNote, RawRow, RawStatement
from spreadlens.numeric.scale import detect_currency, detect_scale


def _decimals_from_format(fmt: str | None) -> int | None:
    if not fmt or fmt == "General":
        return None
    m = re.search(r"0\.(0+)", fmt)
    return len(m.group(1)) if m else 0


def _cell_text(value, fmt: str | None) -> tuple[str, int | None]:
    if value is None:
        return "", None
    if isinstance(value, bool):
        return str(value), None
    if isinstance(value, int):
        decimals = _decimals_from_format(fmt)
        if decimals:
            return format(Decimal(value).quantize(Decimal(1).scaleb(-decimals)), "f"), decimals
        return str(value), 0
    if isinstance(value, float):
        # Excel stores IEEE doubles; repr gives the shortest exact round-trip string.
        d = Decimal(repr(value))
        decimals = _decimals_from_format(fmt)
        if decimals is not None:
            d = d.quantize(Decimal(1).scaleb(-decimals)) if decimals >= 0 else d
        return format(d, "f"), decimals
    return str(value).strip(), None


def read_xlsx(data: bytes) -> tuple[list[RawStatement], list[RawNote], list[dict], list[str]]:
    warnings: list[str] = []
    wb_values = load_workbook(io.BytesIO(data), data_only=True, read_only=False, keep_vba=False, keep_links=False)
    wb_formulas = load_workbook(io.BytesIO(data), data_only=False, read_only=False, keep_vba=False, keep_links=False)
    statements: list[RawStatement] = []
    notes: list[RawNote] = []
    pages = []
    for ws in wb_values.worksheets:
        wsf = wb_formulas[ws.title]
        grid = []
        for row in ws.iter_rows(min_row=1, max_row=min(ws.max_row, 2000), max_col=min(ws.max_column, 30)):
            grid.append(row)
        pages.append({"sheet": ws.title, "rows": len(grid), "method": "xlsx_cells"})
        head_text = "\n".join(
            " ".join(str(c.value) for c in r if c.value is not None and isinstance(c.value, str)) for r in grid[:8]
        )
        kind = classify_title(head_text) or classify_title(ws.title)
        if kind is None:
            if re.search(r"note", ws.title, re.I) or re.search(r"notes?\s+to", head_text, re.I):
                notes.extend(_sheet_notes(ws.title, grid))
            continue
        # header row: >=2 period-like cells
        header_idx = None
        for i, r in enumerate(grid[:25]):
            periods = [c for c in r if isinstance(c.value, (str, int)) and is_period_header(str(c.value))]
            if len(periods) >= 2:
                header_idx = i
                break
        title = next((str(c.value) for r in grid[:6] for c in r if isinstance(c.value, str) and classify_title(c.value)), ws.title)
        st = RawStatement(key=f"{kind}:{ws.title}", statement_type=kind, title=title, scope=detect_scope(head_text + " " + ws.title),
                          method="xlsx_cells", sheet=ws.title)
        sc = detect_scale(head_text)
        st.scale, st.scale_text = sc.value, sc.evidence + ([f"conflict: {','.join(sc.conflicts)}"] if sc.conflicts else [])
        if sc.conflicts:
            st.flags.append("conflicting_units")
        st.currency = detect_currency(head_text).value
        st.flags.append(f"title_context:{head_text[:300]}")
        if header_idx is None:
            st.flags.append("no_period_header_found")
            statements.append(st)
            continue
        hdr = grid[header_idx]
        col_map: dict[int, int] = {}
        note_col = None
        for c in hdr:
            if c.value is None:
                continue
            text = str(c.value)
            if text.strip().lower() in ("note", "notes", "note no."):
                note_col = c.column
            elif is_period_header(text):
                idx = len(st.columns)
                st.columns.append(RawColumn(index=idx, header_raw=text, period_end=None))
                col_map[c.column] = idx
        # restated markers in the row under the header
        if header_idx + 1 < len(grid):
            for c in grid[header_idx + 1]:
                if isinstance(c.value, str) and "restated" in c.value.lower() and c.column in col_map:
                    st.columns[col_map[c.column]].header_raw += " (Restated)"
        label_col = min((c.column for c in hdr if c.value is None or not is_period_header(str(c.value))), default=1)
        for r in grid[header_idx + 1:]:
            label_cell = next((c for c in r if c.column <= min(col_map) - 0 and isinstance(c.value, str) and c.column != note_col), None) if col_map else None
            label = str(label_cell.value).strip() if label_cell else ""
            label_flags: list[str] = []
            if not label and col_map:
                # a label written as a formula has no cached text; keep the formula text as untrusted data (never executed)
                for c in r:
                    if c.column < min(col_map) and c.column != note_col:
                        fv = wsf.cell(row=c.row, column=c.column).value
                        if isinstance(fv, str) and fv.startswith("="):
                            label, label_cell = fv.strip(), c
                            label_flags.append("label_is_formula_text")
                            break
            if label.lower().startswith("restated") and not any(r[k - 1].value is not None for k in col_map if k - 1 < len(r)):
                continue
            cells = []
            for c in r:
                if c.column in col_map:
                    fcell = wsf.cell(row=c.row, column=c.column)
                    is_formula = isinstance(fcell.value, str) and fcell.value.startswith("=")
                    text, decimals = _cell_text(c.value, c.number_format)
                    if is_formula and c.value is None:
                        text = "#FORMULA_NO_CACHED_VALUE"
                    if text == "" and not is_formula:
                        continue
                    cells.append(RawCell(column_index=col_map[c.column], raw_text=text, sheet=ws.title,
                                         cell_ref=f"{get_column_letter(c.column)}{c.row}", number_format_decimals=decimals))
            if not label and not cells:
                continue
            note_ref = None
            if note_col:
                nv = ws.cell(row=r[0].row, column=note_col).value
                note_ref = str(nv).strip() if nv is not None else None
            indent = 0
            if label_cell is not None and label_cell.alignment is not None and label_cell.alignment.indent:
                indent = int(label_cell.alignment.indent)
            raw_label = str(label_cell.value) if label_cell else ""
            lead = len(raw_label) - len(raw_label.lstrip(" "))
            row = RawRow(row_index=len(st.rows), label=label, cells=cells, note_ref=note_ref, sheet=ws.title,
                         cell_ref=f"{get_column_letter(label_cell.column)}{label_cell.row}" if label_cell else None,
                         level=indent + lead // 2, is_header=not cells, is_total=is_subtotal_like(label) if cells else False,
                         flags=label_flags)
            st.rows.append(row)
        _ = label_col
        assign_hierarchy(st.rows)
        for row in st.rows:
            row.unit_type = unit_type_for(row.label, row.section_path)
        statements.append(st)
    if any(ws.sheet_state != "visible" for ws in wb_values.worksheets):
        warnings.append("Workbook has hidden worksheets; they were read like visible ones.")
    return statements, notes, pages, warnings


def _sheet_notes(sheet: str, grid) -> list[RawNote]:
    out: list[RawNote] = []
    current: RawNote | None = None
    for r in grid:
        text = " ".join(str(c.value) for c in r if c.value is not None).strip()
        if not text:
            continue
        m = re.match(r"^(?:note\s+)?(\d{1,3})[\.:]?\s+(.{2,80})$", text, re.I)
        if m and len(text) < 90:
            current = RawNote(note_ref=m.group(1), title=m.group(2).strip(), text="", sheet=sheet)
            out.append(current)
        elif current is not None:
            current.text += text + "\n"
    return out
