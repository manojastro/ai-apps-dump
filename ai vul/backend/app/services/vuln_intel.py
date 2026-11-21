"""Vulnerability definition enrichment from authoritative sources (NVD, KEV, EPSS)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.types import utcnow
from app.models.vulnerability import Vulnerability
from app.services.normalization import severity_from_cvss
from app.services.threat_intel import IntelResult, ThreatIntelService


def _primary_product(ranges: list[dict[str, Any]], vendor_hint: str | None) -> tuple[str | None, str | None]:
    """Pick the CPE vendor/product that best represents the vulnerable software."""
    if vendor_hint:
        for r in ranges:
            if (r.get("vendor") or "").lower() == vendor_hint.lower():
                return r.get("vendor"), r.get("product")
    bounded = [
        r for r in ranges if any(r.get(k) for k in ("version_start_including", "version_end_excluding", "version_end_including"))
    ]
    pick = bounded[0] if bounded else (ranges[0] if ranges else None)
    return (pick.get("vendor"), pick.get("product")) if pick else (None, None)


def apply_nvd(vuln: Vulnerability, nvd: IntelResult, vendor_hint: str | None = None) -> None:
    if nvd.status != "found" or not nvd.data:
        return
    d = nvd.data
    cvss = d.get("cvss") or {}
    vuln.description = d.get("description") or vuln.description
    vuln.cvss_score = cvss.get("base_score")
    vuln.cvss_vector = cvss.get("vector")
    vuln.cvss_version = cvss.get("version")
    vuln.severity = (cvss.get("base_severity") or severity_from_cvss(vuln.cvss_score)).lower()
    vuln.cwes = d.get("cwes", [])
    if d.get("published"):
        vuln.published_at = datetime.fromisoformat(d["published"].replace("Z", "+00:00"))
    vuln.affected_ranges = d.get("cpe_ranges", [])
    vuln.references = d.get("references", [])
    vendor, product = _primary_product(vuln.affected_ranges, vendor_hint)
    vuln.affected_vendor = vendor
    vuln.affected_product = product


def apply_kev(vuln: Vulnerability, kev: IntelResult) -> None:
    if kev.status == "found" and kev.data:
        vuln.kev = True
        vuln.kev_date_added = kev.data.get("dateAdded")
        vuln.kev_due_date = kev.data.get("dueDate")
        vuln.kev_ransomware_use = kev.data.get("knownRansomwareCampaignUse")
        vuln.kev_required_action = kev.data.get("requiredAction")
        vuln.title = vuln.title or kev.data.get("vulnerabilityName")
    elif kev.status == "not_found":
        vuln.kev = False
        vuln.kev_date_added = vuln.kev_due_date = vuln.kev_ransomware_use = vuln.kev_required_action = None
    # unavailable -> leave unknown (None); never coerce to False


def apply_epss(vuln: Vulnerability, epss: IntelResult) -> None:
    if epss.status == "found" and epss.data:
        vuln.epss_score = epss.data.get("epss")
        vuln.epss_percentile = epss.data.get("percentile")
        vuln.epss_date = epss.data.get("date")


def provenance(result: IntelResult) -> dict[str, Any]:
    return {
        "status": result.status,
        "origin": result.origin,
        "reference": result.reference,
        "fetched_at": result.fetched_at,
        "notes": result.notes,
    }


def enrich_vulnerability(
    db: Session, vuln: Vulnerability, ti: ThreatIntelService | None = None, vendor_hint: str | None = None
) -> dict[str, IntelResult]:
    ti = ti or ThreatIntelService(db)
    nvd = ti.get_nvd(vuln.cve_id)
    kev = ti.get_kev(vuln.cve_id)
    epss = ti.get_epss(vuln.cve_id)
    apply_nvd(vuln, nvd, vendor_hint)
    apply_kev(vuln, kev)
    apply_epss(vuln, epss)
    if nvd.status == "found":
        vuln.source = "nvd_live" if nvd.origin in ("live", "cache") else "nvd_snapshot"
        vuln.evidence_status = "verified"
    else:
        vuln.evidence_status = "partial" if vuln.description or vuln.cvss_score is not None else "unverified"
    vuln.intel_sources = {"nvd": provenance(nvd), "kev": provenance(kev), "epss": provenance(epss)}
    vuln.intel_updated_at = utcnow()
    return {"nvd": nvd, "kev": kev, "epss": epss}


def get_or_create_vulnerability(
    db: Session,
    cve_id: str,
    *,
    scanner_description: str | None = None,
    scanner_cvss: float | None = None,
    scanner_severity: str | None = None,
    vendor_hint: str | None = None,
    ti: ThreatIntelService | None = None,
) -> tuple[Vulnerability, bool]:
    vuln = db.scalar(select(Vulnerability).where(Vulnerability.cve_id == cve_id))
    if vuln is not None:
        return vuln, False
    vuln = Vulnerability(
        cve_id=cve_id,
        description=scanner_description,
        cvss_score=scanner_cvss,
        severity=scanner_severity or severity_from_cvss(scanner_cvss),
        source="scanner",
        evidence_status="unverified",
        first_detected_at=utcnow(),
        last_detected_at=utcnow(),
    )
    db.add(vuln)
    enrich_vulnerability(db, vuln, ti, vendor_hint)
    if vuln.evidence_status != "verified" and scanner_description:
        # Keep scanner text but label it as unverified scanner-provided content.
        vuln.intel_sources = {**vuln.intel_sources, "description": {"origin": "scanner", "status": "unverified"}}
    db.flush()
    return vuln, True
