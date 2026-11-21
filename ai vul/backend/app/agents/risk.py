"""Agent 4: Enterprise Risk Assessment (deterministic engine; the LLM never scores)."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import BaseModel

from app.agents.base import Agent, AgentContext
from app.models.vulnerability import Finding
from app.services.risk_service import assess_finding


class RiskOutput(BaseModel):
    risk_assessment_id: str
    risk_score: int
    score_band: list[int]
    risk_level: str
    priority: str
    business_impact: str
    coverage: float
    policy_version: str
    risk_factors: dict[str, float]
    factor_details: dict[str, Any]
    missing_factors: list[str]
    requires_immediate_review: bool
    rationale: list[str]
    sla_due_at: str | None


class RiskAssessmentAgent(Agent):
    name = "Risk Assessment Agent"
    node = "calculate_risk"
    description = "Computes the authoritative risk score with the deterministic, versioned policy engine."
    tools: ClassVar[set[str]] = set()
    boundary = "Deterministic Python only. No LLM involvement in scoring."
    evaluation = ["classification accuracy vs labelled cases", "missing data never scored as zero", "explainability"]
    Output = RiskOutput

    def run(self, ctx: AgentContext, state: dict[str, Any]) -> RiskOutput:
        finding = ctx.db.get(Finding, state["finding_id"])
        assert finding is not None
        ra, result = assess_finding(ctx.db, finding, ctx.run_id)
        return RiskOutput(
            risk_assessment_id=ra.id,
            risk_score=result.score,
            score_band=[result.score_lower, result.score_upper],
            risk_level=result.risk_level,
            priority=result.priority,
            business_impact=result.business_impact,
            coverage=result.coverage,
            policy_version=result.policy_version,
            risk_factors={k: f.points for k, f in result.factors.items()},
            factor_details=result.factors_dict(),
            missing_factors=result.missing_factors,
            requires_immediate_review=result.requires_immediate_review,
            rationale=result.rationale,
            sla_due_at=finding.sla_due_at.isoformat() if finding.sla_due_at else None,
        )
