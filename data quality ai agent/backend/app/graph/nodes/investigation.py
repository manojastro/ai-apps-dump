from typing import TYPE_CHECKING

from app.graph.state import RecoveryState
from app.llm.online import accumulate_usage
from app.security.policy import Role, invoke_tool

if TYPE_CHECKING:
    from app.graph.runtime import Runtime


class InvestigationNodes:
    def __init__(self, runtime: "Runtime"):
        self.runtime = runtime

    async def intake(self, state: RecoveryState) -> RecoveryState:
        case = state["incident"]
        return {
            "fixture": await self.runtime.pipeline.fixture(case),
            "pipeline_metadata": {"id": case.pipeline_id, "environment": case.environment},
        }

    async def context(self, state: RecoveryState) -> RecoveryState:
        case = state["incident"]
        documents = await self.runtime.knowledge.retrieve(
            f"{case.title} customer schema null duplicate amount dependency",
            case.pipeline_id,
            case.environment,
        )
        return {"retrieved_context": documents}

    def branch(self, name: str):
        async def investigate(state: RecoveryState) -> RecoveryState:
            async def audit(kind, tool, payload):
                await self.runtime.event(state["incident_id"], kind, tool, payload)

            item = await invoke_tool(
                Role.INVESTIGATOR,
                f"read_{name}",
                lambda: self.runtime.pipeline.investigate(state["incident"], name),
                audit,
            )
            return {"evidence": [item]}

        return investigate

    async def aggregate(self, state: RecoveryState) -> RecoveryState:
        merged = {item.id: item for item in state["evidence"]}
        return {"aggregated_evidence": sorted(merged.values(), key=lambda e: e.id)}

    async def diagnose(self, state: RecoveryState) -> RecoveryState:
        hypotheses = await self.runtime.provider.diagnose(
            state["aggregated_evidence"], state["retrieved_context"]
        )
        ranked = sorted(hypotheses, key=lambda h: h.confidence, reverse=True)
        return {
            "root_cause_hypotheses": ranked,
            "selected_hypothesis": ranked[0],
            "confidence": ranked[0].confidence,
            "cost_metrics": accumulate_usage(state.get("cost_metrics", {}), self.runtime.provider),
        }

    async def more_evidence(self, state: RecoveryState) -> RecoveryState:
        # A fresh round re-reads each source once; it cannot loop indefinitely.
        return {"evidence_round": state["evidence_round"] + 1}
