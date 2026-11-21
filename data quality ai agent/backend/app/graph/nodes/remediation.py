from typing import TYPE_CHECKING

from app.graph.state import RecoveryState
from app.llm.online import accumulate_usage
from app.models.domain import Attempt, Candidate, Risk
from app.security.policy import Role, invoke_tool, risk_for
from app.validators.engine import all_passed, validate

if TYPE_CHECKING:
    from app.graph.runtime import Runtime


class RemediationNodes:
    def __init__(self, runtime: "Runtime"):
        self.runtime = runtime

    async def plan(self, state: RecoveryState) -> RecoveryState:
        number = state["attempt_number"] + 1
        candidate = await self.runtime.provider.plan(
            state["selected_hypothesis"],
            state["aggregated_evidence"],
            state["retrieved_context"],
            state["validation_feedback"],
        )
        candidate = Candidate.model_validate(candidate.model_dump())
        if state["force_first_fail"] and number == 1:
            candidate = candidate.model_copy(
                update={
                    "amount_divisor": 1,
                    "summary": candidate.summary + " (demo: deliberately incorrect amount units)",
                }
            )
        return {
            "candidate_remediation": candidate,
            "attempt_number": number,
            "cost_metrics": accumulate_usage(state.get("cost_metrics", {}), self.runtime.provider),
        }

    async def risk(self, state: RecoveryState) -> RecoveryState:
        risk = risk_for(state["candidate_remediation"])
        return {
            "risk_level": risk,
            "failure_reason": "Critical destructive operation blocked"
            if risk == Risk.CRITICAL
            else "",
        }

    async def sandbox(self, state: RecoveryState) -> RecoveryState:
        async def audit(kind, tool, payload):
            await self.runtime.event(state["incident_id"], kind, tool, payload)

        candidate = await invoke_tool(
            Role.SANDBOX,
            "sandbox_apply",
            lambda: self.runtime.sandbox.apply(state["fixture"], state["candidate_remediation"]),
            audit,
        )
        return {"sandbox_result": candidate}

    async def replay(self, state: RecoveryState) -> RecoveryState:
        async def audit(kind, tool, payload):
            await self.runtime.event(state["incident_id"], kind, tool, payload)

        result = await invoke_tool(
            Role.SANDBOX,
            "pipeline_replay",
            lambda: self.runtime.pipeline.replay(state["fixture"], state["sandbox_result"]),
            audit,
        )
        return {"replay_result": result}

    async def validate(self, state: RecoveryState) -> RecoveryState:
        results = validate(state["fixture"], state["replay_result"])
        feedback = [
            f"{r.validator}: {r.evidence}; actual={r.actual}" for r in results if r.status == "FAIL"
        ]
        attempt = Attempt(
            number=state["attempt_number"],
            candidate=state["candidate_remediation"],
            validations=results,
            status="PASSED" if all_passed(results) else "REJECTED",
            feedback=feedback,
        )
        return {
            "validation_results": results,
            "validation_feedback": feedback,
            "attempt_history": [attempt],
        }
