"""Nodes 1-7: ingest_change, diff_schema, classify_change, traverse_lineage, assess_asset, aggregate."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from langgraph.types import Send

from schemaguard.agent.assess import VERDICT_ORDER, assess_asset, worst
from schemaguard.agent.guardrails import new_cost_tracking, scan_schema_docs, wrap_untrusted
from schemaguard.agent.llm_calls import BudgetExceeded, call_llm, dumps, prompt
from schemaguard.agent.state import AgentState, AssessInput, Deps
from schemaguard.lineage.model import field_id
from schemaguard.llm.base import LLMError
from schemaguard.schemas.avro import parse_schema
from schemaguard.schemas.classify import classify
from schemaguard.schemas.diff import SchemaDiff, diff_schemas, rename_score

NO_DOWNSTREAM_KINDS = {"added", "doc_changed", "default_changed"}
ASSESSABLE = {"Column", "Visual", "DataTest"}


def make_ingest_change(deps: Deps):
    def ingest_change(state: AgentState) -> dict[str, Any]:
        ev = state["change_event"]
        old, new = ev["old_schema"], ev["new_schema"]
        parse_schema(old)  # raises on invalid Avro -> run marked failed with the error
        parse_schema(new)
        findings = scan_schema_docs(new, "new_schema")
        return {
            "status": "running",
            "old_schema": old,
            "new_schema": new,
            "injection_findings": findings,
            "lineage_version": deps.lineage_version,
            "cost_tracking": state.get("cost_tracking")
            or new_cost_tracking(deps.settings.run_budget_usd, deps.settings.run_budget_tokens),
            "retry_count": 0,
            "attempts": [],
            "approval_status": "not_requested",
        }

    return ingest_change


def make_diff_schema(deps: Deps):
    def diff_schema(state: AgentState) -> dict[str, Any]:
        topic = state["change_event"]["topic"]
        d = diff_schemas(parse_schema(state["old_schema"]), parse_schema(state["new_schema"]), topic)
        return {"schema_diff": d.to_dict()}

    return diff_schema


def make_classify_change(deps: Deps):
    def classify_change(state: AgentState) -> dict[str, Any]:
        d = SchemaDiff.from_dict(state["schema_diff"])
        result = classify(d)
        out: dict[str, Any] = {"change_class": result.to_dict()}
        # LLM: short explanation + optional rename suggestions, which must survive code-checked evidence.
        old, new = parse_schema(state["old_schema"]), parse_schema(state["new_schema"])
        ctx = {"topic": d.topic, "changes": [c.to_dict() for c in d.changes]}
        user = prompt(
            "explain_change",
            diff_json=dumps(ctx),
            schemas=wrap_untrusted(
                "avro-schemas", dumps({"old": state["old_schema"], "new": state["new_schema"]})
            ),
        )
        try:
            data, ct = call_llm(deps, state, "explain_change", user, ctx)
            out["cost_tracking"] = ct
            out["explanation"] = str(data.get("explanation", ""))[:2000]
            accepted = []
            removed = {c.field for c in d.changes if c.kind == "removed"}
            added = {c.field for c in d.changes if c.kind == "added"}
            for s in data.get("rename_suggestions", []) or []:
                src, dst = s.get("from"), s.get("to")
                of, nf = old.field(str(src)), new.field(str(dst))
                if src in removed and dst in added and of and nf:
                    score, ev = rename_score(of, nf)
                    if score >= 0.5:
                        accepted.append({"from": src, "to": dst, "score": score, "evidence": ev})
            if accepted:
                out["change_class"]["llm_rename_suggestions"] = accepted
        except BudgetExceeded as exc:
            out["route_reason"] = f"budget: {exc}"
            out["errors"] = [str(exc)]
        except LLMError as exc:
            out["explanation"] = "(LLM explanation unavailable)"
            out["errors"] = [f"classify_change: {exc}"]
        return out

    return classify_change


def make_traverse_lineage(deps: Deps):
    def traverse_lineage(state: AgentState) -> dict[str, Any]:
        d = state["schema_diff"]
        topic = d["topic"]
        lg = deps.lineage
        nodes: dict[str, dict[str, Any]] = {}
        notes: list[str] = []
        if not lg.has(f"topic:{topic}"):
            notes.append(f"topic {topic} is not in the lineage graph (no known consumers)")
        for idx, c in enumerate(d["changes"]):
            if c["kind"] in NO_DOWNSTREAM_KINDS:
                continue
            fid = field_id(topic, c["field"])
            if not lg.has(fid):
                continue
            for n in lg.downstream(fid):
                rec = nodes.setdefault(
                    n.id,
                    {
                        **n.to_dict(),
                        "label": lg.label(n.id)
                        if n.type not in ("Table", "Task", "Dag", "Owner")
                        else n.id.split(":", 1)[1],
                        "owner": lg.owner_of(n.id),
                        "changes": [],
                    },
                )
                if idx not in rec["changes"]:
                    rec["changes"].append(idx)
        out: dict[str, Any] = {
            "impacted_nodes": sorted(nodes.values(), key=lambda n: (n["context"], n["depth"], n["id"]))
        }
        if notes:
            out["errors"] = []  # informational, stored in route_reason
            out["route_reason"] = "; ".join(notes)
        return out

    return traverse_lineage


def make_fan_out(deps: Deps):
    def fan_out(state: AgentState) -> list[Send] | str:
        if state.get("route_reason", "").startswith("budget"):
            return "aggregate"
        d = state["schema_diff"]
        changes = d["changes"]
        sends = []
        for n in state.get("impacted_nodes", []):
            if n["context"] or n["type"] not in ASSESSABLE:
                continue
            attrs = deps.lineage.node(n["id"])
            if n["type"] == "Column" and attrs.get("layer") == "raw":
                continue
            paths = {
                str(idx): deps.lineage.paths_between(
                    field_id(d["topic"], changes[idx]["field"]), n["id"], dg=deps.flow
                )
                for idx in n["changes"]
            }
            asset = {"id": n["id"], "type": n["type"], "label": n["label"], "owner": n["owner"], **attrs}
            payload: AssessInput = {
                "run_id": state["run_id"],
                "asset": asset,
                "changes": changes,
                "paths_by_change": paths,
            }
            sends.append(Send("assess_asset", payload))
        return sends or "aggregate"

    return fan_out


def make_assess_asset(deps: Deps):
    def assess_asset_node(payload: AssessInput) -> dict[str, Any]:
        paths = {int(k): v for k, v in payload["paths_by_change"].items()}
        return {"assessments": [assess_asset(payload["asset"], payload["changes"], paths)]}

    return assess_asset_node


def make_aggregate(deps: Deps):
    def aggregate(state: AgentState) -> dict[str, Any]:
        lg = deps.lineage
        assessments = state.get("assessments", [])
        by_asset = {a["asset"]: a for a in assessments}
        dashboards: dict[str, str] = {}
        tables: dict[str, str] = {}
        for a in assessments:
            if a["type"] == "Visual":
                for dash, _ in lg.out(a["asset"], "PART_OF"):
                    dashboards[dash] = worst(dashboards.get(dash, "safe"), a["verdict"])
            if a["type"] == "Column":
                for table, _ in lg.inn(a["asset"], "HAS_COLUMN"):
                    tables[table] = worst(tables.get(table, "safe"), a["verdict"])
        counts = Counter(a["verdict"] for a in assessments)
        owners: dict[str, Counter[str]] = defaultdict(Counter)
        for a in assessments:
            owners[a.get("owner") or "unowned"][a["verdict"]] += 1
        d = state["schema_diff"]
        blast, paths = {}, {}
        for c in d["changes"]:
            fid = field_id(d["topic"], c["field"])
            if c["kind"] not in NO_DOWNSTREAM_KINDS and lg.has(fid):
                blast[c["field"]] = lg.blast_radius_summary(fid)
                paths[c["field"]] = lg.impact_paths(fid)
        has_impact = any(a["verdict"] != "safe" for a in assessments)
        build = build_impact(lg, {t for a in assessments for t in a.get("failing_tables", [])})
        agg = {
            "counts": {k: counts.get(k, 0) for k in ("breaking", "degraded", "safe")},
            "dashboards": {k.split(":", 1)[1]: v for k, v in sorted(dashboards.items())},
            "tables": {k.split(":", 1)[1]: v for k, v in sorted(tables.items())},
            "owners": {o: dict(c) for o, c in sorted(owners.items())},
            "blast_radius": blast,
            "impact_paths": paths,
            "has_impact": has_impact,
            "build_impact": build,
            "worst": max(
                (a["verdict"] for a in by_asset.values()), key=lambda v: VERDICT_ORDER[v], default="safe"
            ),
        }
        out: dict[str, Any] = {"aggregate": agg}
        if not has_impact:
            out["status"] = "no_impact"
        return out

    return aggregate


def build_impact(lg: Any, failing: set[str]) -> dict[str, Any]:
    """Tables whose build fails, downstream tables that will not refresh, and dashboards left stale."""
    deps: dict[str, set[str]] = defaultdict(set)  # table -> tables reading it
    for u, v, d in lg.edges():
        if d["type"] == "DERIVES_FROM" and u.startswith("column:") and v.startswith("column:"):
            child = lg.node(u).get("table")
            parent = lg.node(v).get("table")
            if child and parent and child != parent:
                deps[parent].add(child)
    stale: set[str] = set()
    frontier = list(failing)
    while frontier:
        t = frontier.pop()
        for c in deps.get(t, ()):
            if c not in stale and c not in failing:
                stale.add(c)
                frontier.append(c)
    hit = failing | stale
    dashboards = set()
    for vis in lg.nodes_of("Visual"):
        cols = [c for c, _ in lg.inn(vis, "USED_BY")]
        if any(lg.node(c).get("table") in hit for c in cols):
            for dash, _ in lg.out(vis, "PART_OF"):
                dashboards.add(dash.split(":", 1)[1])
    blocked = []
    for test in lg.nodes_of("DataTest"):
        tables = {lg.node(test).get("table")} | {
            lg.node(c).get("table") for c, _ in lg.inn(test, "TESTED_BY")
        }
        if tables & hit:
            blocked.append(test.split(":", 1)[1])
    return {
        "failing_tables": sorted(failing),
        "stale_tables": sorted(stale),
        "stale_dashboards": sorted(dashboards),
        "blocked_tests": sorted(blocked),
    }
