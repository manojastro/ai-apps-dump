#!/usr/bin/env python3
"""X/Twitter Manifestation Community Intelligence Report — Word generator."""

from datetime import date
from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ROW_HEIGHT_RULE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn, nsdecls
from docx.shared import Inches, Pt, RGBColor, Cm, Emu, Twips
from docx.enum.style import WD_STYLE_TYPE

NAVY = RGBColor(0x1B, 0x36, 0x5D)
TEAL = RGBColor(0x2E, 0x75, 0xB6)
BODY = RGBColor(0x22, 0x22, 0x22)
MUTED = RGBColor(0x55, 0x55, 0x55)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ACCENT = "1B365D"
ROW_ALT = "F4F7FA"
HEADER_FILL = "1B365D"
ACCENT_FILL = "D6E3F0"
WARN_FILL = "F7E6C4"
GOOD_FILL = "E3F0E8"
BAD_FILL = "F8E0DE"


def set_run_font(run, name="Arial", size=11, bold=False, italic=False, color=BODY):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = color


def shade_cell(cell, fill):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    for child in tcPr.findall(qn("w:shd")):
        tcPr.remove(child)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def set_cell_borders(cell, color="CCCCCC", sz="4"):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), sz)
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        tcBorders.append(el)
    existing = tcPr.find(qn("w:tcBorders"))
    if existing is not None:
        tcPr.remove(existing)
    tcPr.append(tcBorders)


def set_cell_margins(cell, top=60, bottom=60, left=80, right=80):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, v in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        node = OxmlElement(f"w:{m}")
        node.set(qn("w:w"), str(v))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    existing = tcPr.find(qn("w:tcMar"))
    if existing is not None:
        tcPr.remove(existing)
    tcPr.append(tcMar)


def set_repeat_header(row):
    tr = row._tr
    trPr = tr.get_or_add_trPr()
    tblHeader = OxmlElement("w:tblHeader")
    tblHeader.set(qn("w:val"), "true")
    trPr.append(tblHeader)


def prevent_row_split(row):
    tr = row._tr
    trPr = tr.get_or_add_trPr()
    cant = OxmlElement("w:cantSplit")
    trPr.append(cant)


def set_table_width(table, width_in):
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else tbl.get_or_add_tblPr()
    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        tblPr.append(tblW)
    tblW.set(qn("w:w"), str(int(width_in * 1440)))
    tblW.set(qn("w:type"), "dxa")
    tblLayout = tblPr.find(qn("w:tblLayout"))
    if tblLayout is None:
        tblLayout = OxmlElement("w:tblLayout")
        tblPr.append(tblLayout)
    tblLayout.set(qn("w:type"), "fixed")


def set_col_widths(table, widths):
    """widths in inches."""
    table.autofit = False
    set_table_width(table, sum(widths))
    grid = table._tbl.find(qn("w:tblGrid"))
    if grid is not None:
        for i, w in enumerate(widths):
            grid_col = list(grid)[i]
            grid_col.set(qn("w:w"), str(int(w * 1440)))
    for row in table.rows:
        for i, w in enumerate(widths):
            cell = row.cells[i]
            cell.width = Inches(w)
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            tcW = tcPr.find(qn("w:tcW"))
            if tcW is None:
                tcW = OxmlElement("w:tcW")
                tcPr.append(tcW)
            tcW.set(qn("w:w"), str(int(w * 1440)))
            tcW.set(qn("w:type"), "dxa")


def add_hyperlink(paragraph, text, url, size=10, color=TEAL):
    part = paragraph.part
    r_id = part.relate_to(
        url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True
    )
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    new_run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    rStyle = OxmlElement("w:rStyle")
    rStyle.set(qn("w:val"), "Hyperlink")
    rPr.append(rStyle)
    color_el = OxmlElement("w:color")
    color_el.set(qn("w:val"), "2E75B6")
    rPr.append(color_el)
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rPr.append(u)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(int(size * 2)))
    rPr.append(sz)
    szCs = OxmlElement("w:szCs")
    szCs.set(qn("w:val"), str(int(size * 2)))
    rPr.append(szCs)
    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), "Arial")
    rFonts.set(qn("w:hAnsi"), "Arial")
    rPr.append(rFonts)
    new_run.append(rPr)
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    new_run.append(t)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)
    return hyperlink


def para(doc, text, size=11, bold=False, italic=False, color=BODY, space_after=8, space_before=0, align="left"):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.line_spacing = 1.15
    if align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "right":
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    elif align == "justify":
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold, italic=italic, color=color)
    return p


def mixed_para(doc, parts, space_after=8, justify=True):
    """parts: list of (text, kwargs)."""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = 1.15
    if justify:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for text, kwargs in parts:
        run = p.add_run(text)
        set_run_font(run, **kwargs)
    return p


def add_heading_styled(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.color.rgb = NAVY
        run.font.name = "Arial"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
        if level == 1:
            run.font.size = Pt(18)
        elif level == 2:
            run.font.size = Pt(14)
        else:
            run.font.size = Pt(12)
        run.bold = True
    h.paragraph_format.space_before = Pt(16 if level == 1 else 12)
    h.paragraph_format.space_after = Pt(8)
    return h


def add_hr(doc, color="2E75B6"):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(8)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "12")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color)
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p


def bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet")
    p.clear()
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = 1.12
    if level:
        p.paragraph_format.left_indent = Inches(0.5 + 0.25 * level)
    run = p.add_run(text)
    set_run_font(run, size=11)
    return p


def numbered(doc, text):
    p = doc.add_paragraph(style="List Number")
    p.clear()
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.space_before = Pt(0)
    run = p.add_run(text)
    set_run_font(run, size=11)
    return p


def callout(doc, title, body, fill=ACCENT_FILL):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_col_widths(table, [6.5])
    cell = table.cell(0, 0)
    shade_cell(cell, fill)
    set_cell_borders(cell, "2E75B6", "8")
    set_cell_margins(cell, 80, 80, 120, 120)
    cell.text = ""
    p = cell.paragraphs[0]
    r = p.add_run(title)
    set_run_font(r, size=11, bold=True, color=NAVY)
    p2 = cell.add_paragraph()
    r2 = p2.add_run(body)
    set_run_font(r2, size=10, color=BODY)
    p2.paragraph_format.space_after = Pt(0)
    doc.add_paragraph().paragraph_format.space_after = Pt(8)


def add_toc(doc):
    p = doc.add_paragraph()
    run = p.add_run()
    fldChar_begin = OxmlElement("w:fldChar")
    fldChar_begin.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.set(qn("xml:space"), "preserve")
    instrText.text = 'TOC \\o "1-2" \\h \\z \\u'
    fldChar_separate = OxmlElement("w:fldChar")
    fldChar_separate.set(qn("w:fldCharType"), "separate")
    fldChar_end = OxmlElement("w:fldChar")
    fldChar_end.set(qn("w:fldCharType"), "end")
    r = run._r
    r.append(fldChar_begin)
    r.append(instrText)
    r.append(fldChar_separate)
    placeholder = p.add_run("Right-click and choose Update Field to generate the table of contents in Microsoft Word.")
    set_run_font(placeholder, size=10, italic=True, color=MUTED)
    r2 = p.add_run()._r
    r2.append(fldChar_end)


def header_footer(section, header_text):
    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0]
    hp.clear()
    hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = hp.add_run(header_text)
    set_run_font(r, size=9, color=MUTED)
    r2 = hp.add_run("\tCommunity Intelligence Report")
    set_run_font(r2, size=9, color=MUTED)
    hp.paragraph_format.tab_stops.add_tab_stop(Inches(6.5), WD_TAB_ALIGNMENT.RIGHT)
    pPr = hp._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), "2E75B6")
    pBdr.append(bottom)
    pPr.append(pBdr)

    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0]
    fp.clear()
    fp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = fp.add_run("Anecdotes, not scientific proof.  |  Page ")
    set_run_font(r, size=9, color=MUTED)
    # PAGE field
    run = fp.add_run()
    fldChar1 = OxmlElement("w:fldChar")
    fldChar1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fldChar2 = OxmlElement("w:fldChar")
    fldChar2.set(qn("w:fldCharType"), "end")
    run._r.append(fldChar1)
    run._r.append(instr)
    run._r.append(fldChar2)
    set_run_font(run, size=9, color=MUTED)
    r3 = fp.add_run(" of ")
    set_run_font(r3, size=9, color=MUTED)
    run2 = fp.add_run()
    fldChar1b = OxmlElement("w:fldChar")
    fldChar1b.set(qn("w:fldCharType"), "begin")
    instrb = OxmlElement("w:instrText")
    instrb.set(qn("xml:space"), "preserve")
    instrb.text = " NUMPAGES "
    fldChar2b = OxmlElement("w:fldChar")
    fldChar2b.set(qn("w:fldCharType"), "end")
    run2._r.append(fldChar1b)
    run2._r.append(instrb)
    run2._r.append(fldChar2b)
    set_run_font(run2, size=9, color=MUTED)


def cell_text(cell, text, size=8, bold=False, color=BODY, fill=None, align="left"):
    cell.text = ""
    set_cell_margins(cell)
    set_cell_borders(cell)
    if fill:
        shade_cell(cell, fill)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = 1.05
    if align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold, color=color)
    return p


def header_row(table, labels, fill=HEADER_FILL):
    row = table.rows[0]
    set_repeat_header(row)
    prevent_row_split(row)
    for i, lab in enumerate(labels):
        cell_text(row.cells[i], lab, size=8, bold=True, color=WHITE, fill=fill, align="center")


def add_url_cell(cell, url, fill=None):
    cell.text = ""
    set_cell_margins(cell)
    set_cell_borders(cell)
    if fill:
        shade_cell(cell, fill)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    add_hyperlink(p, "Open post", url, size=8)


def page_break(doc):
    p = doc.add_paragraph()
    p.add_run().add_break()  # page break via runs
    # Use proper page break
    p._p.get_or_add_pPr()
    from docx.enum.text import WD_BREAK
    # clearer:
    # actually:
    last = doc.paragraphs[-1]
    run = last.runs[0] if last.runs else last.add_run()
    run._r.clear_content() if False else None


def add_page_break(doc):
    p = doc.add_paragraph()
    run = p.add_run()
    br = OxmlElement("w:br")
    br.set(qn("w:type"), "page")
    run._r.append(br)


# ---------------------------------------------------------------------------
# DATA
# ---------------------------------------------------------------------------

POSTS = [
    {
        "rank": 1,
        "author": "Fawn",
        "user": "moonlitfawnwtch",
        "id": "2099528101026009435",
        "date": "14 Sep 2026",
        "cat": "Law of Assumption / SP",
        "goal": "Specific person (ex) as devoted boyfriend",
        "tech": "Self-concept + decide + stop efforting",
        "method": "Discovered conscious manifesting Jan 2025 after a breakup. Made a list of 135 traits she wanted. Reached out; he wanted only friendship. After 2 months no-contact and 5 more months of efforting (videos, extra techniques), she stopped efforting and stood on one assumption: he is her devoted boyfriend. Visualized. When he broke no-contact she tried to 'normalize' it rather than treat it as a miracle.",
        "freq": "Ongoing assumption; previously heavy content consumption",
        "dur": "From Jan 2025; ~5 months efforting, then decision; +4 months to official relationship; ~6 months together at posting",
        "actions": "Reached out; later stopped extra techniques; continued ordinary life",
        "outcome": "He broke no-contact; asked her to be his girlfriend ~4 months later; reports ~6 months together and that he is 'obsessed' with her",
        "tips": "Stop stacking techniques; stick to one decided story; normalize the result when it arrives; do not contradict yourself after movement",
        "mistakes": "Overconsuming videos without applying; dismissing self-concept; efforting; going back and forth after first movement (which she says delayed the official relationship)",
        "ux": "Highly detailed first-person arc with timeline, inner state, and a clear 'what I changed' moment.",
        "replies": "Reply from @dittoarchivee: 'this gives me so much hope'.",
        "likes": 541, "replies_n": 3, "reposts": 26, "views": 7978, "bookmarks": 391,
        "eq": "High (first-person, timeline, method change). Unverifiable relationship claim; author offers coaching.",
        "conf": "Medium-high as a community case study; not proof of causation.",
    },
    {
        "rank": 2,
        "author": "4D",
        "user": "4DFairyLive",
        "id": "2090433910668722502",
        "date": "20 Aug 2026",
        "cat": "Habit + Action / Money / Career",
        "goal": "Easy contract-based second job / extra income for school",
        "tech": "Nonduality + identity of already having money + job applications",
        "method": "Wanted a second contract job for 2–3 years. Summer 2025 applied everywhere, got nothing, gave up, then read about nonduality. Stopped treating money as a scarce thing to chase. Did not do affirmations. Stated she wanted to save X before school. May 2026 got an offer for a July 2025 application. Was later cut from the project; assumed she could get another. Ignored Reddit comments that contracts take months.",
        "freq": "Not a technique schedule; identity shift plus prior applications",
        "dur": "Wanted 2–3 years; applications Summer 2025; offer May 2026; replacement offer in 2 weeks after being cut",
        "actions": "Applied widely in 2025; accepted contract; after layoff, did not publicly crash out; stayed available for another contract",
        "outcome": "Replacement offer at same pay in two weeks; still on it ~4 months later; monthly income above 2025 target; declined a simultaneous extra contract",
        "tips": "Stop relating to money as scarce; ignore other people's timelines; after a setback, assume you can get another; applications still happened",
        "mistakes": "Earlier: applying while pissed/desperate and then quitting the search",
        "ux": "Rare non-coach money story that includes failure, layoff, and action. Strongest career case in this sample.",
        "replies": "Thread is mostly the author's own continuation.",
        "likes": 143, "replies_n": 1, "reposts": 6, "views": 5019, "bookmarks": 81,
        "eq": "High. Combines inner shift with documented job-search behavior. Still anecdotal.",
        "conf": "High as a practical case; causation mixed (applications + delayed hiring + mindset).",
    },
    {
        "rank": 3,
        "author": "gus",
        "user": "stereonotes",
        "id": "2076068167244480897",
        "date": "11 Jul 2026",
        "cat": "Affirmations / Self-concept / Subliminals",
        "goal": "General manifestation; daily saturation process",
        "tech": "Robotic affirming + self-concept + subliminals",
        "method": "Not a fan of rigid routines except for manifestation. Works 6am–3pm so she saturates in free time (~4 hours/day claimed). Wake: 10 min self-concept affirming. Commute: keep affirming. Work: no active affirming. Shower: 'I have everything I want, everything I want wants me even more.' 7–11pm: subliminals in bed while affirming and scrolling Pinterest until sleep.",
        "freq": "Daily; ~4 hours claimed saturation around a full-time job",
        "dur": "Ongoing routine (not a one-off 30-day challenge)",
        "actions": "Keeps a job; household tasks after work; does not affirm during work hours",
        "outcome": "Presents this as 'what works for me'; later posted a success after 10 minutes of affirming before sleep (see rank 16)",
        "tips": "Fit practice around real work; protect work hours; morning self-concept; night saturation; keep it simple",
        "mistakes": "Implied: rigid routines that do not fit the person's life",
        "ux": "One of the few posts with clock-level routine detail. Reply asked whether to saturate 3 desperate desires at once.",
        "replies": "@Nisha4bm asked how to handle 3 anxious desires; @author_hs31181 asked for the exact affirmations.",
        "likes": 440, "replies_n": 3, "reposts": 33, "views": 9734, "bookmarks": 226,
        "eq": "High for method description; outcome of this specific post is process not a single result.",
        "conf": "Medium-high for 'how people actually practice'; lower for proving results.",
    },
    {
        "rank": 4,
        "author": "Reira",
        "user": "hazeleyesgrace",
        "id": "2081410601268691421",
        "date": "26 Jul 2026",
        "cat": "Self-concept / Visualization / Family",
        "goal": "Change how abusive/unsupportive parents treat her; SP visit welcomed",
        "tech": "New story + visualization of replacing the old story",
        "method": "Grew up restricted and criticized. Did not script every detail. Repeated: parents will do what she wants and treat her as loving/supportive. Visualized pushing the old story away like a movie and inserting a new one. Stopped waking up expecting the same pattern. Did not use a formal routine. Also assumed SP visit would be welcomed despite a time crunch.",
        "freq": "Throughout the day whenever 3D contradicted her; no timed ritual",
        "dur": "Not quantified in days; described as stubborn persistence while still living in the same house",
        "actions": "Continued living at home; later reports parents allowed travel/staying with SP",
        "outcome": "Claims parents now let her stay with SP, travel alone with him, eat as she wants, and value her work. Reply @lilisrealityy said she manifested the same parent change.",
        "tips": "Do not treat circumstances as a 'final boss'; give yourself the new story first; do not over-specify how; feed the mind the new story when 3D slaps you",
        "mistakes": "Giving outside circumstances too much power; expecting the old pattern every morning",
        "ux": "Detailed family case. Coaching account. Abuse context should not be read as 'just think differently' medical/safety advice.",
        "replies": "@lilisrealityy: independently claimed a similar parent-behavior change.",
        "likes": 392, "replies_n": 5, "reposts": 51, "views": 10976, "bookmarks": 224,
        "eq": "Medium-high detail; coaching funnel; family outcomes unverifiable.",
        "conf": "Medium. Independent reply is interesting but still anecdotal.",
    },
    {
        "rank": 5,
        "author": "Taz",
        "user": "ctrlpinkz",
        "id": "2083684557711098367",
        "date": "1 Aug 2026",
        "cat": "Career / Affirmations + Action",
        "goal": "Six-figure commissions, resume experience, good pay via a Sony-owned awards-show project",
        "tech": "Identity affirming until it felt natural",
        "method": "Already working as a marketer. Affirmed three outcomes (company earning six-figure commissions, great resume experience, good pay) 'for a bit' until she naturally thought as the person who had it. Then a deal/negotiation appeared. Circumstances shifted from limited to full control and pay from five figures toward six. 18-month project.",
        "freq": "Affirmed 'for a bit' until identity felt natural — not a counted daily quota",
        "dur": "Short affirming period relative to career timeline; 18-month project after",
        "actions": "Already employed in marketing; negotiations, campaigns, interviews, documentary, celebrity networking are job tasks",
        "outcome": "Reports officially working for an awards show owned by Sony Music; higher pay; long project",
        "tips": "Affirm until it becomes natural thought, not a chore; career manifestations often ride on a job you already have",
        "mistakes": "Not stated",
        "ux": "Career win with real professional channel. Coaching bio. Screenshot method is first-person.",
        "replies": "Congrats replies; one user asked how to manifest moving to America.",
        "likes": 377, "replies_n": 5, "reposts": 25, "views": 8971, "bookmarks": 168,
        "eq": "Medium-high. Action + job already in place is a confounder.",
        "conf": "Medium. Stronger as 'identity + existing career leverage' than as magic.",
    },
    {
        "rank": 6,
        "author": "Puffie",
        "user": "kook_puff_222",
        "id": "2097337023640248330",
        "date": "8 Sep 2026",
        "cat": "SP / Subliminals / Affirmations",
        "goal": "A school SP who did not know her name to become obsessed with her",
        "tech": "Subliminals + visualization + affirming + self-concept; later assumption only",
        "method": "3 years ago, SP did not know her name. Set intention he would love her. Used subliminals, visualized him loving her, affirmed they always meet in hallways. No initial 3D results. When doubts came she told herself she was attractive/worth it. Then saw glances/blushing. Stopped subliminals due to schedule; kept assuming he already loved her. In May he confessed.",
        "freq": "Frequent affirming; subliminals until schedule made her stop",
        "dur": "Not a precise day count; from 'no results initially' to hallway signs to May confession",
        "actions": "School proximity (hallways) is a major practical channel",
        "outcome": "Signs, then confession in May; she says time-to-result is not a rule",
        "tips": "Self-concept first; persist with no 3D; someone else's 1-month timeline is not yours; you can drop a technique if the assumption is in place",
        "mistakes": "Not dwelling on whether he would fall for her",
        "ux": "Clear method sequence. Coaching/psychic bio. SP-from-thin-air adjacent (he was in her school).",
        "replies": "@sonagwaz: 'this is my situation rn'.",
        "likes": 571, "replies_n": 4, "reposts": 22, "views": 14408, "bookmarks": 398,
        "eq": "Medium-high first-person; coaching account; school-proximity confounder.",
        "conf": "Medium.",
    },
    {
        "rank": 7,
        "author": "brigitté",
        "user": "iamallthatis_",
        "id": "2027415420727157072",
        "date": "27 Feb 2026",
        "cat": "Self-concept / Visualization / Detachment",
        "goal": "General method; also job-offer identity in a related post",
        "tech": "Morning/night visualization + self-concept rampage + 5-min saturation for hard desires",
        "method": "Wakes deciding it will be the best day. Rampages self-concept during morning routine on autopilot. Lives the day present. If the desire arises, thinks as if she has it, then drops it. Intentional visualization at start and end of day. For 'hard' desires, 5-minute saturation/rampage bursts. Reminds herself she is 'operant power'.",
        "freq": "Daily morning + night; optional 5-min bursts",
        "dur": "Described as her ongoing method",
        "actions": "Ordinary day; not a ritual-only life",
        "outcome": "Method post; related Jan 2026 post uses the same approach for imagining multiple job offers",
        "tips": "Live normally; do not debate the affirmation; extra saturation only for desires that feel hard to accept",
        "mistakes": "Not stated",
        "ux": "Highly bookmarked method post (389 bookmarks / 898 likes).",
        "replies": "Not available on fetch (0 listed).",
        "likes": 898, "replies_n": 0, "reposts": 80, "views": 22629, "bookmarks": 389,
        "eq": "High for practice description; outcome of this post is method not a single event.",
        "conf": "Medium-high as a community-standard routine.",
    },
    {
        "rank": 8,
        "author": "Jas",
        "user": "papercups111_",
        "id": "2021649996479869203",
        "date": "11 Feb 2026",
        "cat": "Visualization before sleep",
        "goal": "Kiss with then-friend at a specific place",
        "tech": "Nightly first-person visualization, then forgetting",
        "method": "Did not know LOA. Every night before sleep imagined kissing him at a specific place because it felt good. Eventually forgot about it. Two months later they went out as friends and kissed at that exact place.",
        "freq": "Every night before sleep, until she forgot",
        "dur": "About two months from visualization to event",
        "actions": "They already had a friendship and went out; visualization was not the only variable",
        "outcome": "Kiss at the imagined location, described as better than imagined",
        "tips": "Feeling good in the scene; not obsessing; forgetting",
        "mistakes": "Not stated",
        "ux": "Classic 'unintentional SATS-like' story. Coaching bio. High narrative clarity.",
        "replies": "Not available (0 listed).",
        "likes": 207, "replies_n": 0, "reposts": 8, "views": 5306, "bookmarks": 43,
        "eq": "Medium-high story quality; friendship + going out is a large confounder.",
        "conf": "Medium. Matches mental-rehearsal + selective memory as easily as metaphysics.",
    },
    {
        "rank": 9,
        "author": "Rory",
        "user": "selfconqueen",
        "id": "2069391865506385943",
        "date": "23 Jun 2026",
        "cat": "Law of Assumption / Scripting / Decide",
        "goal": "Multiple small and large: tea, snow, lips, SP, course, job, car, grades",
        "tech": "Repetition, persisting, deciding, saturating, scripting — no visualization (aphantasia-like)",
        "method": "Cannot visualize. Combo of decide/persist/script. Examples: sister making tea unasked; Christmas snow lasting a week despite forecast; fuller lips with only usual chapstick; SP confession; low-enrollment course still ran; job offered after going to someone else then she rejected it; car; unprompted beauty compliment; A in weakest subject (math); SP 'I love you' and 'I think of you every day'.",
        "freq": "Not clocked; 'accepted as fact'",
        "dur": "Assorted, not one experiment window",
        "actions": "Applied for a job; attended school; used chapstick as usual",
        "outcome": "List of claimed hits; low engagement (1 like) — valuable because it is a personal log, not a viral funnel",
        "tips": "Visualization is optional; deciding/accepting as fact is her lever",
        "mistakes": "Not stated",
        "ux": "Independent-feeling log. Several claims (weather, anatomy) are high-hype and low-evidence.",
        "replies": "Thread is self-replies listing items.",
        "likes": 1, "replies_n": 1, "reposts": 0, "views": 28, "bookmarks": 1,
        "eq": "Medium for method diversity; low for extraordinary claims (weather, lips, grades) without corroboration.",
        "conf": "Low-medium overall; useful as a 'no visualization' data point.",
    },
    {
        "rank": 10,
        "author": "mi",
        "user": "miluvin444",
        "id": "2099424708752199998",
        "date": "14 Sep 2026",
        "cat": "Opportunity / Money / Persist",
        "goal": "Bruno Mars seats after a ₱61K ticket scam; extra show; money returning",
        "tech": "Affirm and persist; 'circumstances don't matter'",
        "method": "Lost ₱61K to a fake ticket service. Was at the beach during pre-sale; on a film set (lead actress) during general sale; site said sold out. Still assumed seats. A friend she had not spoken to in a while secured tickets. Also claims an extra show date and money flowing back from other places. Explicit extra lesson: be kind to people.",
        "freq": "Persist in the decision; not a timed ritual in the post",
        "dur": "Around a concert on-sale window",
        "actions": "Friend helped during sale; she was working a film production; networking/kindness mentioned",
        "outcome": "Desired seats; extra show; reports money returning; free food at a birthday",
        "tips": "Affirm and persist; never go back to the old story; be kind — help can be unplanned; circumstances (scam, sold out, being busy) are not treated as vetoes",
        "mistakes": "Not stated as self-critique",
        "ux": "Concrete logistics + a practical non-mystical channel (a friend bought tickets). Coaching account.",
        "replies": "@princess5160: 'i got mine tooo!!'",
        "likes": 141, "replies_n": 4, "reposts": 13, "views": 4144, "bookmarks": 31,
        "eq": "Medium-high for the ticket story; 'extra show manifested' is much weaker.",
        "conf": "Medium. Friend assistance is a clear behavioral path.",
    },
]

POSTS += [
    {
        "rank": 11,
        "author": "dian pratama",
        "user": "godoverunivers",
        "id": "2094521130933792789",
        "date": "31 Aug 2026",
        "cat": "Failure / Critique / Habit + Action",
        "goal": "Revenue / not staying broke",
        "tech": "Compared 'universe' manifestation vs God-directed practice + action",
        "method": "Says manifestation 'worked' zero times in 2 years. Attributes apparent hits to confirmation bias and behavior change (calmer, more decisive, consistent action). Test: 2 years pointed at 'the universe' vs 4 months pointed at God. Practice barely changed; 'the address did.' What he says actually changes outcomes: regulated nervous system + consistent scripted action.",
        "freq": "Multi-year then 4-month comparison",
        "dur": "2 years vs 4 months",
        "actions": "Consistent scripted action; nervous-system regulation (self-report)",
        "outcome": "Universe-directed: $0 moved. God-directed: $250,000 revenue (self-report). Bio also sells this narrative.",
        "tips": "Do not confuse coincidence-noticing with a force; behavior change is the active ingredient",
        "mistakes": "Pointing practice at an impersonal universe for 2 years with no money movement",
        "ux": "Rare explicit failure + alternative explanation. Low engagement. Funnel bio.",
        "replies": "None.",
        "likes": 1, "replies_n": 0, "reposts": 0, "views": 7, "bookmarks": 0,
        "eq": "Medium. Valuable critique; $250k and the controlled 'test' are unverified and commercially framed.",
        "conf": "Medium for the psychological critique; low for the dollar comparison.",
    },
    {
        "rank": 12,
        "author": "Jack Moses",
        "user": "jackmoses777",
        "id": "2091099234720494026",
        "date": "22 Aug 2026",
        "cat": "Habit + Action / Critique",
        "goal": "Financial success (general)",
        "tech": "None — anti-technique for business",
        "method": "Argument, not a ritual: manifestation, letting go, and affirmations will not produce financial success unless you create something real people want to buy.",
        "freq": "N/A",
        "dur": "N/A",
        "actions": "Build a product people want",
        "outcome": "Position statement; 97 likes, 6 replies",
        "tips": "Create a real offer",
        "mistakes": "Using manifestation as a substitute for a marketable product",
        "ux": "Outside the LOA bubble; important counterweight.",
        "replies": "Discussion present (6 replies); full reply text not fully captured.",
        "likes": 97, "replies_n": 6, "reposts": 4, "views": 2610, "bookmarks": 8,
        "eq": "High as a community-critique data point.",
        "conf": "High that this view exists among builders; not a success experiment.",
    },
    {
        "rank": 13,
        "author": "Affirm And Align",
        "user": "AffirmAndAlign",
        "id": "2095949768744939968",
        "date": "4 Sep 2026",
        "cat": "Advice / Anti-stacking",
        "goal": "Better coaching/advice quality",
        "tech": "Context-first instead of prescribing SATS/10k affirmations/self-concept/detach all at once",
        "method": "Observes that struggling users are immediately told to affirm 10k times, work on self-concept, do SATS every night, stop checking 3D, detach, saturate more — before anyone asks what they believe, what they already do, what they enjoy, how much time they have, or what silence means to them. Says this is why routines become ridiculous stacks of seven methods.",
        "freq": "N/A — meta-advice",
        "dur": "N/A",
        "actions": "Ask diagnostic questions first",
        "outcome": "Widely bookmarked relative to likes (19 bookmarks / 54 likes)",
        "tips": "Match technique to the person; do not add methods on top of exhaustion",
        "mistakes": "Prescribing before understanding; stacking every popular method",
        "ux": "Best 'why people fail' diagnosis in the sample. Coaching account.",
        "replies": "0 listed.",
        "likes": 54, "replies_n": 0, "reposts": 1, "views": 1797, "bookmarks": 19,
        "eq": "High as practitioner-meta; not a personal success trial.",
        "conf": "High that method-stacking is a real community failure mode.",
    },
    {
        "rank": 14,
        "author": "H",
        "user": "CYBILL_SHEPARD",
        "id": "2098836903176909043",
        "date": "12 Sep 2026",
        "cat": "Affirmations / Negative experience",
        "goal": "Critique of robotic affirming",
        "tech": "Robotic affirming (criticized)",
        "method": "Direct statement: a tiny percentage might exhaust the analytical mind via repetition; for ~95% it spikes cortisol, creates OCD loops, and cements the trauma of not having the desire.",
        "freq": "N/A",
        "dur": "N/A",
        "actions": "N/A",
        "outcome": "Negative appraisal, not a numbered experiment",
        "tips": "Do not treat robotic affirming as universally safe",
        "mistakes": "Using RA as the only right way; looping on lack",
        "ux": "Important minority report inside a RA-heavy community.",
        "replies": "In a larger conversation (parent tweet).",
        "likes": 0, "replies_n": 1, "reposts": 0, "views": 19, "bookmarks": 0,
        "eq": "Low-medium (opinion, tiny engagement) but thematically important.",
        "conf": "Low as prevalence claim ('95%'); medium as a reported harm pattern.",
    },
    {
        "rank": 15,
        "author": "demi",
        "user": "404DEMI",
        "id": "2097207460419321901",
        "date": "8 Sep 2026",
        "cat": "Detachment / Decide",
        "goal": "General; 'it's never not worked for me'",
        "tech": "Decide, then stop attending to it",
        "method": "Explicitly not repetition, scripting, saturating, or visualizing. Decides she wants it, receives it. Works best when she does not pay extra attention. Lets the old story play out without thinking twice. 'I decide…then the dominos fall.' Follow-up: everything she manifested quickly used that method.",
        "freq": "Once decided, no ongoing technique",
        "dur": "Described as quick/effortless when using this, vs extra-attention methods",
        "actions": "Not specified",
        "outcome": "Global claim of never failing; no single dated result in the post",
        "tips": "If it is already yours, stop 'manifesting' it",
        "mistakes": "Relentless technique as a substitute for a decision",
        "ux": "Clean statement of the 'decide and drop' school. Low-medium engagement.",
        "replies": "Self-reply elaborating the method.",
        "likes": 49, "replies_n": 2, "reposts": 3, "views": 1464, "bookmarks": 13,
        "eq": "Medium. Clear method; unfalsifiable 'never failed' claim.",
        "conf": "Medium as a community pattern; low as proof.",
    },
    {
        "rank": 16,
        "author": "gus",
        "user": "stereonotes",
        "id": "2099241434335326663",
        "date": "13 Sep 2026",
        "cat": "Robotic affirming / Sleep",
        "goal": "Unspecified desire (success story)",
        "tech": "Robotic affirming 10 minutes before sleep",
        "method": "Posted a success after affirming only 10 minutes before sleeping. Says she loves robotic affirming and the law of assumption. Complements her longer routine post.",
        "freq": "Before sleep; 10 minutes in this instance",
        "dur": "Single session claimed",
        "actions": "Not specified",
        "outcome": "'Another success story' — result not named in text (video/GIF attached)",
        "tips": "Short pre-sleep RA can be enough",
        "mistakes": "Not stated",
        "ux": "High views (20.5k). Outcome details live in media, not text.",
        "replies": "0 listed.",
        "likes": 355, "replies_n": 0, "reposts": 17, "views": 20520, "bookmarks": 63,
        "eq": "Medium. Timebox is useful; unnamed result reduces evidence.",
        "conf": "Medium for popularity of pre-sleep RA; low for the specific win.",
    },
    {
        "rank": 17,
        "author": "Client via strawberry",
        "user": "strawbe44ym1lk",
        "id": "2098071095333261748",
        "date": "10 Sep 2026",
        "cat": "Affirmations / Self-concept / Appearance",
        "goal": "Timetable, shorter school day, dream body, friends, beauty, concert",
        "tech": "Morning and pre-sleep self-concept affirming; drop chasing",
        "method": "Client DM screenshots. Affirmed good timetable; early train; teachers missing. Affirmed 'everyone remembers my name, my beauty struck people.' Claimed dream body without sport/dieting after previously counting calories and exercising (lost 2kg in a week after already losing 10kg). Toxic friend left after 'I only have amazing friends.' Morning anxiety ('where is my manifestation?') stopped after SC affirming morning and before sleep. Also concert: 'oh seems cool, anyway I'm going.'",
        "freq": "Every morning and before sleep for self-concept, per client",
        "dur": "During a coaching period; body/school examples described as recent/this week",
        "actions": "Had previously dieted/exercised; later reports eating junk and not exercising",
        "outcome": "List of small and large claimed hits including appearance and weight",
        "tips": "SC morning and night; stop asking where it is; assume small daily events",
        "mistakes": "Chasing manifestations; morning anxiety checking",
        "ux": "Coaching testimonial screenshots. High bookmarks. Health claims should be treated skeptically.",
        "replies": "0 listed.",
        "likes": 672, "replies_n": 0, "reposts": 38, "views": 7970, "bookmarks": 265,
        "eq": "Low-medium. Second-hand coaching testimonial; several medically implausible claims.",
        "conf": "Low for body/appearance; medium for 'stop chasing / morning+night SC' as a felt shift.",
    },
    {
        "rank": 18,
        "author": "Power to Manifest",
        "user": "PowerManif14522",
        "id": "2010264494304551416",
        "date": "11 Jan 2026",
        "cat": "SP / Living in the end",
        "goal": "SP contact after 2 months of silence",
        "tech": "Flip the script; become the version that expects contact; no chasing",
        "method": "Two months no texts/calls. Did not wait/hope; decided. Did not chase, stalk, or force action. He called while she was asleep, asked why they had not talked, later complimented her profile, called again, texted 'call me when you're free.' Thread ends with a coaching CTA.",
        "freq": "Consistency in the new decision (not quantified)",
        "dur": "2 months of silence then contact",
        "actions": "No chasing (self-report)",
        "outcome": "Phone call and continued contact (self-report)",
        "tips": "Circumstances/time/silence are not failure; expect contact; energy over words",
        "mistakes": "Waiting/hoping rather than deciding",
        "ux": "Very high views (78k) and bookmarks. Hard coaching funnel. Thin on exact daily practice.",
        "replies": "7 replies; thread is mostly the author's numbered posts.",
        "likes": 895, "replies_n": 7, "reposts": 48, "views": 78695, "bookmarks": 662,
        "eq": "Medium. Popular SP template; method is slogan-level; CTA reduces independence.",
        "conf": "Low-medium.",
    },
    {
        "rank": 19,
        "author": "Zeion",
        "user": "ibentreality",
        "id": "2095491246924161358",
        "date": "3 Sep 2026",
        "cat": "Visualization / Money / Living in the end",
        "goal": "Make a large income feel normal",
        "tech": "Imagine boring Tuesday AFTER the money, not the arrival moment",
        "method": "If $50k feels too big, do not imagine receiving it. Imagine post-money problems: which account, hiring an accountant, not needing another client, paying upfront, Christmas gifts. Arrival-scene visualization keeps money feeling like a once-in-a-lifetime event.",
        "freq": "Imagination exercise (not scheduled in post)",
        "dur": "N/A",
        "actions": "Not specified",
        "outcome": "Technique post; @alignedbysource replied she had manifested money several times but not kept it constant and recognized the connection",
        "tips": "Normalize the after, not the jackpot moment",
        "mistakes": "Only visualizing the dramatic arrival",
        "ux": "481 likes / 234 bookmarks. Coaching bio. One of the most practical visualization tweaks.",
        "replies": "@baezdenise3 will try it; @ngc3372_ asked if it works for any desire; @alignedbysource added a keeping-money problem.",
        "likes": 481, "replies_n": 2, "reposts": 43, "views": 7335, "bookmarks": 234,
        "eq": "High as a method explanation; outcome is indirect (reply).",
        "conf": "Medium-high that this 'after-state' cue is widely found useful.",
    },
    {
        "rank": 20,
        "author": "JUNI",
        "user": "OHSOVICTORIOUS_",
        "id": "1954963748424389060",
        "date": "11 Aug 2025",
        "cat": "Self-concept / Detachment",
        "goal": "Stop 'slow' manifestation",
        "tech": "Stop checking; think in your favor 24/7 (upgrade the default loop)",
        "method": "Argues people are not manifesting slowly; they are running old code. Subconscious always manifests dominant thoughts. She stopped checking for results and started thinking in her favor constantly; then things felt inevitable rather than slow.",
        "freq": "24/7 dominant-thought framing",
        "dur": "Not dated to a result window",
        "actions": "Stop checking",
        "outcome": "Claims switch from slow to inevitable; no single external event named",
        "tips": "Checking keeps old assumptions in charge",
        "mistakes": "Interpreting 'nothing happening' as proof it is not working",
        "ux": "588 likes / 276 bookmarks. Coaching + affiliate codes in bio.",
        "replies": "Unroll request.",
        "likes": 588, "replies_n": 2, "reposts": 27, "views": 18962, "bookmarks": 276,
        "eq": "Medium. Influential framing; low event-level evidence.",
        "conf": "Medium that 'stop checking' is a core community prescription.",
    },
]
POSTS += [
    {
        "rank": 21,
        "author": "KULTRA",
        "user": "Levariousx",
        "id": "2094780236164366421",
        "date": "1 Sep 2026",
        "cat": "Visualization / Mental rehearsal",
        "goal": "Performance, skill, self-belief, less hesitation",
        "tech": "Morning repetitions of a successful day; replay past success memories",
        "method": "Every morning mentally repeats a successful day, tasks completed, effortless feeling. Short bursts of what the subconscious wants today. Replays past memories of success/confidence and pairs them with today's image (classical conditioning language). Claims less hesitation, procrastination, decision fatigue.",
        "freq": "Every morning on waking",
        "dur": "Ongoing practice; 'the more I practice'",
        "actions": "Skill practice implied ('arms move naturally')",
        "outcome": "Self-reported smoother days and stronger self-belief — not an external jackpot",
        "tips": "Pair emotion with image; use past success as the feeling source",
        "mistakes": "Not stated",
        "ux": "771 likes / 545 bookmarks. Closest post to sports psychology / implementation rehearsal.",
        "replies": "2 listed, not fully captured.",
        "likes": 771, "replies_n": 2, "reposts": 73, "views": 30749, "bookmarks": 545,
        "eq": "Medium-high as a mental-rehearsal protocol; commercial 'visual hypnosis' bio.",
        "conf": "Medium-high that morning rehearsal is a durable practice; aligned with known psych literature.",
    },
    {
        "rank": 22,
        "author": "Chihiro + replies",
        "user": "spiritchihiro",
        "id": "2092594249795793003",
        "date": "26 Aug 2026",
        "cat": "Community methods dump",
        "goal": "Collect 'unhinged' hacks",
        "tech": "Many: decide; song+one scene; affirm then forget; sleep recording; live your life",
        "method": "Prompt post (2,878 likes, 1,445 bookmarks, 173k views). Highest-signal replies: @nsh11 decide X will happen and enjoy 3D catching up; @Bwitchybabe one song + one scene on loop (also used to manifest a dream date); @Disaffirmer affirm like crazy then forget; @tokkiswith affirm then detach and it smacks you; @soultoscreen listen to a recording of herself talking about the dream as already happened before sleep; @catarinaa_tc live your life, do not make manifestation your life; @yaznoirxo playfully interact with 3D knowing it will change.",
        "freq": "Varies by reply",
        "dur": "Varies",
        "actions": "Several replies emphasize living normally",
        "outcome": "Crowd-sourced techniques rather than one story",
        "tips": "See method field — the cluster is decide / saturate / detach / live",
        "mistakes": "Making manifestation your whole life (Portuguese reply)",
        "ux": "Best single snapshot of 2026 LOA-Twitter folk practice.",
        "replies": "16 replies; several quoted above.",
        "likes": 2878, "replies_n": 16, "reposts": 112, "views": 173381, "bookmarks": 1445,
        "eq": "High as community-consensus evidence; low as proof any hack works.",
        "conf": "High for 'what people recommend to each other'.",
    },
    {
        "rank": 23,
        "author": "marr",
        "user": "raiinmarr",
        "id": "2091680336799273208",
        "date": "24 Aug 2026",
        "cat": "Visualization / Mind movie / Affirmations",
        "goal": "SP (and concentration while affirming); claims immediate fulfillment while making it",
        "tech": "DIY mind movie: written affs + TTS + images/video/songs + optional Dispenza/theta track",
        "method": "Wrote SP affirmations, converted to speech, gathered images/videos/songs that create the emotion of already having it, edited into a personal video, added a Joe Dispenza 'mind movie' YouTube layer or theta waves. Rationale: brain does not distinguish present vs future; visualization is remembering you already have it. Stresses feeling and consistency.",
        "freq": "Not specified beyond using the movie to concentrate",
        "dur": "Claims it fulfilled immediately while she was making it",
        "actions": "Production work (editing)",
        "outcome": "Vague 'it fulfilled immediately' — SP not evidenced in text",
        "tips": "Make it enjoyable; feeling is the point; constancy",
        "mistakes": "Not stated",
        "ux": "Best how-to for mind movies in this sample. 69 bookmarks.",
        "replies": "Thread is instructional self-replies.",
        "likes": 64, "replies_n": 1, "reposts": 5, "views": 4923, "bookmarks": 69,
        "eq": "High for method; low for the instantaneous-result claim.",
        "conf": "Medium.",
    },
    {
        "rank": 24,
        "author": "spirituel mommy",
        "user": "divaspiritcleo",
        "id": "2099785294795203035",
        "date": "15 Sep 2026",
        "cat": "Neville / SATS (instructional)",
        "goal": "Teach SATS as day 3 of a 30-day school",
        "tech": "SATS: 5–20 second first-person scene proving the wish is fulfilled, 3–5 minutes before sleep",
        "method": "Pick a short AFTER scene (seeing the number, ordinary healthy-relationship moment, hearing 'congratulations', looking at a view). First person. Repeat 3–5 minutes in the drowsy state. Do not ask how. Author explicitly says SATS is not a scientifically guaranteed method; they use it as focus and self-concept work. Related 14 Sep post teaches Living in the End with the question: if it were done, what would today-me do differently?",
        "freq": "Nightly in the 30-day program",
        "dur": "3–5 minutes; scene 5–20 seconds",
        "actions": "Daytime living-in-the-end choices in the companion post",
        "outcome": "Instructional, not a personal result",
        "tips": "Short proof scene; drowsy state; feel it; do not check",
        "mistakes": "Focusing on lack language; asking how",
        "ux": "Unusually honest disclaimer for this niche. Coaching/guide bio.",
        "replies": "2 on the SATS post.",
        "likes": 18, "replies_n": 2, "reposts": 0, "views": 1432, "bookmarks": 15,
        "eq": "High as a clear SATS protocol; N/A as a success story.",
        "conf": "High that this is how SATS is taught in 2026; not evidence it causes events.",
    },
    {
        "rank": 25,
        "author": "Skit",
        "user": "skitskite",
        "id": "2093782794757460092",
        "date": "29 Aug 2026",
        "cat": "SATS / Success claim",
        "goal": "Money, people, messages, apologies, jobs — 'everything'",
        "tech": "SATS ('has never failed me')",
        "method": "Reply to a Spanish SP-how-to. Says use SATS, it has never failed, manifested money, people, messages, apologies, jobs; at first it scared her how much came true. Loves Neville.",
        "freq": "Not specified",
        "dur": "Lifetime claim ('never failed')",
        "actions": "Not specified",
        "outcome": "Global success claim, no single dated case",
        "tips": "Use SATS",
        "mistakes": "Not stated",
        "ux": "Strong sentiment, weak protocol detail. Parent viral post has 3.5k likes.",
        "replies": "Conversation around SP ethics in parent post.",
        "likes": 1, "replies_n": 2, "reposts": 0, "views": 272, "bookmarks": 3,
        "eq": "Low-medium. First-person enthusiasm without a reconstructable experiment.",
        "conf": "Low.",
    },
    {
        "rank": 26,
        "author": "Cami (reposting a revision story)",
        "user": "Camsubs777",
        "id": "2092054817485009400",
        "date": "25 Aug 2026",
        "cat": "Revision / Reality shifting",
        "goal": "Revise an abusive argument / living situation / appearance",
        "tech": "Neville-style revision of a memory the same night",
        "method": "Screenshots of @gahdayummm. After an argument and being grounded, she revised the memory so the caregiver kicked her out, she had desired appearance, called desired (scripted) parents, they booked a hotel. She fell asleep and woke to the same date as the argument day, with claimed appearance change and hotel outcome. Trigger warning: abuse.",
        "freq": "One night revision",
        "dur": "Overnight / 'same date' claim",
        "actions": "Hotel booked because parents were on another continent (her PS)",
        "outcome": "Hotel stay and claimed appearance change; later 'they've come to get me'",
        "tips": "Don't give up (caption)",
        "mistakes": "Not stated",
        "ux": "274 likes. Extraordinary and medically/physically implausible elements. Abuse context.",
        "replies": "0 listed.",
        "likes": 274, "replies_n": 0, "reposts": 26, "views": 3214, "bookmarks": 129,
        "eq": "Low as evidence of revision altering physical reality. Medium as a specimen of revision belief.",
        "conf": "Very low for supernatural revision; do not treat as a safety plan for abuse.",
    },
    {
        "rank": 27,
        "author": "Coco",
        "user": "cocomanifest_",
        "id": "2086807124005523458",
        "date": "10 Aug 2026",
        "cat": "Health (third-party)",
        "goal": "Others' health: ICU, cancer, diabetes",
        "tech": "Assume they are healthy regardless of 3D",
        "method": "Always tells herself people around her are healthy no matter what 3D shows. Claims friend's dad out of ICU, uncle cancer-free, revised father's diabetes. Says none took long.",
        "freq": "Ongoing assumption",
        "dur": "'None of these took a long time'",
        "actions": "Not described (no mention of medical care)",
        "outcome": "Three third-party health claims",
        "tips": "Ignore 3D on health",
        "mistakes": "Not stated",
        "ux": "Coaching account. These claims are in the 'treat skeptically / do not replace care' bin.",
        "replies": "2 listed.",
        "likes": 205, "replies_n": 2, "reposts": 17, "views": 2978, "bookmarks": 49,
        "eq": "Low. Third-party medical claims, no clinical detail, coaching funnel.",
        "conf": "Very low. Do not use as health advice.",
    },
    {
        "rank": 28,
        "author": "Jordan Crowder",
        "user": "digijordan",
        "id": "2088365090084925941",
        "date": "14 Aug 2026",
        "cat": "Embodiment / Mistake",
        "goal": "Name the biggest manifestation mistake",
        "tech": "'Make it ICY then turn your life into a freezer' (embodiment / make it tangible)",
        "method": "Video (3 minutes). Text: biggest mistake is not making the desire icy/solid in the body/life. Reply @Tis1LeClerc: make it tangible by truly feeling/believing until the body trembles. Long skeptical reply @gangatoday1: this is thought → decision → action, not mystical manifestation; teachers often lack the 'how'.",
        "freq": "N/A",
        "dur": "N/A",
        "actions": "Reply thread emphasizes action space after thought/decision",
        "outcome": "267 likes, 207 bookmarks, 14 replies — useful debate",
        "tips": "Feel it until it is bodily real; critics: then act",
        "mistakes": "Leaving the desire as a vague wish",
        "ux": "Crosses manifestation and performance psychology. Best skeptical reply in-sample.",
        "replies": "See method; @LifeExplorer called the analogy phenomenal.",
        "likes": 267, "replies_n": 14, "reposts": 23, "views": 10707, "bookmarks": 207,
        "eq": "Medium. Video not fully transcribed here; replies are high value.",
        "conf": "Medium.",
    },
    {
        "rank": 29,
        "author": "Mister Unknown",
        "user": "mr404xxx",
        "id": "2091168050414281215",
        "date": "22 Aug 2026",
        "cat": "Anti-system / Decide-expect-live",
        "goal": "Critique of 369, vision boards, courses",
        "tech": "Decide. Expect. Live your life.",
        "method": "Quote-tweet of a long article (@paradeevic). Argument: 4-year-olds get cookies without 369. After learning 'the technique,' results get worse. Months of angel numbers, thought-policing, 6am scripting lose to expecting the thing and going about your day. Beginner and master do the same thing. You cannot sell 'stop trying so hard' as a $497 course.",
        "freq": "N/A",
        "dur": "N/A",
        "actions": "Live your life",
        "outcome": "Argument post; parent article 1.55M views",
        "tips": "Drop the system; decide and expect",
        "mistakes": "Over-systematizing; buying courses; thought-auditing",
        "ux": "Sharp counter to numbered methods. Not a personal 30-day log.",
        "replies": "0 on this post.",
        "likes": 0, "replies_n": 0, "reposts": 0, "views": 147, "bookmarks": 0,
        "eq": "Medium as critique (parent article is the real artifact).",
        "conf": "Medium-high that technique-obsession is a known trap.",
    },
    {
        "rank": 30,
        "author": "R793",
        "user": "sethmanifests",
        "id": "2097931073510384027",
        "date": "10 Sep 2026",
        "cat": "Mistake / Checking",
        "goal": "Separate manifesting from monitoring",
        "tech": "Stop 24/7 checking",
        "method": "You affirm then check, visualize then check, decide then check. Each check is a chance to doubt. Give yourself peace; do not monitor 24/7.",
        "freq": "N/A",
        "dur": "N/A",
        "actions": "Reduce monitoring",
        "outcome": "Advice post",
        "tips": "Checking is a different activity from the practice",
        "mistakes": "Constant result-monitoring",
        "ux": "Coaching account. Clean statement of the #1 community mistake.",
        "replies": "0.",
        "likes": 39, "replies_n": 0, "reposts": 4, "views": 662, "bookmarks": 6,
        "eq": "Medium as advice; triangulates with many other posts.",
        "conf": "High that checking is the most-named problem.",
    },
]
POSTS += [
    {
        "rank": 31,
        "author": "Yatziri",
        "user": "dollymanifest",
        "id": "2099156434999009759",
        "date": "13 Sep 2026",
        "cat": "Robotic affirming (why it helps)",
        "goal": "Explain RA, not one prize",
        "tech": "Robotic affirming to occupy attention so the old story cannot run",
        "method": "Quote of @nevesreality 'repetition creates your reality.' She loves RA because repeating leaves zero time to doubt. More repetition, fewer anxious thoughts; brain accepts it. You do not have to feel anything — just repeat. Not necessary if you dislike it.",
        "freq": "As long as you wish",
        "dur": "N/A",
        "actions": "N/A",
        "outcome": "Subjective: less anxiety/doubt",
        "tips": "RA as attention control, not a speed hack",
        "mistakes": "Thinking you must feel during RA; thinking RA is mandatory",
        "ux": "378 likes. Best insider explanation of RA's psychological job.",
        "replies": "0.",
        "likes": 378, "replies_n": 0, "reposts": 41, "views": 6580, "bookmarks": 132,
        "eq": "High for mechanism-as-users-understand-it.",
        "conf": "Medium-high as community psychology; not event proof.",
    },
    {
        "rank": 32,
        "author": "Kartik Jain",
        "user": "kartikjain0101",
        "id": "2038242388427362394",
        "date": "29 Mar 2026",
        "cat": "Mixed / Social announcement",
        "goal": "Car (example)",
        "tech": "Indirect wishing vs telling someone",
        "method": "Reply to 'Has manifestation worked?': Whenever I manifest something indirectly like 'I like that car, I wish to have one someday' it works. When I say I'm going to buy that car and tell someone, it never works.",
        "freq": "N/A",
        "dur": "N/A",
        "actions": "Not specified",
        "outcome": "Pattern claim: private/indirect yes; public declaration no",
        "tips": "Keep it quiet (user's pattern)",
        "mistakes": "Announcing the goal",
        "ux": "Non-LOA-influencer. Small but useful mixed-experience signal.",
        "replies": "In @shravi_aj thread.",
        "likes": 0, "replies_n": 0, "reposts": 0, "views": 6, "bookmarks": 0,
        "eq": "Low-medium (one sentence, no dates) but independent of coaching Twitter.",
        "conf": "Low as a law; medium as a reported personal pattern (goal-declaration / accountability effects).",
    },
    {
        "rank": 33,
        "author": "Lovlin T",
        "user": "lovlin_t",
        "id": "2038152431822098927",
        "date": "29 Mar 2026",
        "cat": "Detachment / Mixed",
        "goal": "Unspecified",
        "tech": "Letting go (not 'manifestation')",
        "method": "Reply: 'Manifestation no but letting go has almost worked for me. Or so I would say.'",
        "freq": "N/A",
        "dur": "N/A",
        "actions": "Not specified",
        "outcome": "Letting go almost worked; manifestation did not (self-report)",
        "tips": "Detachment over technique",
        "mistakes": "Relying on 'manifestation' as labeled",
        "ux": "Software engineer; outside the coach bubble.",
        "replies": "Parent thread.",
        "likes": 1, "replies_n": 0, "reposts": 0, "views": 73, "bookmarks": 0,
        "eq": "Low detail, high independence.",
        "conf": "Medium as a one-line mixed result.",
    },
    {
        "rank": 34,
        "author": "Nitul",
        "user": "nitul_choudhury",
        "id": "2038294498883866889",
        "date": "29 Mar 2026",
        "cat": "Failure",
        "goal": "Unspecified",
        "tech": "Unspecified manifestation",
        "method": "Reply: 'never worked...lets see how it goes this year.'",
        "freq": "N/A",
        "dur": "Implied prior attempts",
        "actions": "N/A",
        "outcome": "Never worked",
        "tips": "None",
        "mistakes": "None specified",
        "ux": "Mental-health builder; blunt negative.",
        "replies": "Parent thread.",
        "likes": 1, "replies_n": 0, "reposts": 0, "views": 14, "bookmarks": 0,
        "eq": "Low detail; counts as an independent negative.",
        "conf": "Low (no method).",
    },
    {
        "rank": 35,
        "author": "Shravika Jain + thread",
        "user": "shravi_aj",
        "id": "2038128456568115600",
        "date": "29 Mar 2026",
        "cat": "Mixed survey",
        "goal": "Ask if manifestation worked, out of 10 times",
        "tech": "Various (replies: whiteboard, notebook, combo, letting go, indirect wishing)",
        "method": "Question post, 19 replies. Sample: @mukesh_vc 10/10; @srq_ali always worked; @mvsantosh51 continuous process not a 1–2 day tablet; @WallsandWisdom nobody can answer except via belief; @vinodchendhil repeats through the day, whiteboard, book, combos.",
        "freq": "Varies",
        "dur": "Varies; one user said not a day or two",
        "actions": "Writing on boards/books in one reply",
        "outcome": "Mixed: always / 10/10 / never / letting go instead / unverifiable",
        "tips": "Treat it as ongoing; writing repetition",
        "mistakes": "Treating it like a two-day pill",
        "ux": "Best non-LOA-Twitter mixed sample in this research.",
        "replies": "19 replies; see above.",
        "likes": 39, "replies_n": 19, "reposts": 0, "views": 2620, "bookmarks": 2,
        "eq": "Medium as a pulse check; replies are short.",
        "conf": "Medium that experiences split.",
    },
    {
        "rank": 36,
        "author": "simply pen",
        "user": "simplypen12",
        "id": "2099313269353697465",
        "date": "14 Sep 2026",
        "cat": "Failure / Mental health",
        "goal": "Stop flooding negative thoughts",
        "tech": "Positive affirmations (failed in this scenario)",
        "method": "No amount of positive affirmations worked. Thoughts were so bad he saw a doctor, expected a calm talk, was given an injection.",
        "freq": "N/A",
        "dur": "N/A",
        "actions": "Sought medical care",
        "outcome": "Affirmations failed; medical intervention",
        "tips": "Implied: get care when thoughts flood",
        "mistakes": "Expecting affirmations to handle a clinical-level spiral",
        "ux": "Important boundary condition.",
        "replies": "1 (thread continuation not fully fetched).",
        "likes": 1, "replies_n": 1, "reposts": 0, "views": 5, "bookmarks": 0,
        "eq": "Medium as a failure boundary; incomplete thread.",
        "conf": "Medium-high that affirmations are not a crisis tool.",
    },
    {
        "rank": 37,
        "author": "Amina",
        "user": "amna_215",
        "id": "2093818227147337883",
        "date": "29 Aug 2026",
        "cat": "Failure",
        "goal": "Unspecified relief/change",
        "tech": "Self-help videos, meditation, delusion, manifestation, positive affirmations",
        "method": "One-line: none of those amounts worked.",
        "freq": "N/A",
        "dur": "N/A",
        "actions": "Consumed self-help content",
        "outcome": "No help (self-report)",
        "tips": "None",
        "mistakes": "Stacking self-help modes without result",
        "ux": "Low engagement independent negative.",
        "replies": "0.",
        "likes": 6, "replies_n": 0, "reposts": 0, "views": 61, "bookmarks": 0,
        "eq": "Low detail; counts as negative.",
        "conf": "Low.",
    },
    {
        "rank": 38,
        "author": "Sol Brah",
        "user": "SolBrah",
        "id": "2099069288409956759",
        "date": "13 Sep 2026",
        "cat": "Visualization (cautionary + 'it works')",
        "goal": "Avoid a puncture; then get a van lift",
        "tech": "Do not visualize unwanted events; visualize the wanted help",
        "method": "On a country bike ride his mother said a puncture would be annoying. He warned her not to visualize that. Within 5 minutes, flat tyre. They then visualized a van; within ~5 minutes a van offered a lift to town.",
        "freq": "In-the-moment comments",
        "dur": "Minutes",
        "actions": "Walking with a bike on a country road — vans do pass",
        "outcome": "Puncture then a lift (self-report)",
        "tips": "Do not put energy into unwanted scenes",
        "mistakes": "Mother 'visualizing' the puncture (his framing)",
        "ux": "1.5k likes. Classic coincidence-prone story; influencer.",
        "replies": "40 replies (not all fetched).",
        "likes": 1519, "replies_n": 40, "reposts": 37, "views": 38905, "bookmarks": 190,
        "eq": "Low-medium. Memorable; extremely confounded (base rates of punctures and helpful drivers).",
        "conf": "Low as causation; useful as a 'don't mentally rehearse the fear' cue.",
    },
    {
        "rank": 39,
        "author": "Health Wealth",
        "user": "HlthWlthAbndnc",
        "id": "2099899129195294890",
        "date": "15 Sep 2026",
        "cat": "Self-concept / Affirmations",
        "goal": "Fully trusting her own judgment (anti-scam)",
        "tech": "Intention + built-up affirmations",
        "method": "1) Set intention 'I fully trust myself+my judgment.' 2) Built it up: 'I know exactly what I'm doing+it's easy for me to trust myself. Even if it doesn't feel like it, I always know exactly what to do+figure it out.' Context: coaching-scam thread — if you believe the coach is untrustworthy, notice that and ask questions.",
        "freq": "Not specified",
        "dur": "Not specified",
        "actions": "Ask the coach what's happening; it's your money/time",
        "outcome": "Self-trust as the manifestation; practical anti-scam behavior",
        "tips": "Use assumption work on judgment; still interrogate coaches",
        "mistakes": "Believing you have poor judgment; not questioning scammers",
        "ux": "Coaching/divination bio, but the content is about not getting scammed. Useful irony.",
        "replies": "1.",
        "likes": 13, "replies_n": 1, "reposts": 4, "views": 385, "bookmarks": 8,
        "eq": "Medium. Practical + inner work.",
        "conf": "Medium.",
    },
    {
        "rank": 40,
        "author": "Lisa Charelle",
        "user": "DoubleTakeLisa",
        "id": "1955710182589190286",
        "date": "13 Aug 2025",
        "cat": "369 method",
        "goal": "One unspecified asked-for thing",
        "tech": "369 manifestation method",
        "method": "Did 369 two days ago; received one of the things she asked the universe for today. Plans to do it every day.",
        "freq": "Intends daily after a 2-day trial",
        "dur": "2 days to a result (claimed)",
        "actions": "Not specified",
        "outcome": "One requested thing arrived (unnamed)",
        "tips": "None beyond repeating 369",
        "mistakes": "Not stated",
        "ux": "Only first-person 369 hit with a timebox in this search. Very thin.",
        "replies": "0.",
        "likes": 2, "replies_n": 0, "reposts": 0, "views": 56, "bookmarks": 0,
        "eq": "Low. No description of what 369 steps she used or what arrived.",
        "conf": "Low.",
    },
]
POSTS += [
    {
        "rank": 41,
        "author": "amelia",
        "user": "receivednow",
        "id": "2094827733214019763",
        "date": "1 Sep 2026",
        "cat": "Affirmations",
        "goal": "Multiple list items",
        "tech": "Affirmations + persist; stop old story",
        "method": "Says affirmations worked too well, ticking many list items. Stop repeating the old story if you want change. Reality can shift in the next moment. Don't stop persisting.",
        "freq": "Persist (not timed)",
        "dur": "Not specified",
        "actions": "Not specified",
        "outcome": "Multiple unspecified list items ticked",
        "tips": "Stop old story; persist",
        "mistakes": "Repeating the old story",
        "ux": "Coaching/subliminal seller. 204 likes.",
        "replies": "0.",
        "likes": 204, "replies_n": 0, "reposts": 16, "views": 2130, "bookmarks": 35,
        "eq": "Low-medium. No concrete items.",
        "conf": "Low.",
    },
    {
        "rank": 42,
        "author": "Reira",
        "user": "hazeleyesgrace",
        "id": "2097686412372164808",
        "date": "9 Sep 2026",
        "cat": "Mistake / Persist",
        "goal": "Answer 'I've done this for months/years'",
        "tech": "Reframe: you persisted in not having it",
        "method": "If you spent months wanting it while acknowledging unfavorable versions, deciding nothing is happening because you do not see it yet, and letting the outside decide whether you have it, you have not been manifesting — you persisted in the version where you do not have it.",
        "freq": "N/A",
        "dur": "Addresses months/years complaints",
        "actions": "N/A",
        "outcome": "Advice",
        "tips": "Stop letting the outside veto the assumption",
        "mistakes": "Months of wanting + checking = practicing lack",
        "ux": "Coaching. High-signal mistake diagnosis.",
        "replies": "0.",
        "likes": 120, "replies_n": 0, "reposts": 13, "views": 1572, "bookmarks": 38,
        "eq": "Medium as diagnosis; unfalsifiable if every failure is relabeled.",
        "conf": "Medium. Pattern matches other posts; beware unfalsifiability.",
    },
    {
        "rank": 43,
        "author": "TENSHI",
        "user": "tenshispace",
        "id": "2099120990727115204",
        "date": "13 Sep 2026",
        "cat": "Robotic affirming / Old story",
        "goal": "Explain RA as drowning the old inner narration",
        "tech": "Robotic affirming as replacing already-running repeats",
        "method": "Thai: RA is not for speed. It makes the new story loud enough to replace old repeats that were never called affirmations: 'I've never been lucky in love / money is hard / I never succeed.'",
        "freq": "N/A",
        "dur": "N/A",
        "actions": "N/A",
        "outcome": "Conceptual",
        "tips": "You are already affirming; change which sentence is on loop",
        "mistakes": "Using RA as a speed cheat code",
        "ux": "Elegant restatement of cognitive looping.",
        "replies": "1.",
        "likes": 5, "replies_n": 1, "reposts": 4, "views": 828, "bookmarks": 2,
        "eq": "Medium-high conceptually.",
        "conf": "Medium-high as a psych-compatible framing.",
    },
    {
        "rank": 44,
        "author": "brigitté",
        "user": "iamallthatis_",
        "id": "2009111869533950081",
        "date": "8 Jan 2026",
        "cat": "Career / Rampage affirmations / Visualization",
        "goal": "Job-of-dreams identity / many offers",
        "tech": "Non-debatable affirming + identity + vague future-memory visualization",
        "method": "When she affirms it is not up for debate. Assumes identity of the version who has it. Visualized conversations with friends: 'idk what job to take there's so many offers.' Rampage: luck, more than enough, magnetic, opportunities like Niagara, right place/right time, dream job found her out of the blue.",
        "freq": "Mental rampage (not clocked)",
        "dur": "Not specified",
        "actions": "Not specified in this post",
        "outcome": "Method/affirmation drop, not a dated hire",
        "tips": "Vague-but-lived-in scenes; identity; no debate",
        "mistakes": "Not stated",
        "ux": "342 likes. Complements her Feb routine post.",
        "replies": "Thank-you from the asker.",
        "likes": 342, "replies_n": 1, "reposts": 22, "views": 11783, "bookmarks": 140,
        "eq": "Medium. Affirmation specimen more than a result log.",
        "conf": "Medium.",
    },
    {
        "rank": 45,
        "author": "jennay",
        "user": "jennay12013",
        "id": "2085439554085921215",
        "date": "6 Aug 2026",
        "cat": "SP (celebrity) / Obsession mistake",
        "goal": "Text from a celebrity SP",
        "tech": "Year-long manifesting; movement then obsession",
        "method": "Manifesting celebrity SP ~1 year. Little movement (him viewing her story) but she kept obsessing over every little thing and wondering when something bigger would happen. Thread title says she manifested a text; fetch did not return the rest of her method posts beyond a congrats reply.",
        "freq": "Year-long",
        "dur": "~1 year",
        "actions": "Social media (he viewed her story) — practical channel",
        "outcome": "Claims a text; incomplete method in retrieved thread",
        "tips": "Incomplete",
        "mistakes": "Obsessing over every small movement",
        "ux": "Useful as a 'checking small signs' specimen. Incomplete thread.",
        "replies": "@zyoprincess congratulations.",
        "likes": 31, "replies_n": 2, "reposts": 4, "views": 1793, "bookmarks": 15,
        "eq": "Low-medium (truncated).",
        "conf": "Low for the text; medium for the obsession pattern.",
    },
    {
        "rank": 46,
        "author": "FLARE (retelling Shane Missler)",
        "user": "imhiminflesh",
        "id": "2094479505922596986",
        "date": "31 Aug 2026",
        "cat": "SATS / Lottery (viral retelling)",
        "goal": "Lottery win",
        "tech": "Daily SATS (ascribed to Shane Missler / Neville)",
        "method": "Not the author's experiment. Screenshots: Missler Facebook memory of a 2017 Neville quote plus news of a huge jackpot. Caption: he manifested winning using daily SATS; repetition is key. Replies ask what SATS is.",
        "freq": "Every night (as claimed by the poster, not independently verified here)",
        "dur": "Older story (2017–2018 era), recirculated 2026",
        "actions": "Buying lottery tickets is a necessary practical action (not stated in the tweet)",
        "outcome": "News photos of a jackpot winner used as LOA proof",
        "tips": "Repetition; nightly SATS",
        "mistakes": "N/A",
        "ux": "1,502 likes. This is hype recirculation, not a 2026 first-person log.",
        "replies": "@Anit_ishere: 'What's a SAT?'; others call it insane.",
        "likes": 1502, "replies_n": 8, "reposts": 125, "views": 28520, "bookmarks": 711,
        "eq": "Low as evidence. Viral attribution; lottery base rates; not independent 2026 data.",
        "conf": "Very low. Include only as 'what the community circulates as proof'.",
    },
    {
        "rank": 47,
        "author": "blessedbyloa",
        "user": "blessedbyloa",
        "id": "2098810324853936477",
        "date": "12 Sep 2026",
        "cat": "Affirmations list / Self-concept",
        "goal": "Success identity",
        "tech": "Rampage success affirmations",
        "method": "Long lists: born successful, don't try hard I simply win, success in veins, failure/poverty aren't real concepts, flip ideas around success, occupy different assumptions. 543 likes / 171 bookmarks.",
        "freq": "Rampage (not timed)",
        "dur": "N/A",
        "actions": "N/A",
        "outcome": "Affirmation content, not a result log",
        "tips": "Change mental conceptions of success",
        "mistakes": "Entertaining failure/poverty as real concepts (their framing)",
        "ux": "Specimen of 2026 RA copy, not an experiment.",
        "replies": "3.",
        "likes": 543, "replies_n": 3, "reposts": 92, "views": 6619, "bookmarks": 171,
        "eq": "Low as evidence; high as a corpus sample of what people repeat.",
        "conf": "N/A for outcomes.",
    },
    {
        "rank": 48,
        "author": "spirituel mommy",
        "user": "divaspiritcleo",
        "id": "2099422909349638542",
        "date": "14 Sep 2026",
        "cat": "Living in the end (instructional)",
        "goal": "Teach living in the end",
        "tech": "Ask how you would think/feel/behave if it were done; 3–5 min scene",
        "method": "Replace 'I hope I make more money' with 'I have a healthy relationship with money and manage income well.' Task: pick a wish, imagine a tiny done-scene 3–5 minutes, ask what today-you would do differently. States the aim is not denying facts but stopping the mind from living in 'I don't have it.'",
        "freq": "Daily task in a 30-day school",
        "dur": "3–5 minutes",
        "actions": "Today's different choices if it were true",
        "outcome": "Instructional",
        "tips": "Translate lack sentences into already-true identity sentences; tiny scene",
        "mistakes": "Hoping/when-will-it-come focus",
        "ux": "Clear, less mystical than average. Pairs with SATS post.",
        "replies": "0.",
        "likes": 39, "replies_n": 0, "reposts": 0, "views": 1731, "bookmarks": 26,
        "eq": "High as a protocol card.",
        "conf": "High that this is standard teaching.",
    },
    {
        "rank": 49,
        "author": "user",
        "user": "manifestmemoir",
        "id": "2099281508142113089",
        "date": "13 Sep 2026",
        "cat": "Spoken affirmations",
        "goal": "Unspecified desires that 'ALWAYS' manifest",
        "tech": "Affirm out loud with eyes closed",
        "method": "What works effortlessly: affirming out loud with eyes closed. Feels at peace about the desire and it always manifests. Took a while to figure out; now confident.",
        "freq": "Not specified",
        "dur": "N/A",
        "actions": "N/A",
        "outcome": "Always (global claim)",
        "tips": "Out loud + eyes closed for peace/acceptance",
        "mistakes": "Implied: other modes felt less effortless",
        "ux": "Tiny engagement; first-person preference.",
        "replies": "0.",
        "likes": 0, "replies_n": 0, "reposts": 0, "views": 28, "bookmarks": 0,
        "eq": "Low-medium.",
        "conf": "Low.",
    },
    {
        "rank": 50,
        "author": "vee",
        "user": "highestpedestal",
        "id": "1918120891629637970",
        "date": "2 May 2025",
        "cat": "Unfalsifiable failure-reframe",
        "goal": "Respond to 'the method didn't work'",
        "tech": "Assumption / thoughts, not methods",
        "method": "It's not the method that manifests, it's you and your thoughts. If a method 'didn't work,' you assumed it wouldn't, so it didn't.",
        "freq": "N/A",
        "dur": "N/A",
        "actions": "N/A",
        "outcome": "Rhetorical",
        "tips": "Assume the method works / assume you have it",
        "mistakes": "Blaming the method",
        "ux": "314 likes. Central LOA-Twitter logic — and the main reason failures get erased.",
        "replies": "0 listed.",
        "likes": 314, "replies_n": 0, "reposts": 26, "views": 9483, "bookmarks": 70,
        "eq": "High as a belief specimen; poor as an explanatory model (unfalsifiable).",
        "conf": "High that this is how the community explains negatives.",
    },
]


def url_for(p):
    return f"https://x.com/{p['user']}/status/{p['id']}"


def configure_styles(doc):
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(11)
    normal.font.color.rgb = BODY
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    pf = normal.paragraph_format
    pf.space_after = Pt(8)
    pf.line_spacing = 1.15

    for style_name, size, before, after, outline in [
        ("Heading 1", 18, 16, 8, 0),
        ("Heading 2", 14, 14, 6, 1),
        ("Heading 3", 12, 12, 4, 2),
    ]:
        st = styles[style_name]
        st.font.name = "Arial"
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = NAVY
        st._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        # outline is already set by heading style


def set_section_portrait(section, header_text):
    section.orientation = WD_ORIENT.PORTRAIT
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    header_footer(section, header_text)


def set_section_landscape(section, header_text):
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width = Inches(11)
    section.page_height = Inches(8.5)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    header_footer(section, header_text)


def build():
    doc = Document()
    configure_styles(doc)
    section = doc.sections[0]
    set_section_portrait(section, "X/Twitter Manifestation Intelligence")

    # COVER
    for _ in range(3):
        para(doc, "", space_after=0)
    p = para(doc, "COMMUNITY INTELLIGENCE REPORT", size=12, bold=True, color=TEAL, align="center", space_after=6)
    para(doc, "What Real People on X Say They Tried,", size=22, bold=True, color=NAVY, align="center", space_after=0)
    para(doc, "What They Claim Worked, and What Repeatedly Failed", size=22, bold=True, color=NAVY, align="center", space_after=12)
    add_hr(doc)
    para(
        doc,
        "Law of Attraction  ·  Law of Assumption  ·  Visualization  ·  Affirmations  ·  SATS  ·  Scripting  ·  Self-concept  ·  Detachment  ·  Gratitude  ·  369  ·  Vision boards  ·  Career & money stories",
        size=11,
        italic=True,
        color=MUTED,
        align="center",
        space_after=18,
    )
    para(doc, "Research window: September 2024 – September 2026 (plus older viral recirculations)", size=11, align="center", space_after=4)
    para(doc, "Compiled: 15 September 2026", size=11, align="center", space_after=4)
    para(doc, "Source platform: X (Twitter) public posts and threads", size=11, align="center", space_after=18)

    callout(
        doc,
        "Read this first",
        "This is a community-intelligence report built from public X posts that were actually retrieved and read for this project. It is not scientific proof that manifestation techniques cause external events. Claims below are personal experiences, coaching marketing, or folk psychology unless marked otherwise. Direct user statements are separated from interpretation. Engagement is not treated as evidence that a method works.",
        WARN_FILL,
    )

    add_heading_styled(doc, "Contents", 1)
    para(doc, "In Microsoft Word, right-click the field below and choose Update Field.", size=10, italic=True, color=MUTED)
    add_toc(doc)

    add_page_break(doc)

    # INTRO / METHOD
    add_heading_styled(doc, "How this report was built", 1)
    mixed_para(
        doc,
        [
            (
                "The brief asked for a deep read of public X conversation — not a collage of inspirational quotes. Searches used first-person and method language (how I manifested, SATS, robotic affirming, vision board, 369, gratitude, self-concept, manifestation didn't work, biggest mistake, daily routine) with a date filter from September 2024 forward. High-value hits were opened as full threads. Where the method lived in screenshots, those images were read. Coaching bios, CTAs, and recycled viral stories were tagged rather than deleted when they still showed how the community talks.",
                {"size": 11},
            )
        ],
    )

    add_heading_styled(doc, "What was excluded or down-ranked", 2)
    for t in [
        "Generic quote cards and copy-paste 'believe and receive' posts with no practice details.",
        "Crypto, affiliate, and identical spam accounts.",
        "Bitcoin faucet tweets that matched the keyword SATS.",
        "Fandom 'I manifested these concert tickets' one-liners with no method — used only as a cultural note.",
        "The same coach repeating the same story. Counted once.",
        "Courses sold as numbered miracles (55x5, 777, 888) when no first-person experiment was attached.",
    ]:
        bullet(doc, t)

    add_heading_styled(doc, "Sample limits (important)", 2)
    mixed_para(
        doc,
        [
            (
                "This is not a census of thousands of independent, verified experiments. X search returns a thin slice per query. The working set is ",
                {"size": 11},
            ),
            ("dozens of search queries, full-thread reads of the most informative hits, and a ranked set of 50 real posts", {"size": 11, "bold": True}),
            (
                ". Recurring patterns are reported only when they showed up across independent accounts. Where the community is mostly coaches talking to each other, that is stated. Exact metrics that the interface did not provide are marked Not available — never estimated.",
                {"size": 11},
            ),
        ],
    )

    add_heading_styled(doc, "Evidence labels used throughout", 2)
    labels = [
        ("High", "First-person, reconstructable method, some duration/frequency, a named outcome. Still anecdotal."),
        ("Medium", "First-person but thin on time, steps, or the actual result."),
        ("Low", "Advice, affirmation lists, coaching CTAs, or viral retellings without a personal log."),
        ("Confidence", "How much weight this report gives the post as community intelligence — not as physics."),
    ]
    table = doc.add_table(rows=1, cols=2)
    set_col_widths(table, [1.3, 5.2])
    header_row(table, ["Label", "Meaning"])
    for i, (a, b) in enumerate(labels):
        row = table.add_row()
        fill = ROW_ALT if i % 2 else "FFFFFF"
        cell_text(row.cells[0], a, size=9, bold=True, fill=fill)
        cell_text(row.cells[1], b, size=9, fill=fill)
    para(doc, "", space_after=6)

    add_heading_styled(doc, "Correlation is not causation", 2)
    mixed_para(
        doc,
        [
            ("Direct user statement: ", {"size": 11, "bold": True}),
            ("people on X attribute jobs, texts, tickets, money, health, and relationships to inner techniques.", {"size": 11}),
        ],
    )
    mixed_para(
        doc,
        [
            ("Interpretation: ", {"size": 11, "bold": True}),
            (
                "the same stories almost always also contain delayed job applications, existing workplaces, school proximity, friends buying tickets, social media contact, medical care not mentioned, coincidence, and selective posting of hits. Psychological mechanisms that can operate without a metaphysical 'universe' include goal priming, selective attention, confirmation bias, self-efficacy, implementation intentions, mental rehearsal, behavioral activation, and reduced rumination when people 'detach.' This report keeps those layers separate.",
                {"size": 11},
            ),
        ],
    )

    add_heading_styled(doc, "The community, in one paragraph", 1)
    mixed_para(
        doc,
        [
            (
                "Classic Law of Attraction content (vision boards, 369, gratitude journals, 'ask the universe') is still posted, but the loudest, most detailed 2025–2026 English practice community on X is ",
                {"size": 11},
            ),
            ("Law of Assumption / #loass Twitter", {"size": 11, "bold": True}),
            (
                " — Neville Goddard language (SATS, living in the end, revision, persist), robotic affirming, self-concept, subliminals, and especially SP (specific person) stories. A parallel, smaller set of non-coach users says manifestation did nothing until they let go, built a product, applied for jobs, or sought medical care. Coaching funnels are dense. SP content often includes the claim that other people have 'no free will' in your reality; that idea is popular inside the bubble and is treated here as ethically controversial, not as a finding.",
                {"size": 11},
            ),
        ],
    )

    # OUTPUT 1 landscape table
    add_page_break(doc)
    add_heading_styled(doc, "Output 1 — Master dataset (ranked posts)", 1)
    para(
        doc,
        "Fifty real posts, ranked by informational value (detail, method, usefulness, independence), not likes. Full URLs and narrative write-ups are in Output 2. Column 'Eq' is evidence quality. Bookmarks are included when the interface returned them.",
        size=10,
        italic=True,
        color=MUTED,
    )

    # new landscape section
    new_sec = doc.add_section(WD_SECTION.NEW_PAGE)
    set_section_landscape(new_sec, "Output 1 — Master dataset")

    cols = ["#", "Author", "Date", "Goal", "Technique", "Duration", "Outcome (claimed)", "Likes", "Eq", "URL"]
    widths = [0.35, 1.15, 0.85, 1.35, 1.55, 1.15, 1.85, 0.5, 0.55, 0.85]
    t = doc.add_table(rows=1, cols=10)
    set_col_widths(t, widths)
    header_row(t, cols)
    for i, p in enumerate(POSTS):
        row = t.add_row()
        prevent_row_split(row)
        fill = ROW_ALT if i % 2 else "FFFFFF"
        vals = [
            str(p["rank"]),
            f"{p['author']}\n@{p['user']}",
            p["date"],
            p["goal"],
            p["tech"],
            p["dur"][:90],
            p["outcome"][:110],
            str(p["likes"]),
            p["eq"].split(".")[0][:18],
        ]
        for j, v in enumerate(vals):
            cell_text(row.cells[j], v, size=7, fill=fill, align="center" if j in (0, 7) else "left")
        add_url_cell(row.cells[9], url_for(p), fill=fill)

    para(doc, "Table 1. Ranked working set. Metrics as returned by X search at collection time. Views/reposts/bookmarks are in Output 2.", size=8, italic=True, color=MUTED, space_before=8)

    # back to portrait
    sec2 = doc.add_section(WD_SECTION.NEW_PAGE)
    set_section_portrait(sec2, "X/Twitter Manifestation Intelligence")

    add_heading_styled(doc, "Output 1b — Required fields for each high-value post", 2)
    para(
        doc,
        "The compact table cannot hold every required field. The records below keep: author, username, date, URL, summary, goal, technique, exact practice, frequency, duration, claimed outcome, tips, mistakes, user experience, community reaction, engagement, important replies, evidence quality, and confidence.",
        size=11,
    )

    for p in POSTS:
        add_heading_styled(doc, f"{p['rank']}. {p['author']} (@{p['user']}) — {p['date']}", 3)
        hp = doc.add_paragraph()
        hp.paragraph_format.space_after = Pt(4)
        add_hyperlink(hp, url_for(p), url_for(p), size=9)
        meta = (
            f"Category: {p['cat']}  |  Likes {p['likes']}  ·  Replies {p['replies_n']}  ·  "
            f"Reposts {p['reposts']}  ·  Views {p['views']}  ·  Bookmarks {p.get('bookmarks', 'Not available')}"
        )
        para(doc, meta, size=9, italic=True, color=MUTED, space_after=4)
        for label, key in [
            ("Post summary / user experience", "ux"),
            ("Manifestation goal", "goal"),
            ("Technique / method", "tech"),
            ("Exact practice", "method"),
            ("Frequency", "freq"),
            ("Duration", "dur"),
            ("Actions taken", "actions"),
            ("Claimed outcome", "outcome"),
            ("Tips given", "tips"),
            ("Mistakes mentioned", "mistakes"),
            ("Important replies / community reaction", "replies"),
            ("Evidence quality", "eq"),
            ("Confidence", "conf"),
        ]:
            mixed_para(
                doc,
                [(f"{label}: ", {"size": 10, "bold": True, "color": NAVY}), (p[key], {"size": 10})],
                space_after=3,
                justify=True,
            )

    # OUTPUT 2
    add_page_break(doc)
    add_heading_styled(doc, "Output 2 — Top 50 most valuable posts (ranked)", 1)
    para(
        doc,
        "Ranking rule: detailed experience and reconstructable method outrank likes. Independent (non-coach) posts were boosted when they had real constraints (jobs, layoffs, doctors). Viral coaching threads were kept when they showed the dominant folk practice. Quotes below are direct user statements unless labeled interpretation.",
        size=11,
    )

    top_blurbs = {
        1: "Best single 2025–26 SP log in this set: timeline from breakup → 135-item list → friendship-only 3D → months of efforting → one decided sentence → no-contact broken → four more months of wavering → relationship. Direct statement: she stopped watching videos and stacking techniques; she regrets none of the affirming, only the back-and-forth.",
        2: "Best career/money log: applications in 2025, nothing, mindset shift without affirmations, delayed offer, layoff, two-week replacement at same pay. Interpretation: this is identity + labor-market lag + continued employability, not a technique trophy.",
        3: "Best clock-level routine: 10 minutes self-concept at wake, commute RA, zero affirming at work, shower line, 7–11pm subliminals. Community used it as a template (replies asked how to split three desires).",
        4: "Family 'new story' while still in the house. Direct statement: no detailed how, just 'they treat me as loving parents,' plus visualizing shoving the old movie aside. Safety note: this is not a substitute for support in abuse.",
        5: "Marketer already in seat affirms six-figure identity 'for a bit,' then a Sony-related awards project and pay jump. Interpretation: workplace optionality did a lot of the lifting.",
        6: "School SP + subliminals + hallway visualization + self-concept; dropped subliminals once assumption felt solid. Proximity is a huge confounder.",
        7: "The default 2026 #loass day: autopilot self-concept, live normally, visualize bookends, 5-minute saturation only when the desire feels unbelievable.",
        8: "Unintentional nightly scene for two months, then forgot, then the kiss in that place. Direct statement: she did not know LOA. Interpretation: friendship + actually going out.",
        9: "Aphantasia-friendly log (no visualization). Mix of ordinary (job application later offered) and extraordinary (weather, anatomy). Low likes, which is useful — not a growth-hacked thread.",
        10: "Ticket scam + sold-out site + a friend who actually purchased seats. Direct extra lesson: be kind. Interpretation: social capital, not only persisting.",
        11: "Two-year 'universe' failure vs four-month God-and-action story. Direct statement: confirmation bias and behavior change do not require an impersonal force.",
        12: "Builder counterweight: no product people want, no financial manifestation.",
        13: "Best explanation of why routines explode: seven people prescribe seven methods before asking what the silence means.",
        14: "Minority harm report on robotic affirming (cortisol / OCD loops). Tiny engagement, thematically necessary.",
        15: "Decide-and-stop-attending school, explicitly against scripting/RA/visualization.",
        16: "10 minutes RA before sleep as a 'success.' Result unnamed in text.",
        17: "Coaching testimonial bundle (school day, friends, body). Treat body-without-diet claims as hype.",
        18: "Template SP-silence thread, 78k views, coaching CTA. Method is 'I decided / circumstances don't matter.'",
        19: "Imagine the boring Tuesday after the money. A reply admitted she could get money but not keep it — a rare keeping problem.",
        20: "Stop checking; you are running old code. Influential 2025 thread.",
        21: "Morning successful-day rehearsal + pair past success feelings with today's image. Closest to sports psych.",
        22: "Highest-engagement methods dump of the window; replies converge on decide, one scene+song, affirm-then-forget, live your life.",
        23: "DIY mind-movie recipe (affs, TTS, images, Dispenza/theta).",
        24: "Clean SATS card plus an unusual 'this is not scientifically guaranteed' disclaimer.",
        25: "First-person 'SATS never failed' with no protocol timestamps.",
        26: "Revision/shifting story with abuse TW and physically extreme claims. Do not treat as a safety plan.",
        27: "Third-party cancer/ICU/diabetes claims. Flag as likely hype; not medical evidence.",
        28: "Embodiment video + the best skeptical reply (thought, decision, action vs magic).",
        29: "Delete the vision board / 369 / $497 system; decide, expect, live. Parent article ~1.56M views.",
        30: "Checking is a different hobby from practicing.",
        31: "RA as attention occupation so doubt has no airtime — you need not 'feel it.'",
        32: "Independent: private wishing works, telling someone does not (car example).",
        33: "Independent: manifestation no, letting go almost yes.",
        34: "Independent: never worked.",
        35: "19-reply mixed pulse: 10/10, always, never, not a two-day pill, whiteboard writing.",
        36: "Affirmations failed a thought-flood; doctor gave an injection. Boundary condition.",
        37: "Self-help + meditation + manifestation + affirmations: none worked.",
        38: "Puncture then van. High likes, high coincidence, useful 'don't rehearse the fear' moral.",
        39: "Self-trust affirmations aimed at not getting coached into a scam.",
        40: "Only timed first-person 369 hit found (2 days, unnamed result). Weak.",
        41: "Affirmations 'worked too well' — unspecified list.",
        42: "Months/years of 'trying' relabeled as persisting in lack. Powerful and unfalsifiable.",
        43: "You already run repeats ('money is hard'); RA swaps the sentence.",
        44: "Job-offer rampage script and 'so many offers' mental movie.",
        45: "Celebrity SP, one year, obsessing over story views. Truncated thread.",
        46: "Shane Missler lottery recirculated as SATS proof. Treat as hype, not 2026 evidence.",
        47: "Success-identity affirmation dump. Corpus sample.",
        48: "Living-in-the-end worksheet: rewrite lack sentences; 3–5 min scene; what would today-me do.",
        49: "Out-loud, eyes-closed affirming as the thing that finally felt peaceful.",
        50: "If the method failed, your assumption failed. The community's standard move — and why negatives vanish.",
    }

    for p in POSTS:
        mixed_para(
            doc,
            [
                (f"#{p['rank']}  {p['author']} (@{p['user']})  ·  {p['date']}  ·  {p['likes']} likes  ·  {p['views']} views", {"size": 11, "bold": True, "color": NAVY}),
            ],
            space_after=2,
            justify=False,
        )
        hp = doc.add_paragraph()
        hp.paragraph_format.space_after = Pt(2)
        add_hyperlink(hp, url_for(p), url_for(p), size=9)
        para(doc, top_blurbs[p["rank"]], size=11, space_after=10)

    # OUTPUT 3
    add_page_break(doc)
    add_heading_styled(doc, "Output 3 — Top successful methods (community-ranked)", 1)
    para(
        doc,
        "Counts below are independent-ish experiences in this working set, not a platform-wide N. 'Positive' means a user attributed a wanted outcome to the method. 'Negative' means a user said it failed, harmed, or was beside the point. Practical rating is this report's interpretation of usefulness as a psychological/behavioral tool, not a claim of metaphysical efficacy.",
        size=11,
    )

    methods = [
        ["Self-concept / identity assumptions", "I-am sentences during morning routine, showers, or all day; 'I am the person who has X.'", "Daily, often morning+night", "Weeks to months in stories that name time", "8+", "0 direct; some say it felt 'scammy' until used (Fawn)", "Do this before SP techniques; make it autopilot", "Skipping it; using it as a delay tactic forever", "Very frequently recommended in #loass", "Self-efficacy, self-schema, cognitive reframing", "8/10"],
        ["Decide, then live / detach", "Decide it is done; stop extra techniques; live a normal day; let 3D 'catch up.'", "One decision + ongoing non-attention", "Hours to months", "7+", "Users who 'detached' as suppression still checked; some never-worked reports", "Detachment is not apathy; it is dropping the monitoring", "Spiritualizing avoidance; no action on career goals", "Very frequently recommended", "Reduced rumination; attentional withdrawal from checking", "8/10"],
        ["Robotic affirming", "Repeat a sentence until doubt has no slot; feeling optional.", "10 min to several hours; commute/bed", "Days to ongoing", "6+", "1 explicit harm critique (OCD/cortisol); others say it is not the only way", "Use as attention control; not mandatory; not a speed hack", "10k/day prescriptions; looping on lack", "Frequently loved inside #loass; mixed outside", "Verbal overshadowing of worry; habituation; can resemble compulsion", "6/10"],
        ["Visualization / SATS / mental movie", "Short first-person AFTER scene in drowsy state; or a edited mind-movie; or morning successful-day rehearsal.", "Nightly 3–10 min or morning 5–15 min", "2 weeks to months (Jas: ~2 months)", "6+", "Few 'visualization didn't work' hits in this window; more 'I can't visualize' workarounds", "Keep the scene short; proof-it-happened not how-it-happens; optional if you cannot image", "Long elaborate movies; visualizing the fear (Sol Brah story)", "Frequently recommended, especially pre-sleep", "Mental rehearsal / implementation imagery; encoding as memory", "7.5/10"],
        ["Persist in one assumption (don't switch)", "Pick the end state and stay there when 3D contradicts.", "Continuous", "Often months (Fawn, Puffie, Reira)", "8+", "Failures relabeled as 'you didn't persist' (unfalsifiable)", "One sentence is enough", "Method hopping every few days; 7-method stacks", "Very frequently recommended", "Consistency; but community uses it to erase disconfirming data", "7/10 as consistency, 3/10 as a theory of failure"],
        ["Stop checking the 3D", "Do not use bank apps, texts, or 'signs' as a scoreboard.", "Whenever the urge hits", "Until the urge dies down", "Named in 10+ posts", "Some coaches now say checking is allowed if you don't spiral (@mirrraapp)", "If you check, don't write a lack story afterwards", "Obsessing over story views, angel numbers, sold-out pages", "Very frequently recommended", "Exposure reduction for anxiety; fewer confirmation-bias samples", "8/10"],
        ["Habit + practical action", "Apply for jobs, keep the marketing job, let a friend buy the ticket, build a product, see a doctor.", "As the domain requires", "Job stories: months", "4–5 clear cases (4D, Taz, miluvin444, Jack Moses, simply pen)", "LOA accounts often omit this layer", "Do the ordinary verbs", "Manifestation as a substitute for a product, application, or care", "Frequent outside the bubble; under-advertised inside it", "Behavioral activation; opportunity exposure", "9/10 for career/money/health domains"],
        ["Living in the end (after-state)", "Imagine ordinary life after the result (accountant problems, many job offers, supportive parents).", "3–5 min scenes and all-day identity", "Ongoing", "5+", "Arrival-only visualization called out as keeping it feeling huge (Zeion)", "Boring Tuesday after, not the jackpot clip", "Only visualizing the dramatic receive-moment", "Frequently recommended (Neville line)", "Goal habituation; reduces 'once in a lifetime' framing", "7.5/10"],
        ["Subliminals", "Audio under music/Pinterest at night (gus); used then dropped (Puffie).", "Night / background", "Weeks", "2–3", "People drop them without losing 'results' once assumption is in; hard to separate from RA", "Optional overlay", "Treating YouTube subs as the engine", "Occasionally to frequently in #loass/subtwt", "Placebo + repetition; sleep association", "4/10"],
        ["Scripting / lists / 369 / vision boards", "Write 135 traits (Fawn); 369 for 2 days (Lisa); vision-board affirmations (Mel's 21-day RA experiment); mind-movie storyboards.", "Daily writing or a one-time list", "2 days (369 claim) to months", "2 thin 369/VB first-person hits; lists more useful", "Delete-your-vision-board essay; 369 is mostly coaching graphics", "A list can clarify standards; numbered rituals are optional", "Collecting methods instead of a decision", "Classic LOA: frequent marketing, thin logs; #loass: often dismissed", "Goal clarification; implementation intentions if specific", "5/10 for lists; 3/10 for 369/VB as magic"],
        ["Gratitude", "Evening 'one thing grateful / one person / one peaceful moment' in a 15-min ritual post; gratitude journals mostly affiliate listings.", "Nightly in one protocol", "N/A in strong stories", "1–2 practice mentions", "Almost no first-person 'gratitude journal manifested X' logs in this window", "Use as mood hygiene, not a lottery ticket", "Buying 1,000-page journals", "Occasionally recommended; heavily merchandised", "Well-studied for well-being, not for causing jackpots", "6/10 as well-being practice"],
        ["Revision", "Replay today's memory as the wanted version before sleep.", "Same night", "Overnight claims", "1 dramatic story", "Physically extreme claims; abuse context", "As emotional reappraisal maybe; not a time machine", "Using revision instead of leaving a dangerous home", "Occasionally recommended, high awe", "Memory reconsolidation / reappraisal — not literal past-change", "3/10 as metaphysics; 5/10 as emotional reframing"],
        ["SP-specific techniques", "Assume they love you; ignore silence; 'no free will.'", "Daily", "Weeks to a year+", "Many viral stories", "Obsession, checking, ethical issues; truncated celebrity-SP logs", "Work on self-concept; do not stalk (even the coaches say this)", "Treating a human as an NPC; no-contact as a technique while still monitoring", "Dominant #loass genre; mixed/controversial overall", "Self-fulfilling social behavior, proximity, selective posting", "3/10 ethical-practical rating"],
    ]

    t = doc.add_table(rows=1, cols=6)
    set_col_widths(t, [1.3, 1.5, 1.0, 0.9, 0.9, 0.9])
    header_row(t, ["Method", "How users practice it", "Typical time", "Pos / Neg in set", "Sentiment", "Practical /10"])
    for i, m in enumerate(methods):
        row = t.add_row()
        fill = ROW_ALT if i % 2 else "FFFFFF"
        compact = [m[0], m[1][:90], f"{m[2]}\n{m[3]}", f"+ {m[4]}\n− {m[5][:40]}", m[8][:40], m[10]]
        for j, val in enumerate(compact):
            cell_text(row.cells[j], val, size=7, fill=fill)
    para(doc, "Table 2. Methods. Full tips/mistakes/psychology are in the rows' source notes in Output 8–9.", size=8, italic=True, color=MUTED, space_before=6)

    add_heading_styled(doc, "Notes on the method table (interpretation)", 2)
    for t in [
        "The strongest repeated cluster is not 369 or vision boards. It is: pick an end-state identity, repeat it enough that the old sentence loses airtime, stop using reality as a scoreboard, and — in the better career stories — keep doing the ordinary verbs (apply, negotiate, ship).",
        "Robotic affirming has the loudest fan club and the only explicit harm critique in this set. Treat it as optional attention training.",
        "SATS/visualization is taught with remarkable consistency (short first-person after-scene, drowsy, 3–5 minutes). First-person dated wins are fewer than the teaching posts.",
        "Health and lottery claims are the weakest evidence class in the set.",
    ]:
        bullet(doc, t)

    # OUTPUT 4
    add_page_break(doc)
    add_heading_styled(doc, "Output 4 — 50 practical tips from actual discussions", 1)
    para(
        doc,
        "Each tip is traced to user discussion in this working set. Frequency is approximate across independent posts/replies, not a platform count. 'Why they say it works' is their reason; a short interpretation sits in brackets where useful.",
        size=11,
    )

    tips = [
        ("Stop using the 3D as a scoreboard", "Do not check texts, bank apps, or 'signs' after every session.", "Checking restarts the old story and doubt.", "Detachment / persist", "Very frequent (JUNI, sethmanifests, Rashika, Fawn, gus-adjacent culture)"),
        ("One assumption is enough", "Stand on a single decided sentence (Fawn: devoted boyfriend; Reira: parents are supportive).", "Splitting attention across techniques is efforting.", "Living in the end", "Very frequent"),
        ("Self-concept before the prize", "Morning I-am work, then go about the day (gus 10 min; brigitté autopilot; strawberry client morning+night).", "If you still feel unworthy, the specific desire wobbles.", "Self-concept", "Very frequent"),
        ("Live a normal day", "Work hours with no affirming (gus); 'do not make manifestation your life' (catarina reply).", "Obsession is the block.", "Detachment + action", "Very frequent"),
        ("Affirm, then forget", "Saturate, then drop it (Disaffirmer, tokkiswith, 404DEMI).", "Forgetting is evidence you accepted it (their view).", "RA + detachment", "Frequent"),
        ("Pre-sleep is the prized slot", "10 min RA (gus); 3–5 min SATS scene (divaspiritcleo); Jas's unintentional nightly movie.", "Drowsy mind is less argumentative (community belief).", "SATS / sleep affirming", "Frequent"),
        ("Keep the mental scene short", "5–20 seconds that prove it is done, not the whole movie of how (SATS lesson).", "Long how-scenes keep you in planning/lack.", "SATS", "Frequent in Neville teaching posts"),
        ("Visualize the Tuesday after, not the jackpot", "Accountant, which account, too many clients (Zeion).", "Arrival scenes keep the sum feeling unreal.", "Living in the end", "Occasional but high-signal"),
        ("If you cannot visualize, skip it", "Rory: scripting/deciding/saturating, no images.", "The lever is acceptance, not imagery.", "Scripting / decide", "Occasional"),
        ("Do not switch methods every few days", "AffirmAndAlign: stacks happen because every helper adds a new prescription.", "You never stay with one identity long enough (their view).", "Meta", "Frequent"),
        ("Consume less, apply more", "Fawn watched video after video and was not applying; results moved after she stopped efforting.", "Content is a checking substitute.", "Mistake repair", "Frequent"),
        ("Fit the practice to the calendar you actually have", "gus built around a 6am–3pm job.", "Unrealistic 4-hour rituals get abandoned — unless they are leisure (her night block).", "Routine design", "Occasional detailed"),
        ("Protect work hours", "No active affirming on shift (gus).", "Life has to keep working.", "Habit + action", "Occasional"),
        ("A shower sentence is a popular anchor", "gus: 'I have everything I want, everything I want wants me even more.'", "Existing habit loop.", "Affirmations", "Occasional"),
        ("Five-minute bursts for 'unbelievable' desires", "brigitté saturates only the hard ones.", "Don't turn every want into a project.", "Saturation", "Occasional"),
        ("Rewrite lack sentences into identity sentences", "Living-in-the-end worksheet; TENSHI's old loops ('money is hard').", "You are already repeating something.", "Self-concept", "Frequent"),
        ("Out loud + eyes closed if silent RA feels empty", "manifestmemoir: peace, then 'it always manifests.'", "Adds sensory commitment.", "Affirmations", "Occasional"),
        ("One song, one scene, loop", "Bwitchybabe; also used for a dream date.", "Emotion + repetition without a curriculum.", "Visualization", "Occasional (high reply likes)"),
        ("Record yourself speaking as if it already happened, play at sleep", "soultoscreen reply.", "Voice + drowsy state.", "SATS-adjacent", "Occasional"),
        ("DIY a mind movie if you need a focusing object", "Write affs, TTS, images, music, optional theta/Dispenza track (marr).", "Brain treats it as a memory (their claim).", "Visualization", "Occasional"),
        ("Decide X will happen and enjoy 3D catching up", "nsh11 reply on the hacks thread.", "Removes the project manager stance.", "Decide", "Frequent slogan"),
        ("Playfully treat current circumstances as about to change", "yaznoirxo.", "Reduces threat response to 3D.", "Reframe", "Occasional"),
        ("Normalize the result when it arrives", "Fawn, citing Erik The Power Of I Am: don't make the text a miracle if you already decided he's your boyfriend.", "Shock writes 'this is unlikely' back into the story.", "Persist after movement", "Occasional but high-quality"),
        ("Don't go back and forth after first movement", "Fawn says that delay cost her 4 months to the official relationship.", "Wavering restarts the old identity.", "Persist", "Occasional"),
        ("Someone else's timeline is not yours", "Puffie: 1 month for them ≠ 1 month for you; it can be now.", "Stops comparison checking.", "Mindset", "Frequent"),
        ("You can drop a technique once the assumption is in", "Puffie stopped subliminals because of schedule; says results continued.", "Techniques are scaffolding.", "Meta", "Occasional"),
        ("Ignore other people's base rates when they demotivate you", "4D ignored Reddit 'months between contracts.'", "Social proof of delay becomes an assumption (their view).", "Career", "Occasional"),
        ("After a setback, assume you can get another", "4D after being cut from a contract.", "Prevents crash-out identity.", "Career / persist", "Occasional"),
        ("Applications still matter", "4D had applied in July 2025 for a May 2026 offer.", "Labor markets have lags.", "Habit + action", "Rare in #loass, high value"),
        ("If you want money, create something people buy", "Jack Moses.", "No customer, no cash.", "Action", "Occasional outside bubble"),
        ("Regulated nervous system + consistent action", "godoverunivers, after 2 years of universe-pointing.", "Calm + reps, not an impersonal force (his claim).", "Action / critique", "Occasional"),
        ("Keep it quiet if announcing kills it for you", "Kartik: wishing yes, telling someone no.", "Social pressure / identity lock (interpretation).", "Social", "Occasional"),
        ("Letting go can outperform 'manifesting'", "Lovlin in the mixed thread.", "Release > ritual.", "Detachment", "Occasional independent"),
        ("Treat it as a continuous process, not a 2-day pill", "Santosh reply.", "Unrealistic speed expectations.", "Expectations", "Occasional"),
        ("Write it in more than one place if writing helps", "Vinod: throughout the day, whiteboard, book, combo.", "Cue density.", "Scripting", "Occasional independent"),
        ("Be kind; unplanned people help", "miluvin444's friend secured Bruno Mars seats.", "Social networks are a delivery system (interpretation).", "Action / character", "Occasional"),
        ("Don't script every detail of the how", "Reira didn't specify the parent-change mechanics.", "Over-specifying keeps you in control-anxiety.", "Living in the end", "Frequent"),
        ("Stop waking up expecting the old pattern", "Reira: 'It's different now' instead of 'same fight tomorrow.'", "Morning forecast sets the day's filter.", "Self-concept", "Occasional"),
        ("Ask what the 3D means to you before adding a method", "AffirmAndAlign on SP silence: don't care vs when vs checking every 3 minutes are different problems.", "Wrong prescription, worse stack.", "Meta / coaching quality", "High-signal occasional"),
        ("Checking is allowed if you don't write a tragedy afterwards", "Mirrra (coaching app) — minority nuance vs the usual ban.", "The story after the check is the issue.", "Detachment nuance", "Occasional"),
        ("Do not use affirmations as emergency psychiatry", "simply pen: they failed; he needed a doctor.", "Out of scope.", "Safety", "Rare, essential"),
        ("Do not visualize the thing you fear", "Sol Brah puncture story (confounded) used as a warning.", "Fear rehearsal (interpretation).", "Visualization hygiene", "Occasional"),
        ("Use past success memories as the feeling source", "KULTRA pairs old confidence with today's image.", "Classical conditioning language; closer to sports psych.", "Mental rehearsal", "Occasional"),
        ("Morning 15-minute stack that is actually behavioral", "imonmyrise: 5 min sit with stress then silence, 5 min victory visualization, 5 min gratitude/love/peace.", "Emotional regulation + rehearsal + gratitude.", "Hybrid routine", "Occasional"),
        ("Build self-trust as the desire if you are in coach-land", "HlthWlthAbndnc: 'I fully trust my judgment' plus actually questioning scams.", "Inner work + consumer protection.", "Self-concept + action", "Occasional"),
        ("369 is optional and evidence is thin", "Lisa's 2-day unnamed hit vs delete-your-369 essay.", "Focus ritual at best (interpretation).", "369", "Marketing frequent / logs rare"),
        ("Vision boards are optional and sometimes blamed", "Start-up posts exist; the viral critique says systems kill results.", "Clarifying pictures vs scoreboard (interpretation).", "Vision board", "Mixed"),
        ("Robotic affirming is not the only right way", "dollieviviii GIF about stopping past-self from thinking RA is mandatory; dollymanifest says if you dislike it, skip it.", "Fit > dogma.", "RA", "Occasional pushback"),
        ("Persist after you already have movement", "Multiple SP stories; Fawn's 'stick to the script' when he texted.", "Shock can undo the identity.", "Persist", "Frequent in SP genre"),
        ("If money shows up but doesn't stay, inspect the after-identity", "alignedbysource on Zeion's post.", "Getting ≠ keeping.", "Money / self-concept", "Rare and valuable"),
    ]

    t = doc.add_table(rows=1, cols=5)
    set_col_widths(t, [1.4, 1.7, 1.4, 0.9, 1.1])
    header_row(t, ["Tip", "What users recommend", "Why they say it works", "Technique", "How often in this set"])
    for i, rowv in enumerate(tips):
        row = t.add_row()
        fill = ROW_ALT if i % 2 else "FFFFFF"
        for j, val in enumerate(rowv):
            cell_text(row.cells[j], val, size=7, fill=fill)
    para(doc, "Table 3. Fifty tips grounded in retrieved X discussions.", size=8, italic=True, color=MUTED, space_before=6)

    # OUTPUT 5
    add_page_break(doc)
    add_heading_styled(doc, "Output 5 — Most common mistakes (from the collected posts)", 1)
    para(
        doc,
        "Derived from what users and practitioners in this set actually named, not from a generic LOA article. Order is by how often the problem was independently described.",
        size=11,
    )

    mistakes = [
        ["1. Constant checking / monitoring", "sethmanifests, JUNI, Rashika, Fawn, jennay (story views), Mirrra nuance", "Turns practice into a test. Each empty inbox becomes 'it's not working.'", "Very frequent"],
        ["2. Switching or stacking techniques", "AffirmAndAlign, Fawn efforting, method-school culture", "Seven prescriptions, zero diagnosis. Exhaustion mistaken for discipline.", "Very frequent"],
        ["3. Consuming content instead of applying", "Fawn: video after video; 'ofc not applying'", "Learning becomes a checking ritual.", "Frequent"],
        ["4. Letting current circumstances veto the new story", "Reira, Rashika, PowerManif slogans, 4D vs Reddit", "3D is treated as more real than the decision — which, empirically, it is; the community treats that as the error.", "Very frequent inside #loass"],
        ["5. Obsessing about when / making it an emergency", "Mirrra 'every thought an emergency'; jennay; strawberry client's old morning 'where is it?'", "Time-pressure keeps lack salient.", "Frequent"],
        ["6. Efforting (more techniques = more worthy)", "Fawn's turning point was stopping this", "Identity of 'person who must work to deserve it.'", "Frequent in detailed SP logs"],
        ["7. Going back and forth after first movement", "Fawn (4 extra months)", "Shock and disbelief rewrite the assumption.", "Occasional, high-quality"],
        ["8. Repeating the old story while 'trying'", "receivednow, TENSHI, vee, Reira 2026 advice post", "The dominant loop is still lack.", "Frequent"],
        ["9. Unrealistic speed (2-day pill, instant SP, overnight body)", "Santosh; strawberry body claims; PowerManif 'ignore time'", "Guarantees disappointment or unverifiable posting.", "Frequent in marketing, mixed in logs"],
        ["10. Manifestation without domain action", "Jack Moses; 4D's actual applications; simply pen seeing a doctor", "Career/money/health have non-negotiable verbs.", "Frequent outside bubble; under-taught inside"],
        ["11. Announcing the goal (for some people)", "Kartik", "Personal pattern, not a law.", "Occasional"],
        ["12. Making manifestation your personality", "catarina reply; gus actually still works a job", "Life narrows to techniques.", "Occasional"],
        ["13. Robotic affirming into compulsion", "CYBILL_SHEPARD", "Anxiety loops, not saturation.", "Occasional but serious"],
        ["14. Treating other people as NPCs ('no free will')", "Rashika thread; SP genre; parent Spanish disclaimer about not pulling an ex back into harm", "Ethical and practical risk. Not a 'tip' this report endorses.", "Frequent in SP Twitter"],
        ["15. Using revision/assumption in place of safety", "Cam revision story; Reira abuse background", "Dangerous if taken as the plan.", "Occasional extreme stories"],
        ["16. Blaming the user for every miss (unfalsifiability)", "vee: the method didn't fail, your thoughts did", "Makes the belief system untestable. Convenient for coaches.", "Frequent"],
        ["17. Numbered-method collecting (369, 55x5, 777…)", "Taara listicle vs first-person scarcity; delete-system essay", "Ritual collection without a decision.", "Frequent in classic LOA marketing"],
        ["18. Visualizing the unwanted", "Sol Brah anecdote", "Fear rehearsal.", "Occasional"],
        ["19. Paying coaches instead of testing a simple practice", "itsforevermine / Rashika on scams; HlthWlthAbndnc on judgment", "Outsourcing authority.", "Frequent meta-discussion"],
        ["20. Health and lottery as proof objects", "Coco; Missler recirculation", "Highest awe, weakest evidence.", "Frequent as screenshots, rare as audits"],
    ]
    t = doc.add_table(rows=1, cols=4)
    set_col_widths(t, [1.8, 1.7, 1.8, 1.2])
    header_row(t, ["Mistake", "Where it showed up", "Why users say it hurts", "Frequency in set"])
    for i, rowv in enumerate(mistakes):
        row = t.add_row()
        fill = ROW_ALT if i % 2 else "FFFFFF"
        for j, val in enumerate(rowv):
            cell_text(row.cells[j], val, size=7, fill=fill)
    para(doc, "Table 4. Mistakes named in the collected conversation.", size=8, italic=True, color=MUTED, space_before=6)

    # OUTPUT 6
    add_page_break(doc)
    add_heading_styled(doc, "Output 6 — Community-derived routines (not proven formulas)", 1)
    callout(
        doc,
        "These are assembled from the most commonly reported practices in this working set.",
        "They are not scientifically validated protocols. They omit SP 'no free will' instructions on purpose. If mood is clinically severe, the simply pen case is the relevant data point: see a clinician, do not add affirmations.",
        WARN_FILL,
    )

    add_heading_styled(doc, "5-minute routine", 2)
    para(doc, "Built from: SATS lesson (3–5 min), brigitté's optional 5-min saturation, gus's shower sentence, 404DEMI's decide-and-drop.", size=10, italic=True, color=MUTED)
    numbered(doc, "Pick one desire. State it as done in one sentence (identity, not hoping).")
    numbered(doc, "Close eyes. Replay a 5–20 second first-person scene that would only make sense if it were already true (the SATS 'proof' scene).")
    numbered(doc, "If imagery is hard, skip images and repeat the sentence slowly (Rory / RA users).")
    numbered(doc, "Open eyes. Go do the next ordinary thing. Do not check a scoreboard.")

    add_heading_styled(doc, "10-minute routine", 2)
    para(doc, "Built from: gus wake block (10 min self-concept), gus 10-min pre-sleep RA success post, KULTRA morning rehearsal.", size=10, italic=True, color=MUTED)
    numbered(doc, "Minutes 0–3: self-concept only ('I handle my life well; things work out in ordinary ways'), not the prize.")
    numbered(doc, "Minutes 3–8: either a successful-day rehearsal (KULTRA) or robotic repetition of one desire sentence (gus).")
    numbered(doc, "Minutes 8–10: one after-state beat (Zeion: a boring problem you'd have after the result).")
    numbered(doc, "Stop on time. The community's own failure mode is turning 10 minutes into two hours of checking.")

    add_heading_styled(doc, "Morning routine", 2)
    para(doc, "Built from: brigitté, gus, strawberry client, Reira's 'it's different now,' KULTRA.", size=10, italic=True, color=MUTED)
    numbered(doc, "On waking, do not forecast the old problem (Reira).")
    numbered(doc, "While doing existing morning tasks, run self-concept on autopilot (brigitté) or sit for 10 focused minutes (gus).")
    numbered(doc, "Optional: 5-minute successful-day mental run-through of today's actual tasks (KULTRA — this is mental rehearsal of real work).")
    numbered(doc, "If a 'hard' desire nags, one 5-minute saturation, then stop (brigitté).")
    numbered(doc, "Enter work/school with no technique (gus). Let action carry the day (4D, Taz, Jack Moses).")

    add_heading_styled(doc, "Night routine", 2)
    para(doc, "Built from: SATS school, gus 7–11pm block, Jas unintentional SATS, soultoscreen recording, imonmyrise 15-min hybrid.", size=10, italic=True, color=MUTED)
    numbered(doc, "Optional 5 minutes: name one grateful thing, one person, one peaceful moment (imonmyrise) — as mood hygiene.")
    numbered(doc, "In bed, drowsy: 3–10 minutes of either a short proof-scene (SATS) or quiet RA (gus). Feeling is welcome, not required (dollymanifest).")
    numbered(doc, "Optional: a recording of you speaking as if it is done (soultoscreen) or subliminals as background (gus) — treated here as optional audio scaffolding, not a mechanism.")
    numbered(doc, "Sleep. No phone-checking the desire.")

    add_heading_styled(doc, "30-day experiment (community-shaped)", 2)
    para(doc, "Built from: Mel's 21-day RA experiment structure, 30-day SATS school, AffirmAndAlign's anti-stack rule, 4D's longer job arc, Santosh's 'not a two-day tablet.'", size=10, italic=True, color=MUTED)
    numbered(doc, "Days 1–2: Write one goal in outcome language and one identity sentence. Write three actions the person who already has this would take this month (living-in-the-end as behavior, not costume).")
    numbered(doc, "Pick ONE inner tool only (short SATS, or 10 min RA, or a mind movie). Do not add 369 + scripting + subliminals + revision.")
    numbered(doc, "Daily: 10 minutes morning self-concept + 5–10 minutes night proof-scene or RA.")
    numbered(doc, "Daily: one domain action (send the application, draft the offer, train, message a friend, save the receipt). Jack Moses / 4D constraint.")
    numbered(doc, "Checking rule: if you look, do not narrate lack (Mirrra). Better: scheduled weekly review, not all-day monitoring (sethmanifests).")
    numbered(doc, "If mood crashes: stop the experiment and use real support (simply pen).")
    numbered(doc, "Day 30: review actions taken, skills practiced, opportunities exposed to, mood, and any external changes — separately. Do not collapse all of that into 'the universe did it.'")

    # OUTPUT 7
    add_page_break(doc)
    add_heading_styled(doc, "Output 7 — Twenty detailed or unusual success stories", 1)
    para(doc, "Format: Goal → Method → Duration → Action → Result → Lesson. Each line is a retrieved post. Interpretation is labeled.", size=11)

    stories = [
        (1, "Fawn / SP boyfriend", "Worst-breakup SP list of 135 traits → months of videos/efforting → one decided identity + visualization + stop extra techniques → ~Jan 2025 to official relationship after further 4 months of wavering → reached out, then no-contact, then responded when he did → relationship claimed, ~6 months together → stop efforting and don't waver after movement.", "https://x.com/moonlitfawnwtch/status/2099528101026009435"),
        (2, "4D / contract income", "Second job for school savings → no affirmations; nonduality/money-not-scarce; prior mass applications → wanted 2–3 years; apply Summer 2025; offer May 2026; layoff; new offer in 2 weeks → applied, accepted, stayed employable → income above target → interpretation: labor-market lag + identity + action.", "https://x.com/4DFairyLive/status/2090433910668722502"),
        (3, "Taz / Sony awards work", "Six-figure commissions + resume + pay → identity affirming 'for a bit' until natural → already a marketer → negotiations, campaigns, 18-month project → higher pay / Sony-owned awards show (claimed) → career leverage plus identity.", "https://x.com/ctrlpinkz/status/2083684557711098367"),
        (4, "Puffie / school SP", "Boy who didn't know her name → subliminals + viz + affirming + self-concept; later assumption only → from no results to May confession → hallway proximity → confession → self-concept outran the playlist.", "https://x.com/kook_puff_222/status/2097337023640248330"),
        (5, "Jas / kiss location", "Kiss at a specific place → nightly happy visualization, then forgot → ~2 months → they were friends and went out → kiss at that place → unintentional SATS-like rehearsal.", "https://x.com/papercups111_/status/2021649996479869203"),
        (6, "Reira / parents", "Supportive parents / SP visit welcomed → new story + movie-replace visualization, no formal routine → unspecified months while still at home → continued living there → claims freedom to travel/stay with SP → don't crown circumstances 'final boss.' Safety caveat applies.", "https://x.com/hazeleyesgrace/status/2081410601268691421"),
        (7, "miluvin444 / concert after scam", "Seats after ₱61K scam and sold-out pages → affirm/persist + 'circumstances don't matter' → on-sale window → friend bought tickets; she was filming → seats (extra-show claim weaker) → be kind; social help is a path.", "https://x.com/miluvin444/status/2099424708752199998"),
        (8, "PowerManif / SP after silence", "Call after 2 months zero contact → decided, didn't chase → 2 months → no stalking (claimed) → he called asleep, asked about the gap → popular template; coaching CTA. Thin mechanics.", "https://x.com/PowerManif14522/status/2010264494304551416"),
        (9, "Rory / job later offered", "Job she applied for → affirmed/accepted as hers → months (went to someone else first) → she had applied → offered later; she rejected it → even inside LOA logs, applications exist. Other items in her thread are weaker.", "https://x.com/selfconqueen/status/2069391865506385943"),
        (10, "Rory / math grade", "A in weakest subject → accepted as fact, no visualization → not timed → studying not described → claimed A after failing history → unverifiable; included as 'decide-only' genre.", "https://x.com/selfconqueen/status/2069391865506385943"),
        (11, "gus / 10-minute pre-sleep RA", "Unnamed desire → robotic affirming 10 minutes before sleep → one night emphasized → not stated → 'another success' → community loves the timebox more than the missing details.", "https://x.com/stereonotes/status/2099241434335326663"),
        (12, "strawberry client / timetable & trains", "Better school timetable / shorter day → affirming specific logistical sentences → 'this week' cluster → taking trains anyway → early train, deleted class (claimed) → small-logistics hits are the most psychologically ordinary (selective attention + chance).", "https://x.com/strawbe44ym1lk/status/2098071095333261748"),
        (13, "strawberry client / stop chasing", "Felt whole, less morning 'where is it?' → morning+night self-concept after coaching → during coaching period → none extra → anxiety drop → this may be the real product: less rumination.", "https://x.com/strawbe44ym1lk/status/2098071095333261748"),
        (14, "marr / mind movie", "SP focus → DIY mind movie → claims immediate while making it → editing work → unspecified fulfillment → recipe > result.", "https://x.com/raiinmarr/status/2091680336799273208"),
        (15, "Lisa / 369", "One asked-for thing → 369 method → 2 days → not stated → unnamed thing arrived → weakest success log; included because 369 is culturally huge and first-person hits were scarce.", "https://x.com/DoubleTakeLisa/status/1955710182589190286"),
        (16, "Alisha / two job offers", "A job → 'I manifested a job' → not specified → not specified → two offers (one-liner) → low detail, independent-ish.", "https://x.com/070Alisha/status/2096556432825221467"),
        (17, "colleague-attributed promotion", "Promotion → colleague said she manifested it; she didn't expect it so soon → not a method post → she was already working, even showed up in an N95 → promotion → other people will label your prep as manifestation.", "https://x.com/taylormadelt_/status/2099458508156547526"),
        (18, "Skit / SATS everything", "Money, people, messages, apologies, jobs → SATS 'never failed' → lifetime claim → not specified → global success claim → enthusiasm specimen, not an experiment.", "https://x.com/skitskite/status/2093782794757460092"),
        (19, "Sol Brah / van after puncture", "Avoid puncture / then get a lift → don't visualize the puncture; then visualize a van → minutes → walking a bike on a country road → puncture then a van (claimed) → coincidence-prone; moral is fear-rehearsal.", "https://x.com/SolBrah/status/2099069288409956759"),
        (20, "godoverunivers / after LOA failed", "Revenue → stopped pointing at 'the universe,' pointed at God, kept scripted action + nervous system work → 2 years vs 4 months → consistent action → claims $250k → interpretation: attribution shift + action; commercial bio. Included as a conversion-from-LOA story.", "https://x.com/godoverunivers/status/2094521130933792789"),
    ]

    for num, title, body, link in stories:
        add_heading_styled(doc, f"{num}. {title}", 3)
        para(doc, body, size=11)
        hp = doc.add_paragraph()
        hp.paragraph_format.space_after = Pt(8)
        r = hp.add_run("Source: ")
        set_run_font(r, size=9, italic=True, color=MUTED)
        add_hyperlink(hp, link, link, size=9)

    # OUTPUT 8
    add_page_break(doc)
    add_heading_styled(doc, "Output 8 — What actually seems useful", 1)

    add_heading_styled(doc, "Strongest practical ideas", 2)
    para(
        doc,
        "These showed up in multiple independent stories and also map onto known psychology. They may help via mindset, goal clarity, motivation, behavior, or habit — without requiring a metaphysical engine.",
        size=11,
    )
    for t in [
        "A written or spoken end-state (one sentence, a short scene, a list of standards) clarifies what 'done' looks like. Fawn's 135-item list is extreme; the function is standards, not magic.",
        "Daily identity rehearsal (self-concept) is ordinary self-efficacy work. Morning and night bookends are the modal schedule.",
        "Mental rehearsal of the performance or the after-state (KULTRA, Zeion, SATS teaching) matches sports and implementation-intention research more than it matches lottery metaphysics.",
        "Reducing obsessive checking is anxiety hygiene. People feel better and behave less erratically when they stop refreshing the scoreboard.",
        "Detachment-as-living-your-life restores behavioral activation: work, sleep, friends, applications.",
        "In career/money stories that survive scrutiny, someone applied, negotiated, shipped, or was already in the seat (4D, Taz, miluvin444's friend, Jack Moses).",
        "A 5–10 minute cap prevents the practice from becoming the life (AffirmAndAlign's stack warning).",
        "After a setback, a replacement assumption ('I can get another contract') is closer to resilience than to sorcery.",
    ]:
        bullet(doc, t)

    add_heading_styled(doc, "Popular manifestation beliefs (hard to verify)", 2)
    for t in [
        "Reality must mirror a persisted assumption; silence is never information.",
        "SATS in the drowsy state impresses the subconscious, which then 'hardens into fact.'",
        "Robotic repetition forces 3D to comply, feeling optional.",
        "Revision changes the past or swaps timelines overnight.",
        "Other people have no free will in 'your reality' (SP Twitter).",
        "Circumstances and time do not matter, including sold-out events and medical diagnoses.",
        "Money can land 'from thin air' as the preferred path.",
    ]:
        bullet(doc, t)
    para(doc, "Interpretation: these are the load-bearing myths of #loass. They are widely repeated. This research did not find a way to separate them from coincidence, selection bias, and coaching incentives.", size=11, italic=True)

    add_heading_styled(doc, "Mixed / controversial practices", 2)
    for t in [
        "Robotic affirming: beloved attention tool vs OCD/cortisol critique.",
        "369 / 55x5 / 777 writing: huge marketing footprint, almost no reconstructable logs in this window.",
        "Vision boards: still started by some; a high-view essay says delete them.",
        "Subliminals: used at night, then often dropped.",
        "SP manifestation: the main genre, the main ethical problem, and full of proximity/social-media confounders.",
        "Ignoring 3D entirely vs the newer 'you may check if you don't spiral' nuance.",
        "Telling others your goal: Kartik says it kills it; coaches tell thousands publicly.",
        "Gratitude journals: merchandised constantly, almost absent as first-person engines of specific results here.",
    ]:
        bullet(doc, t)

    add_heading_styled(doc, "Likely hype", 2)
    for t in [
        "Shane Missler lottery recirculated as nightly-SATS proof (1.5k likes in Aug 2026).",
        "Instant appearance change, shrinking noses, dream bodies without behavior (testimonial screenshots).",
        "Manifesting other people's cancer, ICU, diabetes 'quickly.'",
        "Overnight timeline swaps / waking up on the same date in a new life.",
        "Celebrity SP texts after a year of story-view tracking, posted without a full method.",
        "'I never fail' global claims with no dates.",
        "Paid 1:1 funnels that end every thread ('DM ELEVATE,' 'no refunds,' 'grab your spot').",
        "Any system that explains all failures as the user's secret lack of faith (unfalsifiable, coach-protective).",
    ]:
        bullet(doc, t)

    # OUTPUT 9
    add_page_break(doc)
    add_heading_styled(doc, "Output 9 — Manifestation playbook (community-derived)", 1)
    para(
        doc,
        "A concise playbook from the strongest recurring experiences, rewritten so a skeptical reader can actually run it. Inner tools are optional scaffolding. Domain action is not.",
        size=11,
    )

    play = [
        ("Goal setting", "Users who were specific did better logs than users who posted 'I manifested my beautiful life.' Fawn listed traits. 4D named contract-style work and a savings target. Zeion warns against only naming a dramatic dollar. Write: the outcome, the identity, and 3 behaviors the 'after' person already does."),
        ("Visualization", "Standard #loass form is SATS: drowsy, first-person, a tiny proof scene, 3–5 minutes. Alternative: morning successful-day rehearsal of real tasks (KULTRA). Alternative: one song, one scene. Skip imagery if you cannot image (Rory). Do not rehearse the fear scene (Sol Brah's moral, regardless of the puncture)."),
        ("Affirmations", "Two schools: (1) robotic repetition to occupy thought (gus, dollymanifest); (2) rampage identity until it is not up for debate (brigitté). Feeling is optional in school 1, prized in Neville school. Caps beat 10k/day. Out-loud + eyes-closed is a minority preference. Stop if it becomes compulsion (CYBILL)."),
        ("Self-concept", "The most repeated 'unlock.' Morning and night I-am work about being a person things work out for, not only about the prize. Fawn originally rolled her eyes at it, then treated it as load-bearing. Strawberry client: SC ended the morning 'where is it?' panic."),
        ("Gratitude", "Thin as a manifestation engine in this sample; present as a 5-minute night anchor in hybrid rituals. Use it as mood practice. Do not buy a 1,000-page deck and call it a method."),
        ("Journaling / scripting", "Useful forms: standards list (Fawn), living-in-the-end sentence swaps (divaspiritcleo), a simple 30-day log of actions vs coincidences. Weak forms: 369 as superstition, scripting at 6am because a course said so (delete-system essay)."),
        ("Detachment", "Not 'I don't care.' It is: decide, then stop extra attending (404DEMI); work your shift without affirming (gus); don't monitor 24/7 (sethmanifests). Fawn's version was stopping the extra videos. Lovlin's independent version: letting go worked when 'manifestation' didn't."),
        ("Action", "Non-optional for jobs, money, health, skills. 4D applied. Taz was already a marketer. miluvin444 had a friend in the queue. Jack Moses: make a thing people buy. simply pen: see a doctor. Living in the end, interpreted charitably, means doing today's version of the after-life (divaspiritcleo's own prompt: what would today-me do differently?)."),
        ("Progress tracking", "Do not track like a slot machine. Weekly: actions taken, mood, rumination minutes, opportunities exposed to, and any external change — as separate columns. That is how you stop confirmation bias from grading the test."),
        ("Weekly review", "AffirmAndAlign's questions: What do I actually believe? What did I already do? What triggered me? Which technique did I enjoy vs force? How much time did I really have? If the week was all checking and no action, that is the finding."),
    ]
    for title, body in play:
        add_heading_styled(doc, title, 3)
        para(doc, body, size=11)

    # OUTPUT 10
    add_page_break(doc)
    add_heading_styled(doc, "Output 10 — Final research insights", 1)

    add_heading_styled(doc, "Top 10 methods", 2)
    for i, name in enumerate([
        "Self-concept / identity sentences (morning + night)",
        "Decide-and-live (drop the project-manager stance)",
        "Stop checking / weekly review instead of all-day monitoring",
        "Short pre-sleep SATS or 10-min RA (optional imagery)",
        "After-state visualization (boring Tuesday after the result)",
        "Persist with one sentence instead of method-hopping",
        "Domain action (apply, ship, ask, train, get care)",
        "Mental rehearsal of today's real tasks (KULTRA-style)",
        "Robotic affirming as optional attention control — with a compulsion off-ramp",
        "Social/ordinary channels (friends, jobs you already have, school proximity) — usually unlabeled '3D'",
    ], 1):
        numbered(doc, name)

    add_heading_styled(doc, "Top 20 tips (compressed)", 2)
    for t in [
        "One sentence. One tool. One month.",
        "Self-concept first, prize second.",
        "Bookend the day; leave the middle for life.",
        "Scene = proof it happened, not how it happens.",
        "If you cannot see images, repeat or write.",
        "Do not collect 369/55x5/777 unless you enjoy writing.",
        "Checking is a different hobby.",
        "If you check, don't narrate doom.",
        "Stop the YouTube university.",
        "After first movement, act bored, not shocked.",
        "Other people's timelines are not data about you — and not laws of physics either.",
        "Applications can take 10 months. That is a labor market.",
        "Make a thing people will pay for if money is the goal.",
        "Be someone people want to help.",
        "Don't announce if announcing poisons you.",
        "Letting go is a valid method.",
        "Affirmations are not emergency care.",
        "Don't rehearse the fear clip.",
        "If money arrives and leaves, inspect the after-identity.",
        "Unfalsifiable slogans ('you didn't persist') are coach-protection, not measurement.",
    ]:
        bullet(doc, t)

    add_heading_styled(doc, "Top 10 mistakes", 2)
    for t in [
        "Checking all day.",
        "Stacking seven methods.",
        "Content instead of practice.",
        "Efforting to deserve it.",
        "Wavering after the first text/offer.",
        "Treating 2 days as a fair test — or 2 years of checking as 'I persisted.'",
        "No domain action.",
        "SP-as-NPC / no-free-will talk.",
        "Health and lottery screenshots as epistemology.",
        "Paying for certainty.",
    ]:
        numbered(doc, t)

    add_heading_styled(doc, "Top 10 most interesting success stories (short list)", 2)
    for t in [
        "Fawn's year-shaped SP log with a clear stop-efforting turn.",
        "4D's job: apply, wait, get, lose, get again, no affirmations.",
        "Taz's already-employed identity shift into a bigger project.",
        "Jas's unintentional nightly scene and later kiss.",
        "Puffie's hallway SP plus dropping subliminals.",
        "Reira's parent-story swap (with safety caveats).",
        "miluvin444's scam-to-seats via a friend.",
        "gus's 4-hour-around-a-job routine as a lifestyle specimen.",
        "Zeion's after-money visualization plus the keeping-money reply.",
        "godoverunivers's two-year miss, then action-attributed revenue (commercial, but rare as a miss).",
    ]:
        numbered(doc, t)

    add_heading_styled(doc, "What successful users in this set have in common", 2)
    for t in [
        "A decided end-state, usually in present/identity language.",
        "Some repetition vehicle (RA, scene, list, rampage) — except the decide-and-drop subset, who still had a clean decision.",
        "A story about reducing panic: less checking, less content, less technique-stacking.",
        "Time measured in weeks/months, not hours — even when they say 'instant is possible.'",
        "In non-SP domains, a practical channel (job, friend, existing role, applications).",
        "Willingness to keep the new sentence when 3D is rude — which is indistinguishable from stubborn goal pursuit.",
        "Posting hits. (Selection bias is itself a finding.)",
    ]:
        bullet(doc, t)

    add_heading_styled(doc, "What unsuccessful users in this set have in common", 2)
    for t in [
        "They say the labeled thing ('manifestation,' 'affirmations,' 'self-help videos') did not move the needle (Nitul, Amina, Lovlin-on-manifestation, simply pen).",
        "Or they did the inner work as a closed loop: checking, stacking, consuming, efforting (the mistake posts).",
        "Or they needed a different tool (medicine, a product, a regulated nervous system, leaving a situation).",
        "Inside #loass, unsuccessful users are often told they were never really doing it — so true negatives are under-counted.",
        "Independent mixed threads (Shravika) show a split: always / never / letting-go-instead / can't-answer-except-by-faith.",
    ]:
        bullet(doc, t)

    add_heading_styled(doc, "Practices worth experimenting with", 2)
    for t in [
        "10 minutes identity + 5 minutes after-state scene, 30 days, one goal, plus weekly action review.",
        "KULTRA-style morning rehearsal of the actual day's hard conversations.",
        "A checking fast: notifications off for the scoreboard app.",
        "Writing the old loop sentence and the new one side by side (TENSHI).",
        "Living-in-the-end as behavior: one daily act from the after-life.",
        "If rumination is the problem, treat detachment as CBT thought-stopping/scheduling, not as magic.",
    ]:
        bullet(doc, t)

    add_heading_styled(doc, "Claims that should be treated skeptically", 2)
    for t in [
        "Lottery SATS.",
        "Cancer/ICU/diabetes flipped by assumption alone.",
        "Bodies and faces changing in days without behavior or medicine.",
        "Timeline jumping / same-date wakeups.",
        "Celebrity mind control.",
        "'No free will' as a romance strategy.",
        "'Circumstances never matter' as a blanket rule (sold-out arenas, visas, disease, violence).",
        "Any coach who cannot describe a miss except as your lack of persist.",
        "Two-day numbered rituals as causal engines.",
        "Global 'I never fail' biographies.",
    ]:
        bullet(doc, t)

    add_heading_styled(doc, "Final community-based manifestation framework", 2)
    mixed_para(
        doc,
        [
            ("Direct synthesis of the working set, labeled as interpretation. ", {"size": 11, "italic": True}),
            (
                "People on X who report the cleanest, least magical-feeling wins do four things that look like psychology and one thing that looks like folklore. The four: they specify an end-state; they rehearse it until it is less emotionally loud; they stop refreshing the scoreboard; they keep taking the ordinary actions available in that domain. The folklore: they talk as if an inner assumption must print into the world. You can run the four without buying the fifth. You cannot, on this evidence, justify the fifth as a proven law.",
                {"size": 11},
            ),
        ],
    )
    para(doc, "", space_after=4)
    mixed_para(
        doc,
        [
            (
                "If you want a single sentence the community would recognize and a skeptic can still use: decide what done looks like, occupy that identity in short daily reps, live the rest of the day, do the verbs, and judge the month by actions and exposure — not by angel numbers.",
                {"size": 11, "bold": True},
            )
        ],
    )

    add_heading_styled(doc, "Appendix A — Search notes", 2)
    para(
        doc,
        "Queries included first-person success and failure language, method names (SATS, robotic affirming, 369, vision board, gratitude, self-concept, living in the end, subliminals, scripting), and community tags (#loass). SATS queries were polluted by Bitcoin 'sats' faucet bots and were filtered. Latest-mode searches were flooded with fandom and coaching CTAs; the highest-information hits often came from phrase searches such as 'how I manifested,' min_faves filters, semantic search for daily routines, and opening image attachments on viral SP threads. Older recirculations (Missler lottery; May 2025 'method didn't fail' posts) were included only when 2026 users still used them as authority.",
        size=11,
    )

    add_heading_styled(doc, "Appendix B — Ethics", 2)
    para(
        doc,
        "SP techniques that treat another adult as an object with no free will are widely taught on X and are not endorsed here. Stories involving abuse, grounding, or medical crisis are quoted as community artifacts, not as care plans. Nothing in this document is medical, legal, or financial advice.",
        size=11,
    )

    add_heading_styled(doc, "Appendix C — What this report is not", 2)
    for t in [
        "Not a claim that 'thousands of posts were hand-coded.' The set is a retrieved, de-duplicated, ranked working sample.",
        "Not a clinical trial of SATS or 369.",
        "Not an endorsement of any coach named.",
        "Not a license to skip medicine, visas, or other people's consent.",
    ]:
        bullet(doc, t)

    out = "/home/ubuntu/LOA/X_Manifestation_Community_Intelligence_Report.docx"
    doc.save(out)
    print("Wrote", out, "posts", len(POSTS))


if __name__ == "__main__":
    build()
