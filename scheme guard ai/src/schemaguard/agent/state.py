"""Agent state. Plain JSON-serialisable values only, so checkpoints work on SQLite and Postgres."""

from __future__ import annotations

import operator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any, TypedDict

import networkx as nx

from schemaguard.config import Settings
from schemaguard.lineage.model import LineageGraph
from schemaguard.llm.base import LLMClient


class AgentState(TypedDict, total=False):
    run_id: str
    status: str  # running | no_impact | awaiting_approval | completed | rejected | escalated | failed
    change_event: dict[str, Any]
    old_schema: dict[str, Any]
    new_schema: dict[str, Any]
    schema_diff: dict[str, Any]
    change_class: dict[str, Any]
    explanation: str
    injection_findings: list[dict[str, Any]]
    lineage_version: int | None
    impacted_nodes: list[dict[str, Any]]
    assessments: Annotated[list[dict[str, Any]], operator.add]
    aggregate: dict[str, Any]
    fix_plan: dict[str, Any]
    patch: dict[str, Any]
    test_results: dict[str, Any]
    baseline_results: dict[str, Any]
    attempts: list[dict[str, Any]]
    retry_count: int
    approval_status: str  # not_requested | pending | approved | rejected
    approval: dict[str, Any]
    pr_url_or_patch_path: str
    report: str
    cost_tracking: dict[str, Any]
    errors: Annotated[list[str], operator.add]
    route_reason: str
    escalation_reason: str


class AssessInput(TypedDict):
    run_id: str
    asset: dict[str, Any]
    changes: list[dict[str, Any]]
    paths_by_change: dict[str, list[list[dict[str, Any]]]]


@dataclass
class Deps:
    """Everything nodes need besides state. Built once per service process."""

    settings: Settings
    llm: LLMClient
    lineage: LineageGraph
    lineage_version: int | None
    pipeline_dir: Path
    _flow: nx.DiGraph | None = field(default=None, repr=False)

    @property
    def flow(self) -> nx.DiGraph:
        if self._flow is None:
            self._flow = self.lineage.flow_digraph()
        return self._flow
