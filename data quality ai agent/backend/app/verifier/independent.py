from typing import Literal

from app.models.domain import (
    Candidate,
    Contract,
    Evidence,
    Hypothesis,
    Operation,
    Risk,
    ValidationResult,
    Verification,
)
from app.security.policy import risk_for
from app.validators.engine import REQUIRED_VALIDATORS, all_passed


class PublicIncident(Contract):
    id: str
    pipeline_id: str
    environment: str
    title: str


class VerifierPackage(Contract):
    incident: PublicIncident
    evidence: list[Evidence]
    hypothesis: Hypothesis
    candidate: Candidate
    validations: list[ValidationResult]


class IndependentVerifier:
    """Separate deterministic reviewer: no planner object, conversation, or hidden reasoning."""

    async def verify(self, package: VerifierPackage) -> Verification:
        evidence = {item.id: item for item in package.evidence}
        references = package.hypothesis.evidence_ids + package.candidate.evidence_ids
        unsupported = sorted({ref for ref in references if ref not in evidence})
        facts = [evidence[ref].facts for ref in package.hypothesis.evidence_ids if ref in evidence]
        supported, needed = False, None
        for fact in facts:
            match package.hypothesis.cause:
                case "schema_drift":
                    supported |= bool(
                        fact.get("customer_id_missing") and fact.get("customerId_present")
                    )
                    needed = Operation.MAP_CUSTOMER
                case "null_spike":
                    supported |= fact.get("null_customer_count", 0) > 0
                    needed = Operation.RESTORE_CUSTOMER
                case "duplicates":
                    supported |= fact.get("duplicate_count", 0) > 0
                    needed = Operation.DEDUPLICATE
                case "transformation_regression":
                    supported |= fact.get("amount_divisor") == 1
                    needed = Operation.CORRECT_AMOUNT
                case "dependency_failure":
                    supported |= bool(fact.get("upstream_failing"))
                    needed = Operation.RETRY_DEPENDENCY
        if not supported:
            unsupported.append("Root cause is not supported by cited observations")
        if needed not in package.candidate.operations:
            unsupported.append("Candidate does not address the supported cause")
        missing = sorted(set(REQUIRED_VALIDATORS) - {r.validator for r in package.validations})
        risk = risk_for(package.candidate)
        findings = [f"{risk} operation requires policy review"] if risk != Risk.LOW else []
        failed = not all_passed(package.validations)
        decision: Literal["APPROVE", "REJECT", "NEEDS_HUMAN"]
        if unsupported or missing or failed or risk == Risk.CRITICAL:
            decision = "REJECT"
        elif risk in (Risk.MEDIUM, Risk.HIGH):
            decision = "NEEDS_HUMAN"
        else:
            decision = "APPROVE"
        return Verification(
            decision=decision,
            confidence=1.0 if not unsupported else 0.2,
            unsupported_claims=unsupported,
            missing_checks=missing,
            risk_findings=findings,
            reason_summary="Evidence, permissions and mandatory check inventory reviewed"
            + ("; deterministic checks failed" if failed else ""),
        )
