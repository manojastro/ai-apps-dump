"""Agent framework: shared context, step reports and persistence helpers."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, ClassVar

from pydantic import BaseModel

from app.repositories.repo import InvestigationRepository
from app.schemas.api import (
    Action,
    Evidence,
    Hypothesis,
    RegressionOut,
    RiskAssessment,
    RootCauseAnalysis,
)


class StepReport(BaseModel):
    agent: str
    duration_ms: int
    summary: dict[str, Any] = {}
    evidence: list[Evidence] = []
    hypotheses: list[Hypothesis] = []


@dataclass
class AgentContext:
    change_id: int
    change_title: str
    base_payload_dict: dict[str, Any]
    ops: list[dict[str, Any]] = field(default_factory=list)
    journal: list[dict[str, Any]] = field(default_factory=list)
    candidate_payload_dict: dict[str, Any] | None = None
    base_summary: dict[str, Any] = field(default_factory=dict)
    candidate_summary: dict[str, Any] | None = None
    matrix_diff: dict[str, Any] = field(default_factory=dict)
    route_changes: list[dict[str, Any]] = field(default_factory=list)
    intent_results_base: list[dict[str, Any]] = field(default_factory=list)
    intent_results_candidate: list[dict[str, Any]] = field(default_factory=list)
    topology_findings: list[dict[str, Any]] = field(default_factory=list)
    regressions: list[RegressionOut] = field(default_factory=list)
    blast_radius_devices: list[str] = field(default_factory=list)
    risk: RiskAssessment | None = None
    rca: RootCauseAnalysis | None = None
    proposed_fix_ops: list[dict[str, Any]] = field(default_factory=list)
    proposed_fix_diff: str | None = None
    fixed_candidate_payload_dict: dict[str, Any] | None = None
    fix_validated: bool = False
    stages: list[dict[str, Any]] = field(default_factory=list)


class BaseAgent:
    name: ClassVar = "agent"

    def run(self, ctx: AgentContext) -> StepReport:
        started = time.perf_counter()
        summary = self.execute(ctx)
        duration_ms = int((time.perf_counter() - started) * 1000)
        return StepReport(agent=self.name, duration_ms=duration_ms,
                          summary=summary,
                          evidence=self.evidence(ctx),
                          hypotheses=self.hypotheses(ctx))

    def execute(self, ctx: AgentContext) -> dict[str, Any]:
        raise NotImplementedError

    def evidence(self, ctx: AgentContext) -> list[Evidence]:
        return []

    def hypotheses(self, ctx: AgentContext) -> list[Hypothesis]:
        return []

    @staticmethod
    def persist(repo: InvestigationRepository, run_id: int, report: StepReport) -> None:
        inv = repo.create(run_id, report.agent, report.duration_ms, report.summary)
        for ev in report.evidence:
            repo.evidence(inv.id, ev.kind, ev.source, {"summary": ev.summary,
                                                       "data": ev.data})
        for hy in report.hypotheses:
            repo.hypothesis(inv.id, hy.statement, hy.status, hy.score, hy.refuted_by)
