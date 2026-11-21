"""E. Analyst Pack Agent.

Why it exists: reviewers need a short, evidence-linked narrative of what the numbers show and
what is still uncertain — not a story. Every numerical claim references stored observations or
calculation records, and a verifier rejects any claim whose numbers are not found in its refs.

AI vs code: the demo adapter writes template sentences from the snapshot. In live mode an eve agent
drafts claims; the same verifier checks them, and rejected claims are listed, not published.
It never infers fraud, business causes or accounting compliance from numerical anomalies.
"""

from __future__ import annotations

import json
import re
from decimal import Decimal

from spreadlens.agents.contracts import AnalystPack, PackClaim, PackSection
from spreadlens.agents.runtime import AgentContext, ExecutionRecorder
from spreadlens.services.artifacts import save_artifact

NAME = "analyst_pack"
NUM = re.compile(r"(?<![\w.])\(?-?\d[\d,]*\.\d+\)?%?|(?<![\w.])\d[\d,]*%")
FORBIDDEN = re.compile(r"\b(fraud|manipulat|misstat\w*\s+intentional|compliant|complies|in\s+compliance|creditworth|approve\s+the\s+loan|recommend\s+lending)", re.I)


def _ref_values(snap: dict, ref: str) -> set[str]:
    vals: set[str] = set()

    def add(v: str | None) -> None:
        if v is None:
            return
        try:
            d = Decimal(v.replace("%", "").replace(",", ""))
        except Exception:  # noqa: BLE001
            return
        for q in (d, abs(d)):
            vals.add(format(q.quantize(Decimal("0.01")), "f"))
            vals.add(format(q.quantize(Decimal("0.1")), "f"))
    for m in snap.get("metrics", []):
        if m["id"] == ref:
            add(m.get("display_value"))
    for st in snap.get("statements", {}).values():
        for line in st["lines"]:
            for c in line["cells"].values():
                if c.get("observation_id") == ref:
                    add(c.get("value"))
    for v in snap.get("validations", []):
        if v["id"] == ref:
            add(v.get("difference"))
    return vals


def verify_claim(claim: PackClaim, snap: dict, derived: dict[str, set[str]] | None = None) -> str | None:
    if FORBIDDEN.search(claim.text):
        return "claim makes a judgement the pack must not make (fraud/compliance/lending)"
    allowed: set[str] = set()
    for r in claim.refs:
        allowed |= _ref_values(snap, r)
        allowed |= (derived or {}).get(r, set())
    for m in NUM.finditer(claim.text):
        tok = m.group(0).strip("()").replace(",", "").replace("%", "")
        try:
            d = Decimal(tok)
        except Exception:  # noqa: BLE001
            continue
        cands = {format(d.quantize(Decimal("0.01")), "f"), format(d.quantize(Decimal("0.1")), "f"),
                 format(abs(d).quantize(Decimal("0.01")), "f"), format(abs(d).quantize(Decimal("0.1")), "f")}
        if not cands & allowed:
            return f"number {m.group(0)} is not supported by the referenced records"
    return None


def _metric(snap: dict, mid: str, period: str) -> dict | None:
    return next((m for m in snap["metrics"] if m["metric_id"] == mid and m["period_end"] == period), None)


def draft(snap: dict) -> tuple[list[PackSection], dict[str, set[str]]]:
    """Deterministic narrative (demo adapter). Percentage-point changes are derived and registered."""
    derived: dict[str, set[str]] = {}
    per = snap["periods"]
    scale = snap["display_scale"]
    trends: list[PackClaim] = []
    if per:
        cur = per[0]
        g = _metric(snap, "revenue_growth", cur)
        if g and g["status"] == "computed":
            trends.append(PackClaim(text=f"Revenue changed by {g['display_value']} in the year ended {cur} compared with the prior year.", refs=[g["id"]]))
        elif g:
            trends.append(PackClaim(text=f"Revenue growth for {cur} is not presented as a percentage: {g['explanation']}", refs=[g["id"]]))
        if len(per) > 1:
            m1, m0 = _metric(snap, "net_profit_margin", cur), _metric(snap, "net_profit_margin", per[1])
            if m1 and m0 and m1["status"] == m0["status"] == "computed":
                pp = (Decimal(m1["value"]) - Decimal(m0["value"])) * 100
                key = f"pp:{m1['id']}:{m0['id']}"
                derived[key] = {format(abs(pp).quantize(Decimal("0.1")), "f"), format(abs(pp).quantize(Decimal("0.01")), "f")}
                direction = "increased" if pp > 0 else "decreased" if pp < 0 else "was unchanged"
                pm1, pm0 = Decimal(m1["value"]) * 100, Decimal(m0["value"]) * 100
                derived[m1["id"]] = {format(pm1.quantize(Decimal("0.1")), "f")}
                derived[m0["id"]] = {format(pm0.quantize(Decimal("0.1")), "f")}
                trends.append(PackClaim(text=(f"Net profit margin {direction} from {pm0.quantize(Decimal('0.1'))}% to {pm1.quantize(Decimal('0.1'))}%, "
                                              f"a change of {abs(pp).quantize(Decimal('0.1'))} percentage points (not a percentage change)."),
                                        refs=[m1["id"], m0["id"], key]))
        for mid, label in (("current_ratio", "Current ratio"), ("debt_to_equity", "Debt to equity"), ("ocf_to_net_profit", "Operating cash flow to net profit")):
            m = _metric(snap, mid, cur)
            if m and m["status"] == "computed":
                trends.append(PackClaim(text=f"{label} for {cur} is {m['display_value']}x ({m['formula']}).", refs=[m["id"]]))
            elif m:
                trends.append(PackClaim(text=f"{label} for {cur}: {m['status'].replace('_', ' ')} — {m['explanation']}", refs=[m["id"]]))
        fcf = _metric(snap, "free_cash_flow", cur)
        if fcf and fcf["status"] == "computed":
            trends.append(PackClaim(text=f"Free cash flow for {cur} is {fcf['display_value']} ({snap['currency']} {scale}), defined as {fcf['formula']}.", refs=[fcf["id"]]))
    comp: list[PackClaim] = []
    for st, d in snap["statements"].items():
        name = st.replace("_", " ")
        if not d["available"]:
            comp.append(PackClaim(text=f"No {name} was provided.", refs=[]))
        else:
            comp.append(PackClaim(text=f"The {name} has {len(d['lines'])} standardised lines and {len(d['unmapped_rows'])} unmapped source figures kept visible.", refs=[]))
    unread = [e for e in snap["exceptions"] if e["category"] in ("unreadable_cell", "dash_ambiguous") and e["status"] == "open"]
    if unread:
        comp.append(PackClaim(text=f"{len(unread)} source figures remain unresolved (unreadable or ambiguous) and are not used in checks.", refs=[]))
    val: list[PackClaim] = []
    fails = [v for v in snap["validations"] if v["status"] == "fail"]
    review = [v for v in snap["validations"] if v["status"] == "requires_review"]
    insuff = [v for v in snap["validations"] if v["status"] == "insufficient_data"]
    passed = [v for v in snap["validations"] if v["status"] == "pass"]
    val.append(PackClaim(text=f"{len(passed)} checks passed, {len(fails)} failed, {len(review)} require review and {len(insuff)} could not run for lack of data. "
                              "Passing arithmetic checks does not prove the figures are correct.", refs=[]))
    for v in fails[:6]:
        val.append(PackClaim(text=f"{v['rule_id']} {v['title']} ({v['period_end']}) failed with an exact residual recorded in the validation sheet.", refs=[v["id"]]))
    adj = [PackClaim(text=f"{a['action'].replace('_', ' ').capitalize()} on '{a['label'] or a['field']}' by {a['user']}: {a['reason']}", refs=[]) for a in snap["adjustments"][:10]]
    if not adj:
        adj = [PackClaim(text="No analyst adjustments were made.", refs=[])]
    limits = [PackClaim(text=t, refs=[]) for t in snap["comparability"]]
    questions = [PackClaim(text=f"{e['title']}", refs=[]) for e in snap["exceptions"] if e["status"] == "open" and e["severity"] in ("critical", "warning")][:12]
    if not questions:
        questions = [PackClaim(text="No open critical or warning exceptions.", refs=[])]
    return [PackSection(heading="Financial trends", claims=trends), PackSection(heading="Data completeness", claims=comp),
            PackSection(heading="Validation exceptions", claims=val), PackSection(heading="Analyst adjustments", claims=adj),
            PackSection(heading="Comparability limitations", claims=limits), PackSection(heading="Questions requiring review", claims=questions)], derived


def run(ctx: AgentContext, snap: dict) -> AnalystPack:
    rec = ExecutionRecorder(ctx, NAME)
    try:
        sections, derived = rec.tool("draft_from_snapshot", draft, snap)
        if ctx.mode == "live":
            compact = {k: snap[k] for k in ("company", "entity", "periods", "currency", "display_scale", "metrics", "comparability")}
            compact["validations"] = [v for v in snap["validations"] if v["status"] != "pass"]
            msg = ("Write concise analyst-pack claims for the six sections. Every number must come from a referenced record "
                   "(metric/observation/validation id). Distinguish percentage changes from percentage-point changes. "
                   "Do not infer fraud, business causes, compliance or lending decisions. Do not describe unresolved figures as verified.\n"
                   + json.dumps(compact, default=str)[:30000])
            live = rec.live(msg, AnalystPack, {"spread_version": snap["spread_version"]})
            sections = live.sections
        rejected = []
        clean = []
        for s in sections:
            ok = []
            for c in s.claims:
                why = verify_claim(c, snap, derived)
                if why:
                    rejected.append(f"{s.heading}: '{c.text[:120]}' — {why}")
                else:
                    ok.append(c)
            clean.append(PackSection(heading=s.heading, claims=ok))
        pack = AnalystPack(sections=clean, rejected_claims=rejected)
        art = save_artifact(ctx.db, ctx.workspace_id, ctx.run_id, pack, NAME)
        rec.finish("succeeded", art.id)
        return pack
    except Exception as exc:
        rec.finish("failed", error=f"{type(exc).__name__}: {exc}"[:500])
        raise
