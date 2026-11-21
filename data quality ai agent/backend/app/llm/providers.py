from typing import Protocol

from app.models.domain import Candidate, Evidence, Hypothesis, KnowledgeDocument, Operation


class Provider(Protocol):
    async def diagnose(
        self, evidence: list[Evidence], context: list[KnowledgeDocument]
    ) -> list[Hypothesis]: ...
    async def plan(
        self,
        hypothesis: Hypothesis,
        evidence: list[Evidence],
        context: list[KnowledgeDocument],
        feedback: list[str],
    ) -> Candidate: ...


CAUSE_OPERATIONS = {
    "schema_drift": Operation.MAP_CUSTOMER,
    "null_spike": Operation.RESTORE_CUSTOMER,
    "duplicates": Operation.DEDUPLICATE,
    "transformation_regression": Operation.CORRECT_AMOUNT,
    "dependency_failure": Operation.RETRY_DEPENDENCY,
}


class DeterministicProvider:
    """Local rules consume measured evidence, never scenario IDs or golden labels."""

    async def diagnose(
        self, evidence: list[Evidence], context: list[KnowledgeDocument]
    ) -> list[Hypothesis]:
        hypotheses = []
        for item in evidence:
            facts = item.facts
            causes = [
                (
                    facts.get("customer_id_missing") and facts.get("customerId_present"),
                    "schema_drift",
                    "Upstream renamed customer_id to customerId",
                ),
                (
                    facts.get("null_customer_count", 0) > 0,
                    "null_spike",
                    "Customer enrichment is missing required identifiers",
                ),
                (
                    facts.get("duplicate_count", 0) > 0,
                    "duplicates",
                    "Retry ingestion duplicated transaction identifiers",
                ),
                (
                    facts.get("amount_divisor") == 1,
                    "transformation_regression",
                    "Currency conversion uses cents as major units",
                ),
                (
                    facts.get("upstream_failing"),
                    "dependency_failure",
                    "Transient upstream API failure exhausted current retries",
                ),
            ]
            for supported, cause, summary in causes:
                if supported:
                    hypotheses.append(
                        Hypothesis(
                            cause=cause, summary=summary, confidence=0.96, evidence_ids=[item.id]
                        )
                    )
        return hypotheses or [
            Hypothesis(
                cause="unknown",
                summary="Insufficient supporting evidence",
                confidence=0.2,
                evidence_ids=[],
            )
        ]

    async def plan(
        self,
        hypothesis: Hypothesis,
        evidence: list[Evidence],
        context: list[KnowledgeDocument],
        feedback: list[str],
    ) -> Candidate:
        operation = CAUSE_OPERATIONS.get(hypothesis.cause)
        if operation is None:
            raise ValueError("No safe local remediation for this hypothesis")
        operations = [operation]
        if any("TransformationValidator" in failure for failure in feedback):
            if Operation.CORRECT_AMOUNT not in operations:
                operations.append(Operation.CORRECT_AMOUNT)
        return Candidate(
            summary=f"Propose {operation.value.replace('_', ' ')}",
            operations=operations,
            evidence_ids=hypothesis.evidence_ids,
            amount_divisor=100 if Operation.CORRECT_AMOUNT in operations else None,
        )
