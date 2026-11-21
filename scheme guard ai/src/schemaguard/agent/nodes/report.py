"""Node 14: write_report. Deterministic sections + an LLM-written business summary."""

from __future__ import annotations

from typing import Any

from schemaguard.agent.llm_calls import BudgetExceeded, call_llm, dumps, prompt
from schemaguard.agent.nodes.fix import artifacts_dir
from schemaguard.agent.state import AgentState, Deps
from schemaguard.llm.base import LLMError

ICON = {"breaking": "🔴 breaking", "degraded": "🟠 degraded", "safe": "🟢 safe"}


def _outcome(state: AgentState) -> str:
    st = state.get("status")
    if st == "no_impact":
        return "No downstream asset is affected; no action is needed."
    if st == "completed":
        return f"A fix passed all data tests, was approved by {state['approval']['reviewer']}, and is ready: {state.get('pr_url_or_patch_path')}."
    if st == "rejected":
        return f"A tested fix was proposed but rejected by {state['approval']['reviewer']}: {state['approval'].get('comment') or 'no comment'}."
    if st == "escalated":
        return f"No automatic fix was applied ({state.get('escalation_reason')}). The owning teams must decide; see recommendations."
    return f"Run status: {st}."


def make_write_report(deps: Deps):
    def write_report(state: AgentState) -> dict[str, Any]:
        d = state["schema_diff"]
        agg = state.get("aggregate", {})
        cc = state.get("change_class", {})
        facts = {
            "topic": d["topic"],
            "change_class": cc.get("change_class"),
            "changes": [
                f"{c['kind']} {c['field']}" + (f" -> {c['new_field']}" if c.get("new_field") else "")
                for c in d["changes"]
            ],
            "counts": agg.get("counts", {}),
            "dashboards": [k for k, v in agg.get("dashboards", {}).items() if v != "safe"],
            "owners": [o for o, c in agg.get("owners", {}).items() if c.get("breaking") or c.get("degraded")],
            "outcome": _outcome(state),
        }
        out: dict[str, Any] = {}
        summary = None
        try:
            data, ct = call_llm(
                deps, state, "write_summary", prompt("write_summary", facts_json=dumps(facts)), facts
            )
            summary, out["cost_tracking"] = str(data.get("summary", "")), ct
        except (BudgetExceeded, LLMError) as exc:
            out["errors"] = [f"write_report summary: {exc}"]
        ct = out.get("cost_tracking") or state.get("cost_tracking", {})
        md = render_report(state, summary or facts["outcome"], facts, ct)
        (artifacts_dir(deps, state["run_id"]) / "report.md").write_text(md, encoding="utf-8")
        out["report"] = md
        if state.get("status") in (None, "running"):
            out["status"] = "completed"
        return out

    return write_report


def render_report(state: AgentState, summary: str, facts: dict[str, Any], ct: dict[str, Any]) -> str:
    d = state["schema_diff"]
    agg = state.get("aggregate", {})
    cc = state.get("change_class", {})
    ev = state.get("change_event", {})
    L: list[str] = []
    L.append(f"# SchemaGuard impact report: `{d['topic']}`")
    L.append("")
    L.append(
        f"- **Run:** `{state['run_id']}` · **Status:** `{state.get('status')}` · **Change class:** `{cc.get('change_class')}`"
    )
    L.append(
        f"- **Source:** {ev.get('source', 'api')} · subject `{ev.get('subject', '')}` v{ev.get('old_version', '?')} → v{ev.get('new_version', '?')}"
    )
    L.append(f"- **Lineage graph version:** {state.get('lineage_version')}")
    L.append("")
    L.append("## Summary")
    L.append(summary)
    L.append("")
    L.append("## What changed")
    L.append("| Change | Field | Detail | Severity | Registry compat (back/fwd) |")
    L.append("|---|---|---|---|---|")
    for pc in cc.get("per_change", []):
        c = pc["change"]
        detail = c.get("new_field") or c.get("new_type") or c.get("details", {}).get("symbols") or ""
        L.append(
            f"| {c['kind']} | `{c['field']}` | {detail} | {pc['severity']} | {pc['backward']}/{pc['forward']} |"
        )
    if state.get("explanation"):
        L.append("")
        L.append(f"> {state['explanation']}")
    if state.get("injection_findings"):
        L.append("")
        L.append("**⚠ Instruction-like text found in schema docs (treated as data, not followed):**")
        for f in state["injection_findings"]:
            L.append(f"- `{f['location']}`: “{f['excerpt']}”")
    L.append("")
    L.append("## What breaks")
    c = agg.get("counts", {})
    L.append(
        f"**{c.get('breaking', 0)} breaking · {c.get('degraded', 0)} degraded · {c.get('safe', 0)} safe** assets assessed."
    )
    if agg.get("dashboards"):
        L.append("")
        L.append("| Dashboard | Verdict |")
        L.append("|---|---|")
        for k, v in agg["dashboards"].items():
            L.append(f"| {k} | {ICON[v]} |")
    rows = sorted(
        state.get("assessments", []),
        key=lambda a: (-{"breaking": 2, "degraded": 1, "safe": 0}[a["verdict"]], a["type"], a["asset"]),
    )
    if rows:
        L.append("")
        L.append("| Asset | Type | Verdict | Owner | Why |")
        L.append("|---|---|---|---|---|")
        for a in rows:
            L.append(
                f"| `{a.get('label') or a['asset']}` | {a['type']} | {ICON[a['verdict']]} | {a.get('owner') or '-'} | {a['reason'].replace('|', '/')} |"
            )
    bi = agg.get("build_impact") or {}
    if bi.get("failing_tables"):
        L.append("")
        L.append("### Build impact")
        L.append(f"- **Builds that will fail:** {', '.join(f'`{t}`' for t in bi['failing_tables'])}")
        if bi.get("stale_tables"):
            L.append(
                f"- **Downstream tables that will not refresh (stale):** {', '.join(f'`{t}`' for t in bi['stale_tables'])}"
            )
        if bi.get("stale_dashboards"):
            L.append(
                f"- **Dashboards showing failed or stale data until fixed:** {', '.join(bi['stale_dashboards'])}"
            )
        if bi.get("blocked_tests"):
            L.append(
                f"- **Data tests that cannot pass until fixed (table fails or is not rebuilt):** {', '.join(f'`{t}`' for t in bi['blocked_tests'])}"
            )
    paths = agg.get("impact_paths", {})
    if any(paths.values()):
        L.append("")
        L.append("### Impact paths")
        for _field, ps in paths.items():
            for p in ps:
                L.append(f"- {p}")
    L.append("")
    L.append("## Who owns it")
    owners = agg.get("owners", {})
    if owners:
        for o, cnt in owners.items():
            if cnt.get("breaking") or cnt.get("degraded"):
                L.append(f"- **{o}**: {cnt.get('breaking', 0)} breaking, {cnt.get('degraded', 0)} degraded")
    else:
        L.append("- nobody downstream is affected")
    L.append("")
    L.append("## The fix")
    plan = state.get("fix_plan")
    if plan:
        L.append(f"**Strategy:** `{plan.get('strategy')}`")
        L.append("")
        L.append(plan.get("rationale", ""))
        if state.get("patch", {}).get("diff") and state.get("status") != "escalated":
            L.append("")
            L.append("```diff")
            L.append(state["patch"]["diff"].rstrip())
            L.append("```")
    else:
        L.append("No fix needed." if state.get("status") == "no_impact" else "No fix planned.")
    if state.get("status") == "escalated":
        L.append("")
        L.append(f"**Escalated:** {state.get('escalation_reason')}")
        L.append(
            "Recommendation: pin consumers to the previous schema version and ask the producer team to restore or alias the field."
        )
    L.append("")
    L.append("## Test evidence")
    base = state.get("baseline_results")
    if base:
        L.append(
            f"- **Without fix (new schema, current code):** {'passes' if base['ok'] else 'fails'} — {base['tests_passed']}/{base['tests_total']} tests passed"
        )
        for f in base["failures"][:5]:
            L.append(f"  - {f}")
    for a in state.get("attempts", []):
        L.append(
            f"- **Attempt {a['attempt']} ({a['strategy']}):** {'✅ all tests pass' if a['ok'] else '❌ failed'}"
        )
        for f in a["failures"][:5]:
            L.append(f"  - {f}")
    if not base and not state.get("attempts"):
        L.append("- No sandbox run was needed.")
    L.append("")
    L.append("## Approval record")
    ap = state.get("approval")
    if ap:
        L.append(
            f"- **{ap['decision']}** by `{ap['reviewer']}` at {ap['at']}"
            + (f": {ap['comment']}" if ap.get("comment") else "")
        )
        if state.get("pr_url_or_patch_path"):
            L.append(f"- Output: {state['pr_url_or_patch_path']}")
    else:
        L.append(f"- Approval status: `{state.get('approval_status', 'not_requested')}`")
    L.append("")
    L.append("## Run cost")
    L.append(
        f"- LLM calls: {ct.get('calls', 0)} · tokens in/out: {ct.get('tokens_in', 0)}/{ct.get('tokens_out', 0)} · estimated cost: ${ct.get('usd', 0):.4f} (budget ${ct.get('budget_usd', 0):.2f})"
    )
    if state.get("errors"):
        L.append("")
        L.append("## Errors and warnings")
        for e in state["errors"]:
            L.append(f"- {e}")
    L.append("")
    L.append("_All data in this report is synthetic. Generated by SchemaGuard._")
    return "\n".join(L) + "\n"
