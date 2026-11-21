"""LangGraph state machine wiring Planner -> Explorer -> Verifier -> Reporter -> TestWriter.

Phase 1: only the Planner node exists. Other nodes raise NotImplementedError
until their phase lands — we never ship fake-success stubs.
"""

from __future__ import annotations

from typing import TypedDict

from sentinel.models import TestCase, UserStory


class SentinelState(TypedDict, total=False):
    story: UserStory
    git_diff: str | None
    test_cases: list[TestCase]


def planner_node(state: SentinelState) -> SentinelState:
    from sentinel.agents.planner import plan

    story = state["story"]
    return {"test_cases": plan(story, state.get("git_diff"))}


def explorer_node(state: SentinelState) -> SentinelState:
    raise NotImplementedError("Phase 2: Explorer (Playwright MCP) not built yet.")


def verifier_node(state: SentinelState) -> SentinelState:
    raise NotImplementedError("Phase 3: Verifier retry logic not built yet.")


def reporter_node(state: SentinelState) -> SentinelState:
    raise NotImplementedError("Phase 3: Reporter (Jira) not built yet.")


def testwriter_node(state: SentinelState) -> SentinelState:
    raise NotImplementedError("Phase 4: Test writer (PR) not built yet.")


def build_graph():
    """Phase 1 graph: Planner only. Full wiring lands with later phases."""
    try:
        from langgraph.graph import StateGraph
    except ImportError as exc:
        raise RuntimeError("langgraph not installed. Run: uv sync") from exc
    g = StateGraph(SentinelState)
    g.add_node("planner", planner_node)
    g.set_entry_point("planner")
    g.set_finish_point("planner")
    return g.compile()
