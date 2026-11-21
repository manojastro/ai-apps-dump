"""Builds risk inputs from persisted data and stores assessments."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.models.remediation import RiskAssessment
from app.models.vulnerability import Finding
from app.services.policy_store import get_risk_policy
from app.services.risk_engine import RiskInputs, RiskResult, calculate_risk


def inputs_for_finding(finding: Finding) -> RiskInputs:
    vuln = finding.vulnerability
    asset = finding.asset if finding.correlation_status == "matched" else None
    service = asset.business_service if asset else None
    srcs = vuln.intel_sources or {}
    return RiskInputs(
        cvss_score=vuln.cvss_score,
        epss_probability=vuln.epss_score,
        kev_listed=vuln.kev,
        asset_criticality=asset.business_criticality if asset else None,
        internet_exposed=asset.internet_exposed if asset else None,
        service_criticality=service.criticality if service else None,
        environment=asset.environment if asset else None,
        sources={
            "cvss": (srcs.get("nvd") or {}).get("reference", vuln.source),
            "epss": (srcs.get("epss") or {}).get("reference", "unknown"),
            "kev": (srcs.get("kev") or {}).get("reference", "unknown"),
            "asset_criticality": f"CMDB CI {asset.cmdb_sys_id}" if asset else "no reliable CMDB match",
            "internet_exposure": f"CMDB CI {asset.cmdb_sys_id}" if asset else "no reliable CMDB match",
        },
    )


def assess_finding(db: Session, finding: Finding, workflow_run_id: str | None = None) -> tuple[RiskAssessment, RiskResult]:
    policy = get_risk_policy(db)
    result = calculate_risk(inputs_for_finding(finding), policy)
    ra = RiskAssessment(
        finding_id=finding.id,
        workflow_run_id=workflow_run_id,
        score=result.score,
        score_lower=result.score_lower,
        score_upper=result.score_upper,
        risk_level=result.risk_level,
        priority=result.priority,
        business_impact=result.business_impact,
        coverage=result.coverage,
        policy_version=result.policy_version,
        factors=result.factors_dict(),
        missing_factors=result.missing_factors,
        requires_immediate_review=result.requires_immediate_review,
        rationale=result.rationale,
    )
    db.add(ra)
    finding.risk_score = result.score
    finding.risk_level = result.risk_level
    finding.priority = result.priority
    finding.sla_due_at = finding.first_seen_at + timedelta(days=result.sla_days)
    db.flush()
    return ra, result
