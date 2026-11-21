"""Evidence validation (deterministic). Decides whether a plan may go to approval or needs manual review."""

from __future__ import annotations

import re
from typing import Any, ClassVar

from pydantic import BaseModel

from app.agents.base import Agent, AgentContext
from app.models.enums import PlanStatus
from app.models.remediation import RemediationPlan
from app.models.vulnerability import Finding
from app.services.policy_store import get_risk_policy

VERSION_TOKEN = re.compile(r"\b\d+\.\d+(?:\.\d+)*(?:[a-z]\d+)?\b")
UNSAFE_PATTERNS = [
    (re.compile(r"curl[^\n|]*\|\s*(ba)?sh", re.I), "pipes a remote script into a shell"),
    (re.compile(r"\brm\s+-rf\b", re.I), "recursive deletion command"),
    (re.compile(r"disable\s+(the\s+)?(firewall|antivirus|edr|defender|selinux)", re.I), "disables a security control"),
    (
        re.compile(r"(iptables\s+-F|ufw\s+disable|netsh\s+advfirewall\s+set\s+\w+\s+state\s+off)", re.I),
        "flushes/disables firewall",
    ),
    (re.compile(r"chmod\s+777", re.I), "world-writable permissions"),
]


class ValidationIssue(BaseModel):
    code: str
    severity: str  # info | warning | blocking
    message: str
    blocking: bool = False


class ValidationOutput(BaseModel):
    plan_id: str
    status: str  # passed | needs_expert_validation | insufficient
    route: str  # approval | manual_review
    issues: list[ValidationIssue]
    citation_validity: float
    checks: dict[str, bool]


def _plan_text(plan: RemediationPlan) -> str:
    parts = [plan.title, plan.summary, plan.recommended_action, plan.expected_impact, plan.maintenance_window]
    parts += [s.get("step", "") if isinstance(s, dict) else str(s) for s in plan.implementation_steps]
    parts += (
        list(plan.verification_steps) + list(plan.rollback_steps) + list(plan.prerequisites) + list(plan.testing_requirements)
    )
    return "\n".join(p for p in parts if p)


def validate_plan(plan: RemediationPlan, finding: Finding, coverage: float | None, min_coverage: float) -> ValidationOutput:
    issues: list[ValidationIssue] = []

    def issue(code: str, severity: str, message: str) -> None:
        issues.append(ValidationIssue(code=code, severity=severity, message=message, blocking=severity == "blocking"))

    evidence = [e for e in plan.evidence_refs if not e.get("invalid")]
    ev_ids = {e["id"] for e in evidence}
    cited: set[str] = {e["id"] for e in plan.evidence_refs if e.get("cited")}
    for step in plan.implementation_steps:
        if isinstance(step, dict):
            cited |= set(step.get("evidence_refs", []))
    invalid = sorted(c for c in cited if c not in ev_ids)
    citation_validity = round(1 - len(invalid) / len(cited), 2) if cited else 0.0
    if invalid:
        issue("invalid_citation", "blocking", f"Plan cites evidence that does not exist: {invalid}")
    if not cited:
        issue("no_citations", "warning", "Plan does not cite any evidence")

    evidence_text = " ".join(str(e.get("content", "")) for e in evidence)
    evidence_versions = set(VERSION_TOKEN.findall(evidence_text))
    fixed_versions = {
        str(e["content"].get("first_unaffected_version"))
        for e in evidence
        if e.get("type") == "affected_range"
        and isinstance(e.get("content"), dict)
        and e["content"].get("first_unaffected_version")
    }
    if plan.target_version and plan.target_version not in fixed_versions:
        issue(
            "unsupported_version_claim",
            "warning",
            f"Target version {plan.target_version} is not supported by evidence (fixed versions in evidence: "
            f"{sorted(fixed_versions) or 'none'})",
        )
    unsupported = sorted(v for v in set(VERSION_TOKEN.findall(_plan_text(plan))) if v not in evidence_versions)
    if unsupported:
        issue("unsupported_version_mention", "warning", f"Version strings not found in evidence: {unsupported[:8]}")

    for pattern, why in UNSAFE_PATTERNS:
        if pattern.search(_plan_text(plan)):
            issue("unsafe_instruction", "blocking", f"Plan contains a prohibited action: {why}")

    if not plan.rollback_steps:
        issue("missing_rollback", "blocking", "Plan has no rollback strategy")
    if not plan.verification_steps:
        issue("missing_verification", "blocking", "Plan has no verification steps")
    if finding.correlation_status != "matched" or finding.asset_id is None:
        issue("asset_unresolved", "blocking", "Affected asset is not reliably matched to the CMDB")
    elif finding.asset and not finding.asset.owner:
        issue("missing_owner", "warning", "Asset has no owner in the CMDB; approver must assign an implementer")
    if finding.vulnerability.evidence_status != "verified":
        issue("unverified_vulnerability", "warning", "Vulnerability data not verified against an authoritative source")
    if coverage is not None and coverage < min_coverage:
        issue("low_risk_coverage", "blocking", f"Risk data coverage {coverage:.0%} is below {min_coverage:.0%}")
    if plan.requires_expert_validation:
        issue("expert_validation_required", "warning", "Planner flagged the plan as requiring expert validation")

    blocking = any(i.blocking for i in issues)
    needs_expert = any(
        i.code
        in ("unsupported_version_claim", "unsupported_version_mention", "unverified_vulnerability", "expert_validation_required")
        for i in issues
    )
    status = "insufficient" if blocking else "needs_expert_validation" if needs_expert else "passed"
    checks = {
        "citations_valid": not invalid,
        "versions_grounded": not any(i.code.startswith("unsupported_version") for i in issues),
        "no_unsafe_actions": not any(i.code == "unsafe_instruction" for i in issues),
        "rollback_present": bool(plan.rollback_steps),
        "verification_present": bool(plan.verification_steps),
        "asset_resolved": finding.correlation_status == "matched",
        "risk_coverage_ok": coverage is None or coverage >= min_coverage,
    }
    return ValidationOutput(
        plan_id=plan.id,
        status=status,
        route="manual_review" if blocking else "approval",
        issues=issues,
        citation_validity=citation_validity,
        checks=checks,
    )


class ValidationAgent(Agent):
    name = "Evidence Validation Agent"
    node = "validate_evidence"
    description = "Deterministically checks citations, version claims, unsafe actions and data sufficiency."
    tools: ClassVar[set[str]] = set()
    boundary = "Deterministic checks only; routes to manual review when evidence is insufficient."
    evaluation = ["detects unsupported version claims", "detects invalid citations", "blocks unsafe instructions"]
    Output = ValidationOutput

    def run(self, ctx: AgentContext, state: dict[str, Any]) -> ValidationOutput:
        plan = ctx.db.get(RemediationPlan, state["plan_id"])
        finding = ctx.db.get(Finding, state["finding_id"])
        assert plan is not None and finding is not None
        coverage = (state.get("risk") or {}).get("coverage")
        result = validate_plan(plan, finding, coverage, get_risk_policy(ctx.db).min_coverage_for_auto_routing)
        plan.validation = result.model_dump(mode="json")
        plan.requires_expert_validation = plan.requires_expert_validation or result.status == "needs_expert_validation"
        if result.route == "approval" and plan.status == PlanStatus.DRAFT:
            plan.status = PlanStatus.ASSESSMENT_COMPLETE
        return result
