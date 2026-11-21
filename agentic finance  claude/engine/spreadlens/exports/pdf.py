"""PDF review pack rendered from one immutable snapshot (ReportLab platypus)."""

from __future__ import annotations

import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

STYLES = getSampleStyleSheet()
SMALL = ParagraphStyle("small", parent=STYLES["BodyText"], fontSize=7.5, leading=9.5)
BODY = ParagraphStyle("body", parent=STYLES["BodyText"], fontSize=9, leading=12)
H1 = ParagraphStyle("h1", parent=STYLES["Heading1"], fontSize=15)
H2 = ParagraphStyle("h2", parent=STYLES["Heading2"], fontSize=11.5, spaceBefore=8)


def p(text: object, style: ParagraphStyle = SMALL) -> Paragraph:
    return Paragraph(escape("" if text is None else str(text)), style)


def _fmt(v: str | None) -> str:
    if v is None:
        return "n/a"
    neg = v.startswith("-")
    a = v.lstrip("-")
    i, _, f = a.partition(".")
    s = f"{int(i):,}" + (f".{f}" if f else "")
    return f"({s})" if neg else s


def _table(data: list[list], widths: list[float], header: bool = True) -> Table:
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#C9CED6")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("FONTSIZE", (0, 0), (-1, -1), 7.5)]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3A5F")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white)]
    t.setStyle(TableStyle(style))
    return t


def render_pdf(snap: dict, pack: dict, status: str) -> bytes:
    buf = io.BytesIO()
    draft = status != "approved"
    footer = (f"{'UNREVIEWED DRAFT — not signed off' if draft else 'APPROVED'} • {snap['company']['name']} • "
              f"spread v{snap['spread_version']} • snapshot {snap['content_hash'][:16]}")

    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawString(12 * mm, 8 * mm, footer)
        canvas.drawRightString(doc.pagesize[0] - 12 * mm, 8 * mm, f"Page {doc.page}")
        if draft:
            canvas.setFillColor(colors.Color(0.85, 0.1, 0.1, alpha=0.10))
            canvas.setFont("Helvetica-Bold", 70)
            canvas.translate(doc.pagesize[0] / 2, doc.pagesize[1] / 2)
            canvas.rotate(30)
            canvas.drawCentredString(0, 0, "DRAFT")
        canvas.restoreState()

    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=12 * mm, rightMargin=12 * mm, topMargin=12 * mm, bottomMargin=14 * mm,
                            title=f"SpreadLens review pack — {snap['company']['name']}", author="SpreadLens AI")
    W = landscape(A4)[0] - 24 * mm
    story: list = []
    story.append(Paragraph(escape(f"Analyst review pack — {snap['company']['name']}"), H1))
    status_line = ("UNREVIEWED DRAFT: figures, mappings and exceptions have not been signed off by a reviewer. Unresolved items are listed below."
                   if draft else f"APPROVED by {snap['approval']['user']} ({snap['approval']['role']}) on {snap['approval']['at'][:10]} for spread version {snap['spread_version']}.")
    story.append(Paragraph(f"<font color='{'#B42318' if draft else '#067647'}'><b>{escape(status_line)}</b></font>", BODY))
    story.append(Spacer(1, 4))
    meta = [["Entity", snap["entity"]["name"], "Scope", snap["entity"]["scope"]],
            ["Currency / unit", f"{snap['currency']} {snap['display_scale']}", "Periods", ", ".join(snap["periods"])],
            ["Spread version", str(snap["spread_version"]), "Snapshot hash", snap["content_hash"][:32]],
            ["Prepared by", snap["created_by"], "Documents", "; ".join(d["filename"] for d in snap["documents"])]]
    story.append(_table([[p(c) for c in r] for r in meta], [W * 0.12, W * 0.38, W * 0.12, W * 0.38], header=False))
    story.append(Spacer(1, 4))
    story.append(p(snap["disclaimer"], BODY))

    story.append(Paragraph("Financial summary", H2))
    for sec in pack.get("sections", []):
        if sec["heading"] != "Financial trends":
            continue
        for c in sec["claims"]:
            story.append(p("• " + c["text"] + (f"  [refs: {', '.join(r[:8] for r in c['refs'])}]" if c["refs"] else ""), BODY))

    for key, title in (("balance_sheet", "Balance sheet"), ("income_statement", "Income statement"), ("cash_flow", "Cash flow statement")):
        st = snap["statements"][key]
        story.append(Paragraph(f"Standardised {title.lower()} ({snap['currency']} {snap['display_scale']})", H2))
        if not st["available"]:
            story.append(p("Not provided in the uploaded documents.", BODY))
            continue
        rows = [[p("Line item"), p("Original label")] + [p(x) for x in snap["periods"]] + [p("Origin"), p("Source")]]
        for line in st["lines"]:
            cells = [line["cells"].get(x) for x in snap["periods"]]
            labels = sorted({c.get("label") for c in line["cells"].values() if c.get("label")})
            rows.append([p(line["label"]), p(" / ".join(labels))]
                        + [p(_fmt(c["value"]) if c else "n/a") for c in cells]
                        + [p(", ".join(sorted({c["origin"] for c in cells if c}))), p("; ".join(c["source"] for c in cells if c)[:80])])
        n = len(snap["periods"])
        story.append(_table(rows, [W * 0.22, W * 0.2] + [W * 0.1] * n + [W * 0.08, W * (0.5 - 0.1 * n)]))
        if st["unmapped_rows"]:
            story.append(p(f"{len(st['unmapped_rows'])} unmapped source figures are listed in the workbook (kept visible, not standardised).", SMALL))

    story.append(PageBreak())
    story.append(Paragraph("Selected ratios", H2))
    rows = [[p("Metric"), p("Period"), p("Value"), p("Status"), p("Formula"), p("Limitations / explanation")]]
    for m in snap["metrics"]:
        rows.append([p(m["title"]), p(m["period_end"]), p(m["display_value"] or "n/a"), p(m["status"].replace("_", " ")),
                     p(m["formula"]), p("; ".join(m["limitations"]) or m["explanation"])])
    story.append(_table(rows, [W * 0.16, W * 0.09, W * 0.08, W * 0.12, W * 0.25, W * 0.30]))

    story.append(Paragraph("Validation results and major exceptions", H2))
    rows = [[p("Rule"), p("Period"), p("Status"), p("Severity"), p("Difference (base units)"), p("Explanation")]]
    for v in snap["validations"]:
        if v["status"] in ("fail", "requires_review", "insufficient_data"):
            rows.append([p(f"{v['rule_id']} {v['title']}"), p(v["period_end"]), p(v["status"]), p(v["severity"]),
                         p(v["difference"] or ""), p(v["explanation"])])
    passed = sum(1 for v in snap["validations"] if v["status"] == "pass")
    story.append(p(f"{passed} checks passed. Passing arithmetic checks does not prove financial correctness.", BODY))
    if len(rows) > 1:
        story.append(_table(rows, [W * 0.25, W * 0.08, W * 0.1, W * 0.07, W * 0.13, W * 0.37]))
    rows = [[p("Severity"), p("Exception"), p("Status"), p("Notes")]]
    for e in snap["exceptions"]:
        if e["severity"] in ("critical", "warning") and e["status"] in ("open", "explained"):
            rows.append([p(e["severity"]), p(e["title"]), p(e["status"]), p(e["resolution_note"] or e["agent_explanation"] or e["detail"])])
    if len(rows) > 1:
        story.append(Spacer(1, 4))
        story.append(_table(rows, [W * 0.08, W * 0.37, W * 0.08, W * 0.47]))

    story.append(Paragraph("Comparability limitations", H2))
    for t in snap["comparability"]:
        story.append(p("• " + t, BODY))
    story.append(Paragraph("Analyst adjustments", H2))
    if not snap["adjustments"]:
        story.append(p("No analyst adjustments.", BODY))
    else:
        rows = [[p("When"), p("User"), p("Action"), p("Item"), p("Before"), p("After"), p("Reason")]]
        for a in snap["adjustments"]:
            rows.append([p(a["at"][:16]), p(a["user"]), p(a["action"]), p(a["label"] or a["field"]), p(a["before"]), p(a["after"]), p(a["reason"])])
        story.append(_table(rows, [W * 0.1, W * 0.1, W * 0.1, W * 0.18, W * 0.14, W * 0.14, W * 0.24]))
    story.append(Paragraph("Questions requiring review", H2))
    for sec in pack.get("sections", []):
        if sec["heading"] == "Questions requiring review":
            for c in sec["claims"]:
                story.append(p("• " + c["text"], BODY))
    story.append(Paragraph("Evidence references", H2))
    story.append(p("Every figure above links to an observation ID; the workbook's 'Source References' sheet lists each one with its "
                   "raw source text, document, page and bounding box (or worksheet cell), extraction method and transformations.", BODY))
    story.append(Paragraph("Reviewer and snapshot details", H2))
    rows = [[p("Decision"), p("User"), p("Role"), p("Version"), p("Stale"), p("When"), p("Comment")]]
    for d in snap["decisions"]:
        rows.append([p(d["decision"]), p(d["user"]), p(d["role"]), p(d["version"]), p("yes" if d["stale"] else "no"), p(d["at"][:16]), p(d["comment"] or "")])
    story.append(_table(rows, [W * 0.12, W * 0.14, W * 0.08, W * 0.07, W * 0.06, W * 0.13, W * 0.40]))
    story.append(p(f"Snapshot content hash: {snap['content_hash']}. Taxonomy {snap['versions']['taxonomy']}, ruleset {snap['versions']['ruleset']}, "
                   f"metrics {snap['versions']['metrics']}.", BODY))
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buf.getvalue()
