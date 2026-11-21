from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .schemas import Detection, Evidence, Hypothesis, RCAResult


@dataclass(frozen=True)
class AgentDefinition:
    name: str
    responsibility: str
    inputs: str
    outputs: str
    available_tools: tuple[str, ...]
    permission_boundary: str
    failure_behavior: str


AGENT_CATALOG = (
    AgentDefinition("Trace Analysis Agent", "Detect trajectory anomalies", "Typed trace", "Typed detections", ("trace_reader",), "Read-only", "Returns rule-level uncertainty"),
    AgentDefinition("Tool Evaluation Agent", "Validate tool selection and arguments", "Tool steps", "Accuracy findings", ("tool_contract_registry",), "Read-only", "Marks unknown tools invalid"),
    AgentDefinition("Security Evaluation Agent", "Identify unsafe action attempts", "Tool calls", "Risk findings", ("policy_engine",), "Read-only; cannot execute", "Fails closed"),
    AgentDefinition("Cost Analysis Agent", "Detect token and cost waste", "Usage metrics", "Cost findings", ("cost_calculator",), "Read-only", "Uses conservative thresholds"),
    AgentDefinition("Outcome Verification Agent", "Verify real outcomes independently", "Expected and external state", "Verified outcome", ("synthetic_artifact_store",), "Read-only", "Unobservable checks fail"),
    AgentDefinition("RCA Agent", "Synthesize evidence-grounded cause", "Detections and evidence", "Typed RCA", ("evidence_store",), "No direct actions", "Falls back to deterministic RCA"),
    AgentDefinition("Optimization Agent", "Propose guarded improvements", "RCA", "Risk-scored action", ("action_catalog",), "Allow-listed proposals only", "Never executes proposals"),
)


class ReasoningProvider(Protocol):
    @property
    def mode(self) -> str: ...

    def synthesize(self, incident_id: str, detections: list[Detection], evidence: list[Evidence]) -> RCAResult: ...


class DeterministicReasoningProvider:
    """Credential-free typed reasoning. It never invents facts outside supplied evidence."""

    mode = "mock"

    def synthesize(self, incident_id: str, detections: list[Detection], evidence: list[Evidence]) -> RCAResult:
        ranked = sorted(detections, key=lambda d: (severity_rank(d.severity.value), d.confidence), reverse=True)
        primary = ranked[0]
        relevant_ids = [item.evidence_id for item in evidence if item.fact == primary.code]
        hypotheses = [
            Hypothesis(
                cause=primary.title,
                confidence=primary.confidence,
                evidence_ids=relevant_ids,
                supporting_reason=primary.explanation,
            )
        ]
        for alternate in ranked[1:3]:
            hypotheses.append(
                Hypothesis(
                    cause=alternate.title,
                    confidence=round(alternate.confidence * 0.78, 3),
                    evidence_ids=[e.evidence_id for e in evidence if e.fact == alternate.code],
                    supporting_reason=alternate.explanation,
                )
            )
        return RCAResult(
            incident_id=incident_id,
            probable_root_cause=primary.title,
            confidence=primary.confidence,
            hypotheses=hypotheses,
            evidence=evidence,
            summary=f"{primary.title} is the most probable cause, supported by {len(relevant_ids)} persisted evidence record(s).",
        )


def severity_rank(value: str) -> int:
    return {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}[value]
