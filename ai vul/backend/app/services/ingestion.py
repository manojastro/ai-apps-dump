"""Finding ingestion pipeline: normalise -> deduplicate -> enrich -> correlate -> score."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vulnerability import Finding, ScanEvidence
from app.services.asset_matching import correlate_asset
from app.services.normalization import NormalizationError, RawFinding, normalize_finding
from app.services.risk_service import assess_finding
from app.services.threat_intel import ThreatIntelService
from app.services.vuln_intel import get_or_create_vulnerability

log = logging.getLogger("aegis.ingestion")


@dataclass
class IngestReport:
    total: int = 0
    created: int = 0
    duplicates: int = 0
    invalid: int = 0
    new_vulnerabilities: int = 0
    ambiguous_assets: int = 0
    unmatched_assets: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)
    finding_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def ingest_findings(db: Session, rows: Sequence[RawFinding | Exception], *, submitted_by: str = "system") -> IngestReport:
    report = IngestReport(total=len(rows))
    ti = ThreatIntelService(db)
    seen_in_batch: set[str] = set()
    for idx, row in enumerate(rows):
        if isinstance(row, Exception):
            report.invalid += 1
            report.errors.append({"row": idx + 1, "reasons": [str(row)[:300]]})
            continue
        try:
            nf = normalize_finding(row)
        except NormalizationError as exc:
            report.invalid += 1
            report.errors.append({"row": idx + 1, "reasons": exc.reasons})
            continue

        existing = db.scalar(select(Finding).where(Finding.dedup_key == nf.dedup_key))
        if existing is not None or nf.dedup_key in seen_in_batch:
            report.duplicates += 1
            if existing is not None:
                existing.last_seen_at = max(existing.last_seen_at, nf.last_seen)
                existing.duplicate_count += 1
            continue
        seen_in_batch.add(nf.dedup_key)

        vuln, created = get_or_create_vulnerability(
            db,
            nf.cve_id,
            scanner_description=nf.description,
            scanner_cvss=nf.scanner_cvss,
            scanner_severity=nf.scanner_severity,
            vendor_hint=nf.software_vendor,
            ti=ti,
        )
        report.new_vulnerabilities += int(created)
        vuln.last_detected_at = max(filter(None, [vuln.last_detected_at, nf.last_seen]))
        vuln.first_detected_at = min(filter(None, [vuln.first_detected_at, nf.first_seen]))

        match = correlate_asset(db, nf.asset_identifier, nf.ip_address, nf.device_id)
        if match.status == "ambiguous":
            report.ambiguous_assets += 1
        elif match.status == "unmatched":
            report.unmatched_assets += 1

        finding = Finding(
            dedup_key=nf.dedup_key,
            scanner=nf.scanner,
            scanner_finding_id=nf.scanner_finding_id,
            vulnerability_id=vuln.id,
            asset_id=match.asset_id,
            reported_asset_identifier=nf.asset_identifier,
            reported_ip=nf.ip_address,
            reported_device_id=nf.device_id,
            software_vendor=nf.software_vendor,
            software_name=nf.software_name,
            software_version=nf.software_version,
            scanner_severity=nf.scanner_severity,
            correlation_status=match.status,
            correlation_confidence=match.confidence,
            correlation_candidates=match.candidates,
            source_evidence={
                "normalized_from": nf.raw,
                "warnings": nf.warnings,
                "match_rule": match.rule,
                "match_explanation": match.explanation,
                "submitted_by": submitted_by,
            },
            first_seen_at=nf.first_seen,
            last_seen_at=nf.last_seen,
            detected_at=nf.last_seen,
        )
        db.add(finding)
        db.flush()
        db.refresh(finding)
        db.add(
            ScanEvidence(
                finding_id=finding.id,
                asset_identifier=nf.asset_identifier,
                device_id=nf.device_id,
                cve_id=nf.cve_id,
                scanner=nf.scanner,
                scan_id=nf.scanner_finding_id or f"import-{finding.id[:8]}",
                scanned_at=nf.last_seen,
                vulnerable=True,
                software_name=nf.software_name,
                software_version=nf.software_version,
                kind="baseline",
                raw={"source": "ingestion"},
                submitted_by=submitted_by,
            )
        )
        assess_finding(db, finding)
        report.created += 1
        report.finding_ids.append(finding.id)
    db.flush()
    log.info("ingested findings", extra={"report": {k: v for k, v in report.to_dict().items() if k != "finding_ids"}})
    return report
