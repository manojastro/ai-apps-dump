"""Agent 1 (Vulnerability Intelligence) and Agent 3 (Threat Intelligence)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select

from app.agents.base import Agent, AgentContext, AgentFailure
from app.core.versions import match_cpe_ranges
from app.models.vulnerability import Finding, Vulnerability
from app.services.normalization import normalize_cve_id
from app.services.threat_intel import IntelResult, _age_hours
from app.services.vuln_intel import apply_epss, apply_kev, provenance


class VulnIntelOutput(BaseModel):
    cve_id: str
    cve_valid: bool
    severity: str
    cvss_score: float | None
    cvss_vector: str | None
    affected_vendor: str | None
    affected_product: str | None
    affected_version: str | None
    version_in_affected_range: bool | None
    range_evidence: str | None
    fixed_version_per_nvd: str | None
    description: str | None
    source: str
    source_reference: str
    source_fetched_at: str | None
    verified: bool
    duplicate_findings: list[dict[str, Any]] = Field(default_factory=list)
    data_quality: str
    completeness_checks: dict[str, bool]
    confidence: float = Field(description="Share of completeness checks satisfied (rule-based, not model-generated)")
    notes: list[str] = Field(default_factory=list)


class VulnerabilityIntelligenceAgent(Agent):
    name = "Vulnerability Intelligence Agent"
    node = "normalize"
    description = "Validates the CVE, normalises scanner data, retrieves authoritative NVD data and detects duplicates."
    tools = {"threat_get_cve"}
    evaluation = ["CVE validation accuracy", "never invents CVE details", "duplicate detection", "range matching"]
    Output = VulnIntelOutput

    def run(self, ctx: AgentContext, state: dict[str, Any]) -> VulnIntelOutput:
        finding = ctx.db.get(Finding, state["finding_id"])
        if finding is None:
            raise AgentFailure("finding not found")
        vuln = finding.vulnerability
        notes: list[str] = []
        cve = normalize_cve_id(vuln.cve_id)
        if cve is None:
            raise AgentFailure(f"invalid CVE identifier {vuln.cve_id!r}")
        nvd = ctx.tool("threat_get_cve", cve_id=cve)
        verified = nvd["status"] == "found"
        if not verified:
            notes.append("Authoritative NVD record unavailable: description/CVSS are scanner-provided and UNVERIFIED")

        in_range: bool | None = None
        range_evidence = fixed = None
        if verified and finding.software_vendor and finding.software_version and vuln.affected_product:
            m = match_cpe_ranges(
                nvd.get("affected_ranges") or vuln.affected_ranges or [],
                finding.software_vendor,
                vuln.affected_product,
                finding.software_version,
            )
            in_range = m.matched
            range_evidence = m.reason
            fixed = m.fixed_version
            if m.upper_bound_inclusive:
                notes.append(
                    f"NVD lists versions up to and including {m.upper_bound_inclusive} as affected; "
                    "the first fixed release is not stated by this record"
                )
            if not m.matched:
                notes.append("Installed version is outside NVD affected ranges: possible false positive, needs review")
        elif not finding.software_version:
            notes.append("Scanner did not report the installed version")

        duplicates = [
            {"finding_id": f.id, "scanner": f.scanner, "asset": f.reported_asset_identifier}
            for f in ctx.db.scalars(
                select(Finding).where(
                    Finding.vulnerability_id == vuln.id,
                    Finding.id != finding.id,
                    Finding.asset_id == finding.asset_id,
                    Finding.asset_id.is_not(None),
                )
            )
        ]
        if duplicates:
            notes.append(f"{len(duplicates)} other finding(s) report this CVE on the same asset (cross-scanner duplicate)")

        checks = {
            "cve_valid": True,
            "authoritative_record": verified,
            "cvss_present": vuln.cvss_score is not None,
            "description_present": bool(vuln.description),
            "product_identified": bool(vuln.affected_product),
            "installed_version_known": bool(finding.software_version),
            "version_range_confirmed": in_range is True,
        }
        score = round(sum(checks.values()) / len(checks), 2)
        quality = "complete" if score >= 0.85 else "partial" if score >= 0.5 else "insufficient"
        return VulnIntelOutput(
            cve_id=cve,
            cve_valid=True,
            severity=vuln.severity,
            cvss_score=vuln.cvss_score,
            cvss_vector=vuln.cvss_vector,
            affected_vendor=vuln.affected_vendor,
            affected_product=vuln.affected_product,
            affected_version=finding.software_version,
            version_in_affected_range=in_range,
            range_evidence=range_evidence,
            fixed_version_per_nvd=fixed,
            description=vuln.description,
            source=vuln.source,
            source_reference=nvd["reference"],
            source_fetched_at=nvd.get("fetched_at"),
            verified=verified,
            duplicate_findings=duplicates,
            data_quality=quality,
            completeness_checks=checks,
            confidence=score,
            notes=notes,
        )


class ThreatIntelOutput(BaseModel):
    cve_id: str
    known_exploited: bool | None
    kev_status: str
    kev_date_added: str | None
    kev_due_date: str | None
    kev_ransomware_use: str | None
    kev_required_action: str | None
    epss_probability: float | None
    epss_percentile: float | None
    epss_date: str | None
    public_exploit_reported: bool | None
    source_timestamp: str | None
    data_age_hours: float | None
    verified: bool
    sources: dict[str, Any]
    risk_notes: list[str]


def _as_result(d: dict[str, Any]) -> IntelResult:
    return IntelResult(
        d["source"], d["cve_id"], d["status"], d.get("data"), d["origin"], d.get("fetched_at"), d["reference"], d.get("notes", [])
    )


class ThreatIntelligenceAgent(Agent):
    name = "Threat Intelligence Agent"
    node = "enrich_threat"
    description = "Checks CISA KEV and FIRST EPSS, separating confirmed exploitation from exploitation probability."
    tools = {"threat_check_kev", "threat_get_epss"}
    evaluation = ["KEV/EPSS correctness", "never treats EPSS as proof", "freshness reporting", "missing-data handling"]
    Output = ThreatIntelOutput

    def run(self, ctx: AgentContext, state: dict[str, Any]) -> ThreatIntelOutput:
        finding = ctx.db.get(Finding, state["finding_id"])
        assert finding is not None
        vuln: Vulnerability = finding.vulnerability
        kev = _as_result(ctx.tool("threat_check_kev", cve_id=vuln.cve_id))
        epss = _as_result(ctx.tool("threat_get_epss", cve_id=vuln.cve_id))
        apply_kev(vuln, kev)
        apply_epss(vuln, epss)
        vuln.intel_sources = {**(vuln.intel_sources or {}), "kev": provenance(kev), "epss": provenance(epss)}

        notes: list[str] = []
        known = True if kev.status == "found" else False if kev.status == "not_found" else None
        if known:
            notes.append("CISA KEV lists this CVE: exploitation in the wild is CONFIRMED by CISA")
        elif known is False:
            notes.append("Not in CISA KEV: no confirmed exploitation recorded by CISA (not proof of safety)")
        else:
            notes.append("KEV status could not be verified")
        if vuln.epss_score is not None:
            notes.append(
                f"EPSS {vuln.epss_score:.4f} (percentile {vuln.epss_percentile:.2f}) is a 30-day exploitation "
                "probability estimate, not evidence of exploitation"
            )
        else:
            notes.append("EPSS probability unavailable")
        if kev.origin == "snapshot" or epss.origin == "snapshot":
            notes.append("Using offline snapshot of real KEV/EPSS data; refresh in live mode for current values")
        timestamps = [t for t in (kev.fetched_at, epss.fetched_at) if t]
        oldest = min(timestamps) if timestamps else None
        return ThreatIntelOutput(
            cve_id=vuln.cve_id,
            known_exploited=known,
            kev_status=kev.status,
            kev_date_added=vuln.kev_date_added,
            kev_due_date=vuln.kev_due_date,
            kev_ransomware_use=vuln.kev_ransomware_use,
            kev_required_action=vuln.kev_required_action,
            epss_probability=vuln.epss_score,
            epss_percentile=vuln.epss_percentile,
            epss_date=vuln.epss_date,
            public_exploit_reported=None,  # no exploit-database source configured: unknown, not false
            source_timestamp=oldest,
            data_age_hours=_age_hours(oldest),
            verified=kev.status != "unavailable" and epss.status != "unavailable",
            sources={"kev": provenance(kev), "epss": provenance(epss)},
            risk_notes=notes,
        )
