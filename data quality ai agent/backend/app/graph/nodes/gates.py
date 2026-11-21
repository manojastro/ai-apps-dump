import hashlib
import json
from typing import TYPE_CHECKING

from langgraph.types import interrupt

from app.graph.state import RecoveryState
from app.models.domain import Approval, Status
from app.validators.engine import all_passed, validate
from app.verifier.independent import PublicIncident, VerifierPackage

if TYPE_CHECKING:
    from app.graph.runtime import Runtime


class GateNodes:
    def __init__(self, runtime: "Runtime"):
        self.runtime = runtime

    async def verify(self, state: RecoveryState) -> RecoveryState:
        package = VerifierPackage(
            incident=PublicIncident.model_validate(
                state["incident"].model_dump(include={"id", "pipeline_id", "environment", "title"})
            ),
            evidence=state["aggregated_evidence"],
            hypothesis=state["selected_hypothesis"],
            candidate=state["candidate_remediation"],
            validations=state["validation_results"],
        )
        result = await self.runtime.verifier.verify(package)
        return {"verification_result": result}

    async def approval(self, state: RecoveryState) -> RecoveryState:
        response = interrupt(
            {
                "kind": "artifact_approval",
                "risk": state["risk_level"],
                "candidate": state["candidate_remediation"].model_dump(mode="json"),
                "scope": "Release a reviewed recovery artifact only",
            }
        )
        decision = Approval.model_validate(response)
        return {
            "approval_status": "APPROVED" if decision.approved else "REJECTED",
            "human_decision": decision.model_dump(),
        }

    async def insufficient(self, state: RecoveryState) -> RecoveryState:
        decision = interrupt(
            {
                "kind": "insufficient_evidence",
                "reason": "Two evidence rounds did not meet the confidence threshold",
                "scope": "Acknowledge escalation; this cannot approve an unproven remediation",
            }
        )
        Approval.model_validate(decision)
        return {
            "final_status": Status.FAILED,
            "failure_reason": "Insufficient evidence; manual investigation required",
        }

    async def artifact(self, state: RecoveryState) -> RecoveryState:
        # Defense in depth: a human or a provider can never bypass the deterministic gate.
        if not all_passed(state["validation_results"]):
            raise ValueError("Cannot publish an artifact with failed or missing critical checks")
        if state["verification_result"].decision == "REJECT":
            raise ValueError("Cannot publish a verifier-rejected artifact")
        artifact = self.runtime.source_control.artifact(
            state["incident"], state["candidate_remediation"]
        )
        # Re-execute against a fresh copy for post-validation before releasing the artifact.
        result = await self.runtime.pipeline.replay(
            state["fixture"], state["candidate_remediation"]
        )
        checks = validate(state["fixture"], result)
        if not all_passed(checks):
            return {"final_status": Status.FAILED, "failure_reason": "Post-validation failed"}
        artifact["post_validation"] = "PASS"
        artifact["evidence_ids"] = state["candidate_remediation"].evidence_ids
        artifact["sha256"] = hashlib.sha256(
            json.dumps(artifact, sort_keys=True).encode()
        ).hexdigest()
        return {"final_remediation": artifact, "final_status": Status.COMPLETED}

    async def failed(self, state: RecoveryState) -> RecoveryState:
        return {
            "final_status": Status.FAILED,
            "failure_reason": state.get("failure_reason")
            or f"Mandatory checks failed after {state['attempt_number']} attempts",
        }

    async def rejected(self, state: RecoveryState) -> RecoveryState:
        return {
            "final_status": Status.REJECTED,
            "failure_reason": "Verifier or human reviewer rejected this remediation",
        }
