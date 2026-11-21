"""Streamlit UI. Talks to the API only.  `uv run schemaguard ui` (API must be running)."""

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any

import httpx
import streamlit as st

API = os.environ.get("SCHEMAGUARD_API_URL", "http://localhost:8000").rstrip("/")
HEADERS = {"X-API-Key": os.environ["SCHEMAGUARD_API_KEY"]} if os.environ.get("SCHEMAGUARD_API_KEY") else {}
ICON = {"breaking": "🔴", "degraded": "🟠", "safe": "🟢"}
STATUS_ICON = {
    "awaiting_approval": "⏸️",
    "completed": "✅",
    "no_impact": "🟢",
    "escalated": "⚠️",
    "rejected": "⛔",
    "failed": "❌",
    "running": "⏳",
}
PRESETS: dict[str, tuple[str, list[dict[str, Any]]]] = {
    "Rename orders.amount → total_amount": (
        "orders.v1",
        [{"op": "rename_field", "field": "amount", "to": "total_amount"}],
    ),
    "Drop orders.amount": ("orders.v1", [{"op": "drop_field", "field": "amount"}]),
    "Drop unused orders.coupon_code": ("orders.v1", [{"op": "drop_field", "field": "coupon_code"}]),
    "orders.quantity int → string": (
        "orders.v1",
        [{"op": "change_type", "field": "quantity", "type": "string"}],
    ),
    "New status value REFUNDED": (
        "orders.v1",
        [{"op": "add_enum_symbol", "field": "status", "symbol": "REFUNDED"}],
    ),
    "orders.customer_id becomes nullable": ("orders.v1", [{"op": "make_nullable", "field": "customer_id"}]),
    "Add nullable orders.channel": (
        "orders.v1",
        [{"op": "add_field", "field": "channel", "type": ["null", "string"], "default": None}],
    ),
}

st.set_page_config(page_title="SchemaGuard", page_icon="🛡️", layout="wide")


def api(method: str, path: str, **kw: Any) -> Any:
    r = httpx.request(method, f"{API}{path}", headers=HEADERS, timeout=30, **kw)
    if r.status_code >= 400:
        st.error(f"{method} {path} → {r.status_code}: {r.text[:300]}")
        return None
    return r.json() if "json" in r.headers.get("content-type", "") else r.text


with st.sidebar:
    st.title("🛡️ SchemaGuard")
    st.caption(f"API: {API} · all data is synthetic")
    health = api("GET", "/health")
    if health:
        st.caption(
            f"lineage v{health['lineage_version']} · llm={health['llm_provider']} · db={health['database']}"
        )
    st.subheader("Simulate a schema change")
    preset = st.selectbox("Scenario", list(PRESETS))
    if st.button("Submit change", type="primary"):
        topic, ops = PRESETS[preset]
        res = api("POST", "/changes", json={"topic": topic, "mutations": ops})
        if res:
            st.session_state["run_id"] = res["run_id"]
            st.success(("Started " if res["created"] else "Already processed: ") + res["run_id"][:8])
            time.sleep(1)

runs = api("GET", "/runs") or []
st.header("Runs")
if not runs:
    st.info("No runs yet. Submit a change from the sidebar.")
    st.stop()
st.dataframe(
    [
        {
            "run": r["run_id"][:8],
            "status": f"{STATUS_ICON.get(r['status'], '')} {r['status']}",
            "topic": r["topic"],
            "class": r["change_class"],
            "created": datetime.fromtimestamp(r["created_at"]).strftime("%H:%M:%S"),
        }
        for r in runs
    ],
    width="stretch",
    hide_index=True,
)
ids = [r["run_id"] for r in runs]
default = ids.index(st.session_state["run_id"]) if st.session_state.get("run_id") in ids else 0
run_id = st.selectbox(
    "Run detail",
    ids,
    index=default,
    format_func=lambda i: f"{i[:8]} · {next(r['status'] for r in runs if r['run_id'] == i)}",
)
run = api("GET", f"/runs/{run_id}")
if not run:
    st.stop()
s = run["state"]
st.subheader(f"{STATUS_ICON.get(run['status'], '')} {run['status']} — {run['topic']}")
if run.get("error"):
    st.error(run["error"])
if run["status"] == "running":
    st.info("Running… refresh in a few seconds.")
    if st.button("Refresh"):
        st.rerun()
agg = s.get("aggregate") or {}
c = agg.get("counts", {})
m1, m2, m3, m4 = st.columns(4)
m1.metric("Breaking", c.get("breaking", 0))
m2.metric("Degraded", c.get("degraded", 0))
m3.metric("Safe", c.get("safe", 0))
m4.metric("Est. LLM cost", f"${(s.get('cost_tracking') or {}).get('usd', 0):.4f}")
if s.get("explanation"):
    st.caption(s["explanation"])

tab_graph, tab_verdicts, tab_patch, tab_tests, tab_report = st.tabs(
    ["Impact graph", "Verdicts", "Patch", "Tests", "Report"]
)
with tab_graph:
    dot = api("GET", f"/runs/{run_id}/graph.dot")
    if dot and "->" in dot:
        st.graphviz_chart(dot, width="stretch")
    else:
        st.write("Nothing downstream.")
    for field, paths in (agg.get("impact_paths") or {}).items():
        st.markdown(f"**{field}**")
        for p in paths:
            st.markdown(f"- {p}")
with tab_verdicts:
    if agg.get("dashboards"):
        st.markdown(" · ".join(f"{ICON[v]} **{k}**" for k, v in agg["dashboards"].items()))
    rows = sorted(
        s.get("assessments") or [],
        key=lambda a: ({"breaking": 0, "degraded": 1, "safe": 2}[a["verdict"]], a["asset"]),
    )
    st.dataframe(
        [
            {
                "verdict": f"{ICON[a['verdict']]} {a['verdict']}",
                "asset": a.get("label") or a["asset"],
                "type": a["type"],
                "owner": a.get("owner"),
                "reason": a["reason"],
                "evidence": " | ".join(a["evidence"]),
            }
            for a in rows
        ],
        width="stretch",
        hide_index=True,
    )
with tab_patch:
    plan = s.get("fix_plan") or {}
    if plan:
        st.markdown(f"**Strategy:** `{plan.get('strategy')}`  \n{plan.get('rationale')}")
    if (s.get("patch") or {}).get("diff"):
        st.code(s["patch"]["diff"], language="diff")
        if not s["patch"]["check"]["ok"]:
            st.warning("Guardrail violations: " + "; ".join(s["patch"]["check"]["violations"]))
    else:
        st.write("No patch.")
with tab_tests:
    base = s.get("baseline_results")
    if base:
        st.markdown(
            f"**Without fix:** {'passes' if base['ok'] else 'fails'} ({base['tests_passed']}/{base['tests_total']} tests)"
        )
        for f in base["failures"][:8]:
            st.text(f)
    for a in s.get("attempts") or []:
        st.markdown(f"**Attempt {a['attempt']} – {a['strategy']}:** {'✅ pass' if a['ok'] else '❌ fail'}")
        for f in a["failures"]:
            st.text(f)
    if s.get("test_results", {}).get("tests"):
        st.dataframe(s["test_results"]["tests"], width="stretch", hide_index=True)
with tab_report:
    if s.get("report"):
        st.markdown(s["report"])
    else:
        st.write("The report is written when the run finishes.")

if run["status"] == "awaiting_approval":
    st.divider()
    st.subheader("Human approval")
    st.write(
        "The patch passed all data tests in the sandbox. Approving creates a local branch (and a draft PR only if GITHUB_TOKEN is configured)."
    )
    reviewer = st.text_input("Reviewer", value=os.environ.get("USERNAME", "reviewer"))
    comment = st.text_area("Comment", "")
    a, b = st.columns(2)
    if a.button("✅ Approve", type="primary"):
        if api("POST", f"/runs/{run_id}/approve", json={"reviewer": reviewer, "comment": comment}):
            time.sleep(1.5)
            st.rerun()
    if b.button("⛔ Reject"):
        if api("POST", f"/runs/{run_id}/reject", json={"reviewer": reviewer, "comment": comment}):
            time.sleep(1.5)
            st.rerun()
