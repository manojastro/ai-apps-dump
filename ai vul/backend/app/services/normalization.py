"""Scanner-agnostic normalisation of raw vulnerability findings.

Every scanner adapter (mock Defender, real Defender, CSV, JSON, future Tenable/Qualys)
produces ``RawFinding`` objects. ``normalize_finding`` validates and canonicalises them
into ``NormalizedFinding`` - or rejects them with explicit reasons. Nothing is invented:
fields the scanner did not provide stay ``None``.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

CVE_PATTERN = re.compile(r"^CVE-(\d{4})-(\d{4,7})$")
_CVE_LOOSE = re.compile(r"cve[\s_\-]*(\d{4})[\s_\-]*(\d{4,7})", re.IGNORECASE)

SEVERITY_ALIASES = {
    "critical": "critical",
    "crit": "critical",
    "4": "critical",
    "urgent": "critical",
    "high": "high",
    "important": "high",
    "3": "high",
    "medium": "medium",
    "moderate": "medium",
    "2": "medium",
    "low": "low",
    "1": "low",
    "info": "none",
    "informational": "none",
    "none": "none",
    "0": "none",
}


class RawFinding(BaseModel):
    """Loosely-typed scanner output (untrusted input)."""

    scanner: str
    scanner_finding_id: str | None = None
    cve_id: str | None = None
    asset_identifier: str | None = None  # hostname / FQDN as reported
    ip_address: str | None = None
    device_id: str | None = None
    software_vendor: str | None = None
    software_name: str | None = None
    software_version: str | None = None
    severity: str | None = None
    cvss_score: float | str | None = None
    description: str | None = None
    first_seen: datetime | str | None = None
    last_seen: datetime | str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class NormalizedFinding(BaseModel):
    scanner: str
    scanner_finding_id: str | None
    cve_id: str
    asset_identifier: str
    ip_address: str | None
    device_id: str | None
    software_vendor: str | None
    software_name: str | None
    software_version: str | None
    scanner_severity: str
    scanner_cvss: float | None
    description: str | None
    first_seen: datetime
    last_seen: datetime
    dedup_key: str
    warnings: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class NormalizationError(ValueError):
    def __init__(self, reasons: list[str]) -> None:
        super().__init__("; ".join(reasons))
        self.reasons = reasons


def normalize_cve_id(value: str | None) -> str | None:
    """Return canonical ``CVE-YYYY-NNNN`` or None when the identifier is not a valid CVE."""
    if not value:
        return None
    candidate = value.strip().upper()
    if not CVE_PATTERN.match(candidate):
        m = _CVE_LOOSE.search(value)
        if not m:
            return None
        candidate = f"CVE-{m.group(1)}-{m.group(2)}"
    m = CVE_PATTERN.match(candidate)
    if not m:
        return None
    year = int(m.group(1))
    if year < 1999 or year > datetime.now(UTC).year + 1:
        return None
    return candidate


def normalize_severity(value: str | None) -> str:
    if value is None:
        return "unknown"
    return SEVERITY_ALIASES.get(str(value).strip().lower(), "unknown")


def severity_from_cvss(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= 9.0:
        return "critical"
    if score >= 7.0:
        return "high"
    if score >= 4.0:
        return "medium"
    if score > 0:
        return "low"
    return "none"


def _parse_dt(value: datetime | str | None) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    except ValueError:
        return None


def normalize_hostname(value: str | None) -> str | None:
    if not value:
        return None
    v = value.strip().lower().rstrip(".")
    return v or None


def dedup_key(scanner: str, asset_identifier: str, cve_id: str, software: str | None) -> str:
    """Identity of a finding: same scanner + asset + CVE + software == duplicate."""
    basis = "|".join([scanner.lower(), asset_identifier.lower(), cve_id.upper(), (software or "").lower()])
    return hashlib.sha256(basis.encode()).hexdigest()[:40]


def normalize_finding(raw: RawFinding, now: datetime | None = None) -> NormalizedFinding:
    now = now or datetime.now(UTC)
    reasons: list[str] = []
    warnings: list[str] = []
    cve = normalize_cve_id(raw.cve_id)
    if cve is None:
        reasons.append(f"invalid or missing CVE identifier: {raw.cve_id!r}")
    host = normalize_hostname(raw.asset_identifier) or normalize_hostname(raw.ip_address)
    if host is None and not raw.device_id:
        reasons.append("no asset identifier (hostname, IP or device id)")
    cvss: float | None = None
    if raw.cvss_score not in (None, ""):
        try:
            cvss = float(raw.cvss_score)  # type: ignore[arg-type]
            if not 0 <= cvss <= 10:
                warnings.append(f"scanner CVSS {cvss} out of range; ignored")
                cvss = None
        except (TypeError, ValueError):
            warnings.append(f"unparseable scanner CVSS {raw.cvss_score!r}; ignored")
    severity = normalize_severity(raw.severity)
    if severity == "unknown" and cvss is not None:
        severity = severity_from_cvss(cvss)
        warnings.append("scanner severity missing; derived from scanner CVSS")
    first_seen = _parse_dt(raw.first_seen) or now
    last_seen = _parse_dt(raw.last_seen) or first_seen
    if last_seen < first_seen:
        warnings.append("last_seen earlier than first_seen; swapped")
        first_seen, last_seen = last_seen, first_seen
    if reasons:
        raise NormalizationError(reasons)
    assert cve is not None
    identifier = host or str(raw.device_id)
    description = (raw.description or "").strip()[:4000] or None
    return NormalizedFinding(
        scanner=raw.scanner.lower(),
        scanner_finding_id=raw.scanner_finding_id,
        cve_id=cve,
        asset_identifier=identifier,
        ip_address=(raw.ip_address or "").strip() or None,
        device_id=(raw.device_id or "").strip() or None,
        software_vendor=(raw.software_vendor or "").strip().lower() or None,
        software_name=(raw.software_name or "").strip() or None,
        software_version=(raw.software_version or "").strip() or None,
        scanner_severity=severity,
        scanner_cvss=cvss,
        description=description,
        first_seen=first_seen,
        last_seen=last_seen,
        dedup_key=dedup_key(raw.scanner, identifier, cve, raw.software_name),
        warnings=warnings,
        raw=raw.model_dump(mode="json", exclude_none=True),
    )
