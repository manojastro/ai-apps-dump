"""Render synthetic statements to digital PDF, scanned (image-only) PDF and XLSX."""

from __future__ import annotations

import io
import random
import textwrap
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal as D

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from fixtures.synth.model import Row, StatementSpec

W, H = A4
X_LABEL, X_NOTE, X_C1, X_C2 = 50, 335, 465, 548


def fmt(v: D | str | None, grouping: str = "intl", places: int = 2) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    q = v.quantize(D(1).scaleb(-places))
    s = format(abs(q), f",.{places}f") if grouping == "intl" else _indian(abs(q), places)
    return f"({s})" if q < 0 else s


def _indian(v: D, places: int) -> str:
    s = format(v, f".{places}f")
    i, _, frac = s.partition(".")
    if len(i) > 3:
        head, tail = i[:-3], i[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        i = ",".join(parts + [tail])
    return i + ("." + frac if frac else "")


@dataclass
class PdfStatementPage:
    spec: StatementSpec
    company: str
    scope_label: str  # "Standalone" / "Consolidated"
    unit_line: str = "(All amounts in INR crores, unless otherwise stated)"
    periods: tuple[date, date] = (date(2025, 3, 31), date(2024, 3, 31))
    headers: tuple[str, str] | None = None
    restated_col: int | None = None
    grouping: str = "intl"
    split_after: int | None = None  # row index to continue on the next page (multi-page table)
    extra_lines: list[str] = field(default_factory=list)


def _header_text(p: date) -> str:
    return f"{p.day} {p.strftime('%B')} {p.year}"


def draw_statement(c: canvas.Canvas, sp: PdfStatementPage) -> None:
    rows = sp.spec.rows
    chunks = [rows] if sp.split_after is None else [rows[: sp.split_after], rows[sp.split_after:]]
    for ci, chunk in enumerate(chunks):
        y = H - 50
        if ci == 0:
            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(W / 2, y, sp.company)
            y -= 18
            c.setFont("Helvetica-Bold", 11)
            title = sp.spec.title if sp.scope_label.lower() in sp.spec.title.lower() else f"{sp.scope_label} {sp.spec.title}"
            c.drawCentredString(W / 2, y, title)
            y -= 15
            c.setFont("Helvetica", 9)
            c.drawCentredString(W / 2, y, sp.unit_line)
            y -= 13
            for line in sp.extra_lines:
                c.drawCentredString(W / 2, y, line)
                y -= 12
            y -= 10
        else:
            y -= 20
        c.setFont("Helvetica-Bold", 9)
        c.drawString(X_LABEL, y, "Particulars")
        c.drawRightString(X_NOTE + 18, y, "Note")
        h1, h2 = sp.headers or (_header_text(sp.periods[0]), _header_text(sp.periods[1]))
        c.drawRightString(X_C1, y, h1)
        c.drawRightString(X_C2, y, h2)
        if sp.restated_col is not None:
            c.setFont("Helvetica", 8)
            c.drawRightString((X_C1, X_C2)[sp.restated_col], y - 10, "(Restated)")
            y -= 10
        y -= 18
        for r in chunk:
            _draw_row(c, r, y, sp)
            y -= 14
            if y < 60:
                c.showPage()
                y = H - 60
        if ci == len(chunks) - 1:
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(X_LABEL, max(y - 20, 40), "The accompanying notes form an integral part of these financial statements.")
        c.showPage()


def _draw_row(c: canvas.Canvas, r: Row, y: float, sp: PdfStatementPage) -> None:
    bold = r.kind in ("header", "total")
    c.setFont("Helvetica-Bold" if bold else "Helvetica", 9)
    x = X_LABEL + (10 * r.level if r.kind == "item" else 0)
    c.drawString(x, y, r.label)
    if r.note:
        c.setFont("Helvetica", 9)
        c.drawRightString(X_NOTE + 14, y, r.note)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 9)
    if r.kind != "header":
        v1 = r.values.get(sp.periods[0])
        v2 = r.values.get(sp.periods[1])
        places = 2
        c.drawRightString(X_C1, y, fmt(v1, sp.grouping, places))
        c.drawRightString(X_C2, y, fmt(v2, sp.grouping, places))


def draw_cover(c: canvas.Canvas, company: str, lines: list[str]) -> None:
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(W / 2, H / 2 + 40, company)
    c.setFont("Helvetica", 13)
    y = H / 2
    for line in lines:
        c.drawCentredString(W / 2, y, line)
        y -= 20
    c.showPage()


def draw_notes(c: canvas.Canvas, scope_label: str, notes: list[tuple[str, str, str]]) -> None:
    y = H - 50
    c.setFont("Helvetica-Bold", 11)
    c.drawString(X_LABEL, y, f"Notes to the {scope_label.lower()} financial statements")
    y -= 26
    for ref, title, body in notes:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(X_LABEL, y, f"{ref}. {title}")
        y -= 14
        c.setFont("Helvetica", 9)
        for line in textwrap.wrap(body, 100):
            c.drawString(X_LABEL, y, line)
            y -= 12
        y -= 10
        if y < 80:
            c.showPage()
            y = H - 50
    c.showPage()


def pdf_bytes(draw) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, invariant=1)
    c.setTitle("Synthetic financial statements (SpreadLens fixture)")
    c.setAuthor("SpreadLens synthetic fixture generator")
    draw(c)
    c.save()
    return buf.getvalue()


def scanned_from_pdf(data: bytes, dpi: int = 150, seed: int = 7) -> bytes:
    """Rasterise each page and rebuild an image-only PDF with mild noise and skew (no text layer)."""
    import pypdfium2 as pdfium
    from PIL import Image, ImageFilter
    from reportlab.lib.utils import ImageReader

    rnd = random.Random(seed)
    pdf = pdfium.PdfDocument(io.BytesIO(data))
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, invariant=1)
    for i in range(len(pdf)):
        img = pdf[i].render(scale=dpi / 72).to_pil().convert("L")
        img = img.rotate(rnd.uniform(-0.25, 0.25), resample=Image.BICUBIC, fillcolor=255, expand=False)
        px = img.load()
        w, h = img.size
        for _ in range(int(w * h * 0.0015)):
            x, y = rnd.randrange(w), rnd.randrange(h)
            px[x, y] = rnd.choice((0, 90, 200))
        img = img.filter(ImageFilter.GaussianBlur(0.35))
        jb = io.BytesIO()
        img.save(jb, format="JPEG", quality=82)
        jb.seek(0)
        c.drawImage(ImageReader(jb), 0, 0, width=W, height=H)
        c.showPage()
    pdf.close()
    c.save()
    return buf.getvalue()


def xlsx_bytes(sheets: list[tuple[str, StatementSpec, str, str]], periods: tuple[date, date], factor: D = D("1"),
               notes: list[tuple[str, str, str]] | None = None, label_overrides: dict[str, str] | None = None,
               company: str = "") -> bytes:
    """sheets: (sheet_name, spec, title, unit_line). factor converts crores to the sheet's unit."""
    wb = Workbook()
    wb.remove(wb.active)
    for name, spec, title, unit_line in sheets:
        ws = wb.create_sheet(name)
        ws["A1"] = company
        ws["A2"] = title
        ws["A3"] = unit_line
        ws["A1"].font = ws["A2"].font = Font(bold=True)
        ws["A5"], ws["B5"] = "Particulars", "Note"
        ws["C5"], ws["D5"] = _header_text(periods[0]), _header_text(periods[1])
        for cell in ("A5", "B5", "C5", "D5"):
            ws[cell].font = Font(bold=True)
        r = 6
        for row in spec.rows:
            label = (label_overrides or {}).get(row.label, row.label)
            ws.cell(row=r, column=1, value=label)
            ws.cell(row=r, column=1).alignment = Alignment(indent=row.level if row.kind == "item" else 0)
            if row.kind in ("header", "total"):
                ws.cell(row=r, column=1).font = Font(bold=True)
            if row.note:
                ws.cell(row=r, column=2, value=int(row.note))
            if row.kind != "header":
                for col, p in ((3, periods[0]), (4, periods[1])):
                    v = row.values.get(p)
                    if isinstance(v, D):
                        f = D("1") if (row.code or "").startswith("is.eps") else factor  # per-share amounts are never scaled
                        cell = ws.cell(row=r, column=col, value=float(v * f))
                        cell.number_format = "#,##,##0.00;(#,##,##0.00)"
                    elif isinstance(v, str):
                        ws.cell(row=r, column=col, value=v)
            r += 1
        ws.column_dimensions["A"].width = 58
        ws.column_dimensions["C"].width = 16
        ws.column_dimensions["D"].width = 16
    if notes:
        ws = wb.create_sheet("Notes")
        ws["A1"] = "Notes to the financial statements"
        r = 3
        for ref, title, body in notes:
            ws.cell(row=r, column=1, value=f"{ref}. {title}")
            ws.cell(row=r + 1, column=1, value=body)
            r += 3
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
