from __future__ import annotations

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.constants import DISCLAIMER, NO_EXECUTION_STATEMENT, PLAN_ARTIFACT_NAME, PRODUCT_NAME
from app.models.plan import FinalPlan

NAVY = colors.HexColor("#16324F")
PAPER = colors.HexColor("#F4F0E6")
INK = colors.HexColor("#121A24")
BRASS = colors.HexColor("#9A7348")
RULE = colors.HexColor("#D6CDB8")


def _styles():
    base = getSampleStyleSheet()
    base.add(
        ParagraphStyle(
            name="CoverTitle",
            fontName="Times-Bold",
            fontSize=22,
            textColor=NAVY,
            leading=26,
            spaceAfter=8,
        )
    )
    base.add(ParagraphStyle(name="H", fontName="Times-Bold", fontSize=13, textColor=NAVY, spaceBefore=10, spaceAfter=4))
    base.add(ParagraphStyle(name="Body", fontName="Times-Roman", fontSize=9.5, textColor=INK, leading=13, spaceAfter=4))
    base.add(ParagraphStyle(name="Fine", fontName="Times-Italic", fontSize=8, textColor=INK, leading=11, spaceAfter=6))
    base.add(ParagraphStyle(name="Warn", fontName="Times-Bold", fontSize=9, textColor=colors.HexColor("#8B3A3A"), leading=12))
    return base


def render_plan_pdf(plan: FinalPlan, dest: Path | None = None) -> bytes:
    styles = _styles()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"{PLAN_ARTIFACT_NAME} {plan.plan_id}",
        author=PRODUCT_NAME,
    )
    story = []

    def p(text: str, style="Body"):
        story.append(Paragraph(text.replace("\n", "<br/>"), styles[style]))

    def h(text: str):
        story.append(Paragraph(text, styles["H"]))

    selected = next((s for s in plan.scenarios if s.name == plan.selected), plan.scenarios[0] if plan.scenarios else None)

    p(PRODUCT_NAME, "Fine")
    p(PLAN_ARTIFACT_NAME, "CoverTitle")
    p(
        f"plan_id {plan.plan_id} · version {plan.version} · {plan.generated_at_ist}<br/>"
        f"snapshot_id {plan.snapshot_id} · rules_version {plan.rules_version}",
        "Fine",
    )
    p(DISCLAIMER, "Fine")
    p(NO_EXECUTION_STATEMENT, "Warn")

    h("2. Disclaimer")
    p(DISCLAIMER)
    p("This document is a financial-planning simulation. It is not suitability certification or fiduciary advice.")

    h("3. Plan version and timestamp")
    p(f"Version {plan.version}. Generated {plan.generated_at_ist}. Data mode {plan.data_mode}. Degraded={plan.degraded}.")

    h("4. Household mandate")
    hh = plan.household
    p(
        f"{hh.first_name}, age {hh.age}, {hh.city} {hh.state}. "
        f"{hh.earners} earner(s), {hh.dependents} dependent(s). Tax regime: {hh.tax_regime}."
    )

    h("5. IPS summary")
    ips = plan.ips
    p(
        f"Risk score {ips.risk_score} ({ips.risk_band}). Capacity for loss: {ips.capacity_for_loss}. "
        f"Equity ceiling {ips.equity_ceiling_pct}%. Debt floor {ips.required_debt_floor_pct}%. "
        f"Liquid reserve target {ips.minimum_liquid_reserve_months} months."
    )
    for n in ips.notes:
        p(f"• {n}")

    h("6. Current financial position")
    p(
        f"Monthly take-home ₹{hh.monthly_take_home_inr:,.0f}. Essential ₹{hh.essential_expenses_monthly_inr:,.0f}. "
        f"Liabilities: {len(hh.liabilities)}. Holdings: {len(plan.holdings)}."
    )
    if plan.current_allocation:
        p("Current mix (from holdings): " + ", ".join(f"{k} {v}%" for k, v in plan.current_allocation.items() if v))

    h("7. Emergency-reserve analysis")
    er = plan.emergency_reserve
    p(
        f"Liquid ₹{er.get('liquid_inr', 0):,.0f} versus target ₹{er.get('target_inr', 0):,.0f} "
        f"(gap ₹{er.get('gap_inr', 0):,.0f})."
    )

    h("8. Current vs target allocation")
    if selected:
        p(
            f"Selected simulation {selected.label}: cash {selected.cash_pct}%, debt {selected.fixed_income_pct}%, "
            f"equity {selected.equity_pct}%, gold {selected.gold_pct}%, international {selected.international_pct}%, "
            f"alternatives {selected.alternatives_pct}%."
        )

    h("9. Protect / Balance / Grow comparison")
    rows = [["Scenario", "Equity", "Debt", "Cash", "Gold", "Alt", "Vol", "Coverage"]]
    for s in plan.scenarios:
        rows.append(
            [
                s.label,
                f"{s.equity_pct}%",
                f"{s.fixed_income_pct}%",
                f"{s.cash_pct}%",
                f"{s.gold_pct}%",
                f"{s.alternatives_pct}%",
                s.estimated_volatility_class,
                f"{s.source_coverage_pct}%",
            ]
        )
    table = Table(rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.3, RULE),
                ("BACKGROUND", (0, 1), (-1, -1), PAPER),
                ("TEXTCOLOR", (0, 1), (-1, -1), INK),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 6))

    h("10. Selected simulation and rationale")
    if selected:
        p(f"{selected.label}: {selected.rationale}")
        p(selected.argument_for)

    h("11. Why the other simulations differ")
    for s in plan.scenarios:
        if selected and s.name == selected.name:
            continue
        p(f"<b>{s.label}</b> — {s.rationale} Against: {s.argument_against}")

    h("12. Allocation table")
    if selected:
        for w in selected.weights:
            p(f"{w.sleeve}: {w.weight_pct}% (₹{w.inr_amount:,.0f}) — {w.role}")

    h("13. Monthly contribution plan")
    if selected:
        p(f"Planning surplus directed in this simulation: ₹{selected.monthly_contribution_inr:,.0f}/month. Not an order.")

    h("14. Five actions for this month")
    for i, a in enumerate(plan.actions, 1):
        amt = f" (₹{a.amount_inr:,.0f})" if a.amount_inr is not None else ""
        p(f"{i}. {a.title}{amt} — {a.detail}")

    h("15. Do-not-do list")
    if selected:
        for item in selected.do_not_do:
            p(f"• {item}")

    h("16. Stress tests")
    for st in plan.stress:
        p(f"<b>{st.name}</b> (hypothetical): {st.description} {st.impact_summary}")

    h("17. Tax considerations")
    for t in plan.tax_notes:
        p(f"• {t}")

    h("18. Protection gaps")
    for t in plan.protection_notes:
        p(f"• {t}")

    h("19. Goal progress")
    for g in hh.goals:
        p(f"• {g.name}: ₹{g.target_amount_inr:,.0f} by {g.target_year} ({g.priority})")

    h("20. Home-loan analysis")
    if plan.home_loan_analysis:
        p(str(plan.home_loan_analysis.get("note", "")))
        p(
            f"Guaranteed interest saving (if prepaid): ₹{plan.home_loan_analysis.get('guaranteed_interest_saving', 0):,.0f}. "
            "Investment legs are hypothetical."
        )
    else:
        p("No home loan on the household profile.")

    h("21. 90-day review checklist")
    p("• Re-check emergency reserve months versus policy.")
    p("• Re-fetch the regulatory snapshot before any tax-sensitive decision.")
    p("• Confirm constraints still hold.")
    p("• Do not place orders through this application — it cannot execute them.")

    h("22. Source register")
    for src in plan.sources:
        p(
            f"• {src.title} ({src.authority}) tier {src.tier} — {src.url} — as_of {src.as_of} — "
            f"fetched {src.fetched_at} — {src.verification}"
        )

    h("23. Data-quality warnings")
    for w in plan.data_quality_warnings:
        p(f"• {w}", "Warn")

    h("24. Assumptions")
    if selected:
        for a in selected.assumptions:
            p(f"• {a}")

    h("25. Failure modes")
    if selected:
        for a in selected.failure_modes:
            p(f"• {a}")

    h("26. Full disclaimer")
    p(DISCLAIMER, "Fine")

    h("27. Execution statement")
    p(NO_EXECUTION_STATEMENT, "Warn")
    p(f"Risk Officer status: {plan.risk_status}. Model: {plan.model_name}.")

    def _footer(canvas, _doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, A4[1] - 8 * mm, A4[0], 8 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Times-Roman", 8)
        canvas.drawString(18 * mm, A4[1] - 5.5 * mm, f"{PRODUCT_NAME} · educational simulation")
        canvas.setFillColor(INK)
        canvas.setFont("Times-Roman", 8)
        canvas.drawString(18 * mm, 10 * mm, f"{plan.plan_id} · {plan.generated_at_ist}")
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, DISCLAIMER[:90] + "…")
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    data = buf.getvalue()
    if dest:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    return data
