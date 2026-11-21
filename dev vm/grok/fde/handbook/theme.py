"""Shared Word theme and primitives for the career handbook."""
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn, nsdecls
from docx.shared import Cm, Inches, Pt, RGBColor, Twips, Emu
from docx.enum.style import WD_STYLE_TYPE

NAVY = "1B365D"
NAVY_RGB = RGBColor(0x1B, 0x36, 0x5D)
TEAL = "1F6F8B"
TEAL_RGB = RGBColor(0x1F, 0x6F, 0x8B)
GOLD = "C4A35A"
SLATE = "334155"
SLATE_RGB = RGBColor(0x33, 0x41, 0x55)
MUTED = "64748B"
ROW_ALT = "F4F7FA"
HEADER_FILL = "1B365D"
CALLOUT_FILL = "EEF4F8"
MUST_FILL = "FFF6E5"
WARN_FILL = "FDECEC"
CODE_FILL = "F8FAFC"
WHITE = "FFFFFF"
CONTENT_WIDTH = 9360  # US Letter, 1" margins


def set_run_font(run, name="Arial", size=11, bold=False, italic=False, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color is not None:
        if isinstance(color, str):
            run.font.color.rgb = RGBColor.from_string(color)
        else:
            run.font.color.rgb = color


def shade_cell(cell, fill):
    tc = cell._tePr if hasattr(cell, "_tePr") else cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def set_cell_margins(cell, top=60, bottom=60, left=80, right=80):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, v in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        node = OxmlElement(f"w:{m}")
        node.set(qn("w:w"), str(v))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def set_cell_width(cell, dxa):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcW = OxmlElement("w:tcW")
    tcW.set(qn("w:w"), str(dxa))
    tcW.set(qn("w:type"), "dxa")
    tcPr.append(tcW)


def set_table_borders(table, color="CCCCCC", sz="4"):
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else OxmlElement("w:tblPr")
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), sz)
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tblPr.append(borders)


def prevent_row_split(row):
    tr = row._tr
    trPr = tr.get_or_add_trPr()
    cant = OxmlElement("w:cantSplit")
    trPr.append(cant)


def add_page_field(paragraph, kind="PAGE"):
    run = paragraph.add_run()
    r = run._r
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f" {kind} "
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "end")
    r.append(fld1)
    r.append(instr)
    r.append(fld2)
    set_run_font(run, size=9, color=MUTED)


def add_hyperlink(paragraph, text, url):
    part = paragraph.part
    r_id = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    new_run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), TEAL)
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "22")
    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), "Arial")
    rFonts.set(qn("w:hAnsi"), "Arial")
    rPr.extend([rFonts, color, u, sz])
    t = OxmlElement("w:t")
    t.text = text
    new_run.append(rPr)
    new_run.append(t)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)


def configure_styles(doc):
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(11)
    normal.font.color.rgb = SLATE_RGB
    normal.paragraph_format.space_after = Pt(8)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.line_spacing = 1.15
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")

    heading_specs = [
        ("Heading 1", 18, NAVY, 18, 8, 0),
        ("Heading 2", 14, TEAL, 14, 6, 1),
        ("Heading 3", 12, NAVY, 10, 4, 2),
        ("Heading 4", 11, SLATE, 8, 4, 3),
    ]
    for name, size, color, before, after, outline in heading_specs:
        st = styles[name]
        st.font.name = "Arial"
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = RGBColor.from_string(color)
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.keep_with_next = True
        pPr = st.element.get_or_add_pPr()
        ol = OxmlElement("w:outlineLvl")
        ol.set(qn("w:val"), str(outline))
        pPr.append(ol)

    if "Caption" not in [s.name for s in styles]:
        cap = styles.add_style("Caption", WD_STYLE_TYPE.PARAGRAPH)
    else:
        cap = styles["Caption"]
    cap.font.name = "Arial"
    cap.font.size = Pt(9)
    cap.font.italic = True
    cap.font.color.rgb = RGBColor.from_string(MUTED)


def init_document():
    doc = Document()
    configure_styles(doc)
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.header_distance = Inches(0.4)
    section.footer_distance = Inches(0.4)

    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = hp.add_run("Forward Deployed & Agentic AI Engineering Handbook")
    set_run_font(run, size=9, color=MUTED)
    pPr = hp._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), NAVY)
    pBdr.append(bottom)
    pPr.append(pBdr)

    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    left = fp.add_run("v1.0  ·  Research date 15 September 2026  ·  Confidential study copy")
    set_run_font(left, size=8, color=MUTED)
    fp.add_run("\t")
    page_run = fp.add_run("Page ")
    set_run_font(page_run, size=9, color=MUTED)
    add_page_field(fp, "PAGE")
    of = fp.add_run(" of ")
    set_run_font(of, size=9, color=MUTED)
    add_page_field(fp, "NUMPAGES")
    fp.paragraph_format.tab_stops.add_tab_stop(Inches(6.5), WD_TAB_ALIGNMENT.RIGHT)
    pPr = fp._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    top = OxmlElement("w:top")
    top.set(qn("w:val"), "single")
    top.set(qn("w:sz"), "6")
    top.set(qn("w:space"), "4")
    top.set(qn("w:color"), NAVY)
    pBdr.append(top)
    pPr.append(pBdr)
    return doc


class Book:
    def __init__(self, doc):
        self.doc = doc
        self.fn = 1
        self.footnotes = {}

    def page_break(self):
        self.doc.add_page_break()

    def h1(self, text):
        p = self.doc.add_heading(text, level=1)
        return p

    def h2(self, text):
        return self.doc.add_heading(text, level=2)

    def h3(self, text):
        return self.doc.add_heading(text, level=3)

    def h4(self, text):
        return self.doc.add_heading(text, level=4)

    def p(self, text, bold=False, italic=False, size=11):
        para = self.doc.add_paragraph()
        run = para.add_run(text)
        set_run_font(run, size=size, bold=bold, italic=italic, color=SLATE)
        para.paragraph_format.space_after = Pt(8)
        return para

    def rich(self, parts, size=11):
        """parts: list of str or (text, dict(bold, italic, color))."""
        para = self.doc.add_paragraph()
        for part in parts:
            if isinstance(part, str):
                run = para.add_run(part)
                set_run_font(run, size=size, color=SLATE)
            else:
                text, opts = part
                run = para.add_run(text)
                set_run_font(
                    run,
                    size=opts.get("size", size),
                    bold=opts.get("bold", False),
                    italic=opts.get("italic", False),
                    color=opts.get("color", SLATE),
                )
        para.paragraph_format.space_after = Pt(8)
        return para

    def bullets(self, items, level=0):
        for item in items:
            para = self.doc.add_paragraph(item, style="List Bullet")
            for run in para.runs:
                set_run_font(run, size=11, color=SLATE)
            para.paragraph_format.left_indent = Inches(0.25 + 0.25 * level)
            para.paragraph_format.space_after = Pt(3)

    def numbered(self, items):
        for item in items:
            para = self.doc.add_paragraph(item, style="List Number")
            for run in para.runs:
                set_run_font(run, size=11, color=SLATE)
            para.paragraph_format.space_after = Pt(3)

    def quote(self, text, source=None):
        para = self.doc.add_paragraph()
        para.paragraph_format.left_indent = Inches(0.3)
        para.paragraph_format.space_before = Pt(6)
        para.paragraph_format.space_after = Pt(6)
        run = para.add_run(text)
        set_run_font(run, size=11, italic=True, color=SLATE)
        if source:
            s = para.add_run("  — " + source)
            set_run_font(s, size=9, italic=False, color=MUTED)
        return para

    def box(self, title, body, fill=CALLOUT_FILL, title_color=NAVY):
        table = self.doc.add_table(rows=1, cols=1)
        table.autofit = False
        table.allow_autofit = False
        table.columns[0].width = Twips(CONTENT_WIDTH)
        cell = table.cell(0, 0)
        set_cell_width(cell, CONTENT_WIDTH)
        shade_cell(cell, fill)
        set_cell_margins(cell, 80, 80, 120, 120)
        cell.text = ""
        p = cell.paragraphs[0]
        r = p.add_run(title)
        set_run_font(r, size=10, bold=True, color=title_color)
        p.paragraph_format.space_after = Pt(4)
        if isinstance(body, str):
            body = [body]
        for line in body:
            bp = cell.add_paragraph()
            br = bp.add_run(line)
            set_run_font(br, size=10, color=SLATE)
            bp.paragraph_format.space_after = Pt(2)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(6)

    def must(self, body):
        self.box("MUST KNOW", body if isinstance(body, list) else [body], MUST_FILL, "8A6A1B")

    def warn(self, body):
        self.box("EVIDENCE / CAUTION", body if isinstance(body, list) else [body], WARN_FILL, "8B2E2E")

    def interview(self, body):
        self.box("INTERVIEW CALLOUT", body if isinstance(body, list) else [body], CALLOUT_FILL, TEAL)

    def code(self, text, caption=None):
        table = self.doc.add_table(rows=1, cols=1)
        table.autofit = False
        table.columns[0].width = Twips(CONTENT_WIDTH)
        cell = table.cell(0, 0)
        set_cell_width(cell, CONTENT_WIDTH)
        shade_cell(cell, CODE_FILL)
        set_cell_margins(cell, 80, 80, 120, 120)
        cell.text = ""
        p = cell.paragraphs[0]
        run = p.add_run(text)
        set_run_font(run, name="Consolas", size=8.5, color=SLATE)
        p.paragraph_format.space_after = Pt(0)
        if caption:
            cap = self.doc.add_paragraph(caption, style="Caption")
            cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
        else:
            self.doc.add_paragraph().paragraph_format.space_after = Pt(6)

    def table(self, headers, rows, col_widths=None, caption=None):
        n = len(headers)
        if col_widths is None:
            w = CONTENT_WIDTH // n
            col_widths = [w] * (n - 1) + [CONTENT_WIDTH - w * (n - 1)]
        assert sum(col_widths) == CONTENT_WIDTH, (sum(col_widths), CONTENT_WIDTH)
        table = self.doc.add_table(rows=1 + len(rows), cols=n)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        table.allow_autofit = False
        set_table_borders(table, "D0D7DE", "4")
        for i, w in enumerate(col_widths):
            table.columns[i].width = Twips(w)
        hdr = table.rows[0]
        prevent_row_split(hdr)
        for i, h in enumerate(headers):
            cell = hdr.cells[i]
            set_cell_width(cell, col_widths[i])
            shade_cell(cell, HEADER_FILL)
            set_cell_margins(cell)
            cell.text = ""
            p = cell.paragraphs[0]
            r = p.add_run(h)
            set_run_font(r, size=9, bold=True, color=WHITE)
        for ri, row in enumerate(rows):
            wr = table.rows[ri + 1]
            prevent_row_split(wr)
            fill = WHITE if ri % 2 == 0 else ROW_ALT
            for i, val in enumerate(row):
                cell = wr.cells[i]
                set_cell_width(cell, col_widths[i])
                shade_cell(cell, fill)
                set_cell_margins(cell)
                cell.text = ""
                p = cell.paragraphs[0]
                r = p.add_run("" if val is None else str(val))
                set_run_font(r, size=8.5, color=SLATE)
        if caption:
            cap = self.doc.add_paragraph(caption, style="Caption")
        else:
            self.doc.add_paragraph().paragraph_format.space_after = Pt(8)
        return table

    def toc(self):
        p = self.doc.add_paragraph()
        run = p.add_run()
        r = run._r
        fld1 = OxmlElement("w:fldChar")
        fld1.set(qn("w:fldCharType"), "begin")
        instr = OxmlElement("w:instrText")
        instr.set(qn("xml:space"), "preserve")
        instr.text = ' TOC \\o "1-3" \\h \\z \\u '
        fld2 = OxmlElement("w:fldChar")
        fld2.set(qn("w:fldCharType"), "separate")
        run2 = OxmlElement("w:r")
        t = OxmlElement("w:t")
        t.text = "Right-click and choose Update Field in Microsoft Word to populate this table of contents."
        run2.append(t)
        fld3 = OxmlElement("w:fldChar")
        fld3.set(qn("w:fldCharType"), "end")
        r.append(fld1)
        r.append(instr)
        r.append(fld2)
        r.append(run2)
        r.append(fld3)
