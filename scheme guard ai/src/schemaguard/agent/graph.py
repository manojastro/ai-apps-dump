"""The LangGraph StateGraph wiring all nodes together."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from schemaguard.agent.nodes.analysis import (
    make_aggregate,
    make_assess_asset,
    make_classify_change,
    make_diff_schema,
    make_fan_out,
    make_ingest_change,
    make_traverse_lineage,
)
from schemaguard.agent.nodes.approval import make_human_approval, make_open_pr, route_after_approval
from schemaguard.agent.nodes.fix import (
    make_check_tests,
    make_escalate,
    make_generate_patch,
    make_plan_fix,
    make_run_tests,
    route_after_check,
    route_after_plan,
)
from schemaguard.agent.nodes.report import make_write_report
from schemaguard.agent.state import AgentState, Deps
from schemaguard.observability import instrument_node


def route_after_aggregate(state: AgentState) -> str:
    if state.get("route_reason", "").startswith("budget"):
        return "escalate"
    return "plan_fix" if state["aggregate"]["has_impact"] else "write_report"


def route_after_patch(state: AgentState) -> str:
    return "escalate" if state.get("route_reason", "").startswith("budget") else "run_tests"


def build_graph(deps: Deps) -> StateGraph:
    g: StateGraph = StateGraph(AgentState)

    def add(name: str, fn: Any) -> None:
        g.add_node(name, instrument_node(name, fn))  # type: ignore[call-overload]

    add("ingest_change", make_ingest_change(deps))
    add("diff_schema", make_diff_schema(deps))
    add("classify_change", make_classify_change(deps))
    add("traverse_lineage", make_traverse_lineage(deps))
    add("assess_asset", make_assess_asset(deps))
    add("aggregate", make_aggregate(deps))
    add("plan_fix", make_plan_fix(deps))
    add("generate_patch", make_generate_patch(deps))
    add("run_tests", make_run_tests(deps))
    add("check_tests", make_check_tests(deps))
    add("human_approval", make_human_approval(deps))
    add("open_pr", make_open_pr(deps))
    add("escalate", make_escalate(deps))
    add("write_report", make_write_report(deps))

    g.add_edge(START, "ingest_change")
    g.add_edge("ingest_change", "diff_schema")
    g.add_edge("diff_schema", "classify_change")
    g.add_edge("classify_change", "traverse_lineage")
    g.add_conditional_edges("traverse_lineage", make_fan_out(deps), ["assess_asset", "aggregate"])
    g.add_edge("assess_asset", "aggregate")
    g.add_conditional_edges("aggregate", route_after_aggregate, ["plan_fix", "write_report", "escalate"])
    g.add_conditional_edges("plan_fix", route_after_plan, ["generate_patch", "escalate"])
    g.add_conditional_edges("generate_patch", route_after_patch, ["run_tests", "escalate"])
    g.add_edge("run_tests", "check_tests")
    g.add_conditional_edges("check_tests", route_after_check, ["human_approval", "plan_fix", "escalate"])
    g.add_conditional_edges("human_approval", route_after_approval, ["open_pr", "write_report"])
    g.add_edge("open_pr", "write_report")
    g.add_edge("escalate", "write_report")
    g.add_edge("write_report", END)
    return g
