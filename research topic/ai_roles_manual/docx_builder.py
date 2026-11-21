# -*- coding: utf-8 -*-
"""Styling engine for the Comprehensive AI Roles Career & Transition Manual.

Implements the mandated formatting standard:
  - Margins: exactly 0.75 in on all sides
  - Body: Calibri 10.5 pt, #212529
  - H1: 16 pt Calibri/Arial Bold #0F172A | H2: 13 pt #1E293B | H3: 11 pt #334155
  - Code blocks: single-cell tables, fill #0F172A, Consolas 9 pt, #F8FAFC, line spacing 1.15
  - Callouts: single-cell tables, thick left border (sz 24, #0F172A), fill #F1F5F9, italic Calibri
  - Data tables: centered, header row #0F172A white bold, alternating rows #F8FAFC,
    explicit cell padding, borders #CBD5E1
"""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BODY_COLOR = "212529"
NAVY_1 = "0F172A"
NAVY_2 = "1E293B"
SLATE_3 = "334155"
CODE_BG = "0F172A"
CODE_FG = "F8FAFC"
CALLOUT_BG = "F1F5F9"
ROW_ALT = "F8FAFC"
BORDER = "CBD5E1"
WHITE = "FFFFFF"
GRAY = "64748B"

PAGE_W_IN = 8.5
MARGIN_IN = 0.75
CONTENT_W_IN = PAGE_W_IN - 2 * MARGIN_IN  # 7.0 in usable width


# ---------------------------------------------------------------- low-level XML
def _el(tag, **attrs):
    e = OxmlElement(tag)
    for k, v in attrs.items():
        e.set(qn("w:" + k), str(v))
    return e


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_pr.append(_el("w:shd", val="clear", color="auto", fill=fill))


def set_cell_margins(cell, top=60, start=100, bottom=60, end=100):
    """Explicit interior cell padding, in twips."""
    tc_pr = cell._tc.get_or_add_tcPr()
    mar = _el("w:tcMar")
    for name, val in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        mar.append(_el("w:" + name, w=val, type="dxa"))
    tc_pr.append(mar)


def set_table_borders(table, color=BORDER, sz=4, inside=True):
    tbl_pr = table._tbl.tblPr
    borders = _el("w:tblBorders")
    edges = ["top", "left", "bottom", "right"]
    if inside:
        edges += ["insideH", "insideV"]
    for edge in edges:
        borders.append(_el("w:" + edge, val="single", sz=sz, space=0, color=color))
    tbl_pr.append(borders)


def set_row_cant_split(row):
    tr_pr = row._tr.get_or_add_trPr()
    tr_pr.append(_el("w:cantSplit"))


def set_header_row(row):
    tr_pr = row._tr.get_or_add_trPr()
    tr_pr.append(_el("w:tblHeader"))


def set_col_widths(table, widths_in):
    """Fix column widths (inches) at both grid and cell level."""
    tbl = table._tbl
    grid = tbl.tblGrid
    if grid is not None:
        for gc, w in zip(grid.findall(qn("w:gridCol")), widths_in):
            gc.set(qn("w:w"), str(int(w * 1440)))
    for row in table.rows:
        for cell, w in zip(row.cells, widths_in):
            cell.width = Inches(w)


def clear_table_style(table):
    table.style = doc_table_style(table)


def doc_table_style(table):
    from docx.enum.table import WD_TABLE_ALIGNMENT
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    layout = _el("w:tblLayout", type="fixed")
    tbl_pr.append(layout)
    return table.style


def add_field(paragraph, instr, placeholder="1"):
    run = paragraph.add_run()
    fld1 = _el("w:fldChar", fldCharType="begin")
    instr_el = OxmlElement("w:instrText")
    instr_el.set(qn("xml:space"), "preserve")
    instr_el.text = instr
    fld2 = _el("w:fldChar", fldCharType="separate")
    t = OxmlElement("w:t")
    t.text = placeholder
    fld3 = _el("w:fldChar", fldCharType="end")
    run._r.append(fld1)
    run._r.append(instr_el)
    run._r.append(fld2)
    run._r.append(t)
    run._r.append(fld3)
    return run


# ---------------------------------------------------------------- base document
def new_document():
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(MARGIN_IN)
    section.bottom_margin = Inches(MARGIN_IN)
    section.left_margin = Inches(MARGIN_IN)
    section.right_margin = Inches(MARGIN_IN)

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor.from_string(BODY_COLOR)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.15

    for name, size, color, before, after in (
        ("Heading 1", 16, NAVY_1, 14, 6),
        ("Heading 2", 13, NAVY_2, 10, 4),
        ("Heading 3", 11, SLATE_3, 8, 3),
        ("Heading 4", 10.5, SLATE_3, 6, 3),
    ):
        st = doc.styles[name]
        st.font.name = "Calibri"
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = RGBColor.from_string(color)
        st.font.italic = False
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.keep_with_next = True
        rpr = st.element.get_or_add_rPr()
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = _el("w:rFonts")
            rpr.append(rfonts)
        for attr in ("w:ascii", "w:hAnsi", "w:cs"):
            rfonts.set(qn(attr), "Calibri")

    footer = section.footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run("Comprehensive AI Roles Career & Transition Manual  |  Page ")
    r.font.size = Pt(8)
    r.font.name = "Calibri"
    r.font.color.rgb = RGBColor.from_string(GRAY)
    fld_run = add_field(fp, r"PAGE \* arabic \* MERGEFORMAT")
    fld_run.font.size = Pt(8)
    fld_run.font.name = "Calibri"
    fld_run.font.color.rgb = RGBColor.from_string(GRAY)
    return doc


# ---------------------------------------------------------------- block builders
def H(doc, text, level=1, page_break_before=False):
    h = doc.add_heading(text, level=level)
    if page_break_before:
        h.paragraph_format.page_break_before = True
    for run in h.runs:
        run.font.name = "Calibri"
        run.font.bold = True
    return h


def P(doc, text, bold=False, italic=False, size=10.5, color=BODY_COLOR,
      align=None, space_after=6):
    para = doc.add_paragraph()
    para.paragraph_format.space_after = Pt(space_after)
    if align == "center":
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)
    return para


def RICH(doc, segments, space_after=6):
    """segments: list of (text, bold, italic, color) tuples in one paragraph."""
    para = doc.add_paragraph()
    para.paragraph_format.space_after = Pt(space_after)
    for text, bold, italic, color in segments:
        run = para.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(10.5)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = RGBColor.from_string(color)
    return para


def BULLETS(doc, items, style="List Bullet"):
    for item in items:
        para = doc.add_paragraph(style=style)
        para.paragraph_format.space_after = Pt(2)
        para.paragraph_format.line_spacing = 1.15
        if isinstance(item, tuple):
            lead, rest = item
            r1 = para.add_run(lead)
            r1.font.bold = True
            r1.font.name = "Calibri"
            r1.font.size = Pt(10.5)
            r1.font.color.rgb = RGBColor.from_string(BODY_COLOR)
            r2 = para.add_run(rest)
            r2.font.name = "Calibri"
            r2.font.size = Pt(10.5)
            r2.font.color.rgb = RGBColor.from_string(BODY_COLOR)
        else:
            run = para.add_run(item)
            run.font.name = "Calibri"
            run.font.size = Pt(10.5)
            run.font.color.rgb = RGBColor.from_string(BODY_COLOR)


def NUMBERS(doc, items):
    """Explicitly numbered list - guarantees each list restarts at 1
    (python-docx's shared List Number definition would continue one
    global counter across the document)."""
    for idx, item in enumerate(items, start=1):
        para = doc.add_paragraph()
        para.paragraph_format.space_after = Pt(3)
        para.paragraph_format.line_spacing = 1.15
        para.paragraph_format.left_indent = Inches(0.25)
        para.paragraph_format.first_line_indent = Inches(-0.25)
        num_run = para.add_run(f"{idx}.  ")
        num_run.font.name = "Calibri"
        num_run.font.size = Pt(10.5)
        num_run.font.bold = True
        num_run.font.color.rgb = RGBColor.from_string(NAVY_1)
        if isinstance(item, tuple):
            lead, rest = item
            r1 = para.add_run(lead)
            r1.font.bold = True
            r1.font.name = "Calibri"
            r1.font.size = Pt(10.5)
            r1.font.color.rgb = RGBColor.from_string(BODY_COLOR)
            r2 = para.add_run(rest)
            r2.font.name = "Calibri"
            r2.font.size = Pt(10.5)
            r2.font.color.rgb = RGBColor.from_string(BODY_COLOR)
        else:
            run = para.add_run(item)
            run.font.name = "Calibri"
            run.font.size = Pt(10.5)
            run.font.color.rgb = RGBColor.from_string(BODY_COLOR)


def _code_table(doc):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    tbl_pr.append(_el("w:tblLayout", type="fixed"))
    borders = _el("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        borders.append(_el("w:" + edge, val="single", sz=2, space=0, color=NAVY_1))
    tbl_pr.append(borders)
    cell = table.cell(0, 0)
    set_cell_shading(cell, CODE_BG)
    set_cell_margins(cell, top=120, start=160, bottom=120, end=160)
    set_col_widths(table, [CONTENT_W_IN])
    return table, cell


def CODE(doc, code_text, caption=None):
    """Dark code block: single-cell table, #0F172A fill, Consolas 9 pt, #F8FAFC, 1.15 line spacing."""
    if caption:
        cap = doc.add_paragraph()
        cap.paragraph_format.space_after = Pt(2)
        cap.paragraph_format.keep_with_next = True
        run = cap.add_run(caption)
        run.font.name = "Calibri"
        run.font.size = Pt(9)
        run.font.bold = True
        run.font.color.rgb = RGBColor.from_string(SLATE_3)
    table, cell = _code_table(doc)
    first = True
    for line in code_text.split("\n"):
        para = cell.paragraphs[0] if first else cell.add_paragraph()
        first = False
        para.paragraph_format.line_spacing = 1.15
        para.paragraph_format.space_after = Pt(0)
        para.paragraph_format.space_before = Pt(0)
        run = para.add_run(line if line else " ")
        run.font.name = "Consolas"
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor.from_string(CODE_FG)
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(4)
    spacer.paragraph_format.line_spacing = 1.0
    r = spacer.add_run(" ")
    r.font.size = Pt(2)
    return table


def CALLOUT(doc, text, title=None):
    """Callout: single-cell table, thick left border (sz 24, #0F172A), fill #F1F5F9, italic body."""
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    tbl_pr.append(_el("w:tblLayout", type="fixed"))
    borders = _el("w:tblBorders")
    borders.append(_el("w:left", val="single", sz=24, space=0, color=NAVY_1))
    for edge in ("top", "bottom", "right", "insideH", "insideV"):
        borders.append(_el("w:" + edge, val="single", sz=2, space=0, color=BORDER))
    tbl_pr.append(borders)
    cell = table.cell(0, 0)
    set_cell_shading(cell, CALLOUT_BG)
    set_cell_margins(cell, top=100, start=160, bottom=100, end=160)
    set_col_widths(table, [CONTENT_W_IN])
    set_row_cant_split(table.rows[0])  # keep the callout box on one page
    para = cell.paragraphs[0]
    para.paragraph_format.line_spacing = 1.15
    if title:
        t = para.add_run(title + "  ")
        t.font.name = "Calibri"
        t.font.size = Pt(10.5)
        t.font.bold = True
        t.font.italic = True
        t.font.color.rgb = RGBColor.from_string(NAVY_1)
    run = para.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(10.5)
    run.font.italic = True
    run.font.color.rgb = RGBColor.from_string(BODY_COLOR)
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(4)
    r = spacer.add_run(" ")
    r.font.size = Pt(2)
    return table


def TABLE(doc, headers, rows, widths=None, caption=None, font_size=9,
          header_size=9, align_first_left=True):
    """Data table: centered, navy header with white bold text, alternating #F8FAFC rows,
    padding and light #CBD5E1 borders."""
    if caption:
        cap = doc.add_paragraph()
        cap.paragraph_format.space_after = Pt(2)
        cap.paragraph_format.keep_with_next = True
        run = cap.add_run(caption)
        run.font.name = "Calibri"
        run.font.size = Pt(9.5)
        run.font.bold = True
        run.font.color.rgb = RGBColor.from_string(NAVY_2)

    ncols = len(headers)
    if widths is None:
        widths = [CONTENT_W_IN / ncols] * ncols
    else:
        total = sum(widths)
        widths = [w * CONTENT_W_IN / total for w in widths]

    table = doc.add_table(rows=1 + len(rows), cols=ncols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    tbl_pr.append(_el("w:tblLayout", type="fixed"))
    set_table_borders(table, color=BORDER, sz=4, inside=True)
    set_col_widths(table, widths)

    hdr = table.rows[0]
    set_header_row(hdr)
    set_row_cant_split(hdr)
    for j, htext in enumerate(headers):
        cell = hdr.cells[j]
        set_cell_shading(cell, NAVY_1)
        set_cell_margins(cell, top=70, start=90, bottom=70, end=90)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.line_spacing = 1.1
        run = para.add_run(htext)
        run.font.name = "Calibri"
        run.font.size = Pt(header_size)
        run.font.bold = True
        run.font.color.rgb = RGBColor.from_string(WHITE)

    for i, row_vals in enumerate(rows):
        row = table.rows[i + 1]
        set_row_cant_split(row)
        fill = ROW_ALT if i % 2 == 1 else None
        for j, val in enumerate(row_vals):
            cell = row.cells[j]
            if fill:
                set_cell_shading(cell, fill)
            set_cell_margins(cell, top=60, start=90, bottom=60, end=90)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            para = cell.paragraphs[0]
            if j == 0 and align_first_left:
                para.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            para.paragraph_format.line_spacing = 1.1
            run = para.add_run(str(val))
            run.font.name = "Calibri"
            run.font.size = Pt(font_size)
            run.font.color.rgb = RGBColor.from_string(BODY_COLOR)
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(4)
    r = spacer.add_run(" ")
    r.font.size = Pt(2)
    return table


def PAGEBREAK(doc):
    from docx.enum.text import WD_BREAK
    para = doc.add_paragraph()
    run = para.add_run()
    run.add_break(WD_BREAK.PAGE)
    para.paragraph_format.space_after = Pt(0)


def COVER(doc, title_lines, subtitle, meta_lines):
    """Clean navy-on-white cover page."""
    for _ in range(3):
        P(doc, " ", space_after=0)
    for line in title_lines:
        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.space_after = Pt(4)
        run = para.add_run(line)
        run.font.name = "Calibri"
        run.font.size = Pt(28)
        run.font.bold = True
        run.font.color.rgb = RGBColor.from_string(NAVY_1)
    bar = doc.add_paragraph()
    bar.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = bar.add_run("─" * 42)
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor.from_string(BORDER)
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_before = Pt(10)
    run = para.add_run(subtitle)
    run.font.name = "Calibri"
    run.font.size = Pt(13)
    run.font.italic = True
    run.font.color.rgb = RGBColor.from_string(SLATE_3)
    for _ in range(6):
        P(doc, " ", space_after=0)
    for line in meta_lines:
        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.space_after = Pt(3)
        run = para.add_run(line)
        run.font.name = "Calibri"
        run.font.size = Pt(10.5)
        run.font.color.rgb = RGBColor.from_string(SLATE_3)
    PAGEBREAK(doc)
