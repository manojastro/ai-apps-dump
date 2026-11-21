"""Excel workbook rendered from one immutable snapshot.

- All untrusted text passes through excel_safe_text (formula / DDE injection neutralised).
- Values are written as numbers only when Decimal -> float is exact enough for Excel (<=15 significant
  digits); otherwise the exact decimal string is written and the cell is marked. Every sheet also keeps
  exact decimal strings in the Source References sheet.
- Extracted, derived and adjusted values are distinguished by fill colour (legend on Read Me).
"""

from __future__ import annotations

import io
from decimal import Decimal

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from spreadlens.numeric.decimal_utils import excel_safe
from spreadlens.security.sanitize import excel_safe_text

FILL = {
    "reported": PatternFill("solid", fgColor="FFFFFF"),
    "derived": PatternFill("solid", fgColor="E8F0FE"),
    "adjusted": PatternFill("solid", fgColor="FFF4D6"),
    "missing": PatternFill("solid", fgColor="F3F3F3"),
    "header": PatternFill("solid", fgColor="1F3A5F"),
    "draft": PatternFill("solid", fgColor="FDE2E1"),
}
NUMFMT = '#,##0.00;(#,##0.00);"-"'
SHEETS = {"balance_sheet": "Balance Sheet", "income_statement": "Income Statement", "cash_flow": "Cash Flow"}


def _t(v: object) -> str:
    return excel_safe_text(v)


def _header(ws: Worksheet, row: int, values: list[str]) -> None:
    for i, v in enumerate(values, start=1):
        c = ws.cell(row=row, column=i, value=_t(v))
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = FILL["header"]
        c.alignment = Alignment(wrap_text=True, vertical="center")


def _num(ws: Worksheet, row: int, col: int, value: str | None, origin: str = "reported", fmt: str = NUMFMT) -> None:
    cell = ws.cell(row=row, column=col)
    if value is None:
        cell.value = "n/a"
        cell.fill = FILL["missing"]
        return
    d = Decimal(value)
    if excel_safe(d):
        cell.value = float(d)
        cell.number_format = fmt
    else:
        cell.value = format(d, "f")  # exact text: a float would lose precision
        cell.font = Font(italic=True)
    cell.fill = FILL.get(origin, FILL["reported"])


def _widths(ws: Worksheet, widths: list[int]) -> None:
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def render_workbook(snap: dict, pack: dict, status: str) -> bytes:
    wb = Workbook()
    draft = status != "approved"
    ws = wb.active
    ws.title = "Read Me"
    lines = [
        ("SpreadLens AI — analyst review workbook", True),
        ("UNREVIEWED DRAFT — figures and exceptions have not been signed off" if draft else
         f"APPROVED snapshot — signed off by {snap['approval']['user']} on {snap['approval']['at'][:10]}", True),
        (f"Company: {snap['company']['name']}", False),
        (f"Entity / scope: {snap['entity']['name']} ({snap['entity']['scope']})", False),
        (f"Currency and unit: {snap['currency']} {snap['display_scale']} (monetary lines); EPS in {snap['currency']} per share", False),
        (f"Snapshot: spread version {snap['spread_version']}, content hash {snap['content_hash']}", False),
        (f"Taxonomy {snap['versions']['taxonomy']}, ruleset {snap['versions']['ruleset']}, metrics {snap['versions']['metrics']}", False),
        ("", False),
        ("Legend: white = extracted (reported) value; blue = derived value; amber = analyst-adjusted value; grey 'n/a' = not available.", False),
        ("Precision: values are written as numbers when they fit Excel's 15-significant-digit precision; otherwise as exact text (italic).", False),
        ("Exact source strings and normalised base-unit values are in 'Source References'.", False),
        ("", False),
        (snap["disclaimer"], False),
        ("", False),
        ("Assumptions and limitations:", True),
        *[(f"• {x}", False) for x in snap["comparability"]],
    ]
    for i, (t, bold) in enumerate(lines, start=1):
        c = ws.cell(row=i, column=1, value=_t(t))
        c.font = Font(bold=bold, color="B42318" if (i == 2 and draft) else None)
        if i == 2 and draft:
            c.fill = FILL["draft"]
    _widths(ws, [140])

    ws = wb.create_sheet("Metadata")
    _header(ws, 1, ["Field", "Value"])
    meta = [("Company", snap["company"]["name"]), ("Reporting entity", snap["entity"]["name"]), ("Scope", snap["entity"]["scope"]),
            ("Currency", snap["currency"]), ("Display unit", snap["display_scale"]), ("Periods", ", ".join(snap["periods"])),
            ("Review status", "Approved" if not draft else "Unreviewed draft"), ("Spread version", str(snap["spread_version"])),
            ("Snapshot hash", snap["content_hash"]), ("Prepared by", snap["created_by"])]
    for d in snap["documents"]:
        meta.append(("Source document", f"{d['filename']} (v{d['version_no']}, sha256 {d['sha256'][:16]}…, processing: {d['agent_mode']})"))
    for i, (k, v) in enumerate(meta, start=2):
        ws.cell(row=i, column=1, value=_t(k))
        ws.cell(row=i, column=2, value=_t(v))
    _widths(ws, [24, 110])
    ws.freeze_panes = "A2"

    for key, title in SHEETS.items():
        ws = wb.create_sheet(title)
        st = snap["statements"][key]
        per = snap["periods"]
        _header(ws, 1, ["Canonical item", "Code", "Original label"] + [f"{p} ({snap['display_scale']})" for p in per] + ["Origin", "Sources"])
        r = 2
        if not st["available"]:
            ws.cell(row=2, column=1, value="Statement not provided in the uploaded documents.")
        for line in st["lines"]:
            ws.cell(row=r, column=1, value=_t(line["label"])).font = Font(bold=line["is_total"])
            ws.cell(row=r, column=2, value=_t(line["code"]))
            labels = {c.get("label") for c in line["cells"].values() if c.get("label")}
            ws.cell(row=r, column=3, value=_t(" / ".join(sorted(labels))))
            origins = set()
            for j, p in enumerate(per):
                c = line["cells"].get(p)
                origin = c["origin"] if c else "reported"
                origins.add(origin)
                _num(ws, r, 4 + j, c["value"] if c else None, origin, "0.00" if line["unit"] == "eps" else NUMFMT)
            ws.cell(row=r, column=4 + len(per), value=_t(", ".join(sorted(origins))))
            ws.cell(row=r, column=5 + len(per), value=_t("; ".join(c["source"] for c in line["cells"].values())))
            r += 1
        if st["unmapped_rows"]:
            r += 1
            ws.cell(row=r, column=1, value="Unmapped source rows (kept visible, not standardised)").font = Font(bold=True)
            r += 1
            for u in st["unmapped_rows"]:
                ws.cell(row=r, column=1, value=_t(u["label"]))
                ws.cell(row=r, column=2, value=_t(u["period_end"]))
                _num(ws, r, 3, u["value"])
                ws.cell(row=r, column=4, value=_t(u["state"]))
                ws.cell(row=r, column=5, value=_t(u["source"]))
                r += 1
        # safe generated formula: a check column only for totals of the balance sheet
        if key == "balance_sheet":
            codes = {line["code"]: i + 2 for i, line in enumerate(st["lines"])}
            if "bs.total_assets" in codes and "bs.total_equity_and_liabilities" in codes:
                r += 1
                ws.cell(row=r, column=1, value="Check: total assets less total equity and liabilities (formula)")
                for j in range(len(per)):
                    col = get_column_letter(4 + j)
                    c = ws.cell(row=r, column=4 + j, value=f"={col}{codes['bs.total_assets']}-{col}{codes['bs.total_equity_and_liabilities']}")
                    c.number_format = NUMFMT
        _widths(ws, [44, 30, 40] + [18] * len(per) + [14, 50])
        ws.freeze_panes = "D2"
        ws.auto_filter.ref = f"A1:{get_column_letter(5 + len(per))}{max(r, 2)}"

    ws = wb.create_sheet("Ratios and Trends")
    _header(ws, 1, ["Metric", "Period", "Value", "Unit", "Status", "Formula", "Explanation", "Limitations", "Input IDs"])
    for i, m in enumerate(snap["metrics"], start=2):
        ws.cell(row=i, column=1, value=_t(m["title"]))
        ws.cell(row=i, column=2, value=_t(m["period_end"]))
        if m["value"] is not None and m["unit"] in ("ratio", "percent"):
            d = Decimal(m["value"])
            c = ws.cell(row=i, column=3, value=float(d))
            c.number_format = "0.0%" if m["unit"] == "percent" else "0.00"
            c.fill = FILL["derived"]
        elif m["value"] is not None:
            ws.cell(row=i, column=3, value=_t(m["display_value"])).fill = FILL["derived"]
        else:
            ws.cell(row=i, column=3, value="n/a").fill = FILL["missing"]
        for j, k in enumerate(["unit", "status", "formula", "explanation"], start=4):
            ws.cell(row=i, column=j, value=_t(m[k]))
        ws.cell(row=i, column=8, value=_t("; ".join(m["limitations"])))
        ws.cell(row=i, column=9, value=_t(", ".join(m["inputs"])))
    _widths(ws, [30, 12, 12, 10, 22, 50, 60, 50, 40])
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:I{len(snap['metrics']) + 1}"

    ws = wb.create_sheet("Validation Results")
    cols = ["rule_id", "rule_version", "title", "statement_type", "period_end", "status", "severity", "expression", "expected",
            "observed", "difference", "tolerance", "tolerance_basis", "explanation"]
    _header(ws, 1, [c.replace("_", " ").title() for c in cols] + ["Input observation IDs"])
    for i, v in enumerate(snap["validations"], start=2):
        for j, k in enumerate(cols, start=1):
            if k in ("expected", "observed", "difference", "tolerance"):
                ws.cell(row=i, column=j, value=_t(v[k]) if v[k] is not None else "")  # exact base-unit decimals as text
            else:
                ws.cell(row=i, column=j, value=_t(v[k]))
        ws.cell(row=i, column=len(cols) + 1, value=_t(", ".join(v["inputs"])))
    _widths(ws, [8, 8, 44, 16, 12, 18, 10, 50, 20, 20, 20, 16, 60, 70, 40])
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols) + 1)}{len(snap['validations']) + 1}"

    ws = wb.create_sheet("Unresolved Exceptions")
    _header(ws, 1, ["Severity", "Category", "Title", "Detail", "Status", "Agent explanation", "Resolution note"])
    open_ex = [e for e in snap["exceptions"] if e["status"] in ("open", "explained")]
    for i, e in enumerate(open_ex, start=2):
        for j, k in enumerate(["severity", "category", "title", "detail", "status", "agent_explanation", "resolution_note"], start=1):
            ws.cell(row=i, column=j, value=_t(e[k]))
    _widths(ws, [10, 18, 50, 70, 12, 60, 40])
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:G{max(2, len(open_ex) + 1)}"

    ws = wb.create_sheet("Analyst Adjustments")
    _header(ws, 1, ["When", "User", "Action", "Item", "Before", "After", "Reason", "Version before", "Version after"])
    for i, a in enumerate(snap["adjustments"], start=2):
        vals = [a["at"][:19], a["user"], a["action"], a["label"] or a["field"], str(a["before"]), str(a["after"]), a["reason"],
                a["version_before"], a["version_after"]]
        for j, v in enumerate(vals, start=1):
            c = ws.cell(row=i, column=j, value=_t(v) if isinstance(v, str) else v)
            c.fill = FILL["adjusted"]
    _widths(ws, [20, 20, 18, 36, 30, 30, 50, 10, 10])
    ws.freeze_panes = "A2"

    ws = wb.create_sheet("Source References")
    _header(ws, 1, ["Observation ID", "Label (source)", "Code", "Period end", "Raw text", "State", "Exact value (base units)",
                    "Source scale", "Document", "Location", "Method", "Preferred", "Version kind"])
    for i, s in enumerate(snap["sources"], start=2):
        vals = [s["observation_id"], s["label"], s["code"] or "(unmapped)", s["period_end"], s["raw_text"], s["state"],
                s["value_units"] or "", s["scale"], s["document"], s["source"], s["method"], "yes" if s["preferred"] else "no", s["version_kind"]]
        for j, v in enumerate(vals, start=1):
            ws.cell(row=i, column=j, value=_t(v))
    _widths(ws, [34, 40, 30, 12, 16, 14, 26, 10, 36, 26, 12, 10, 12])
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:M{max(2, len(snap['sources']) + 1)}"

    ws = wb.create_sheet("Narrative")
    _header(ws, 1, ["Section", "Claim", "Evidence references"])
    r = 2
    for sec in pack.get("sections", []):
        for c in sec["claims"]:
            ws.cell(row=r, column=1, value=_t(sec["heading"]))
            ws.cell(row=r, column=2, value=_t(c["text"]))
            ws.cell(row=r, column=3, value=_t(", ".join(c["refs"])))
            r += 1
    _widths(ws, [26, 110, 50])

    for sheet in wb.worksheets:
        sheet.sheet_view.showGridLines = sheet.title != "Read Me"
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
