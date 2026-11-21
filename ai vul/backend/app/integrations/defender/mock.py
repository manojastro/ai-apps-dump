"""Simulated Microsoft Defender for Endpoint (Threat & Vulnerability Management).

Findings are *derived*, not hard-coded: each simulated device has an installed-software
inventory, and the adapter flags a CVE when an installed version falls inside the NVD CPE
affected range for that CVE. Applying a simulated patch changes the inventory, so the next
rescan genuinely reflects it.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.types import new_id, utcnow
from app.core.versions import match_cpe_ranges
from app.integrations.scanners.base import AdapterStatus, RescanResult, VulnerabilityScannerAdapter
from app.models.simulation import SimDevice
from app.services.normalization import RawFinding, severity_from_cvss
from app.services.threat_intel import ThreatIntelService

SCANNER_NAME = "mock_defender"


class MockDefenderAdapter(VulnerabilityScannerAdapter):
    name = SCANNER_NAME
    display_name = "Microsoft Defender for Endpoint (simulated)"

    def __init__(self, db: Session) -> None:
        self.db = db
        self.ti = ThreatIntelService(db)

    def _devices(self) -> list[SimDevice]:
        return list(self.db.scalars(select(SimDevice).options(selectinload(SimDevice.software)).order_by(SimDevice.id)))

    def _cvss(self, cve_id: str) -> float | None:
        rec = self.ti.snapshot.get("nvd", {}).get(cve_id) or {}
        return (rec.get("cvss") or {}).get("base_score")

    def _scan_device(self, device: SimDevice, ranges: dict[str, list[dict[str, Any]]]) -> list[RawFinding]:
        out: list[RawFinding] = []
        for sw in device.software:
            for cve_id, cve_ranges in ranges.items():
                m = match_cpe_ranges(cve_ranges, sw.vendor, sw.product, sw.version, sw.sw_edition)
                if not m.matched:
                    continue
                cvss = self._cvss(cve_id)
                out.append(
                    RawFinding(
                        scanner=SCANNER_NAME,
                        scanner_finding_id=f"{device.id[:12]}-{cve_id}",
                        cve_id=cve_id,
                        asset_identifier=device.computer_dns_name,
                        ip_address=device.last_ip_address,
                        device_id=device.id,
                        software_vendor=sw.vendor,
                        software_name=sw.display_name,
                        software_version=sw.version,
                        severity=severity_from_cvss(cvss).capitalize() if cvss is not None else None,
                        cvss_score=cvss,
                        first_seen=sw.updated_at,
                        last_seen=device.last_seen,
                        extra={"cpe_match": m.criteria, "match_reason": m.reason, "os_platform": device.os_platform},
                    )
                )
        return out

    def list_findings(self) -> list[RawFinding]:
        ranges = self.ti.known_ranges()
        return [f for d in self._devices() for f in self._scan_device(d, ranges)]

    def refresh_findings(self) -> list[RawFinding]:
        return self.list_findings()

    def get_finding(self, finding_id: str) -> RawFinding | None:
        return next((f for f in self.list_findings() if f.scanner_finding_id == finding_id), None)

    def get_affected_assets(self, finding_id: str) -> list[dict[str, Any]]:
        cve = finding_id.split("-", 1)[1] if finding_id.count("-") >= 3 else finding_id
        return [
            {"device_id": f.device_id, "computer_dns_name": f.asset_identifier, "ip": f.ip_address}
            for f in self.list_findings()
            if f.cve_id == cve
        ]

    def rescan(self, device_id: str | None, asset_identifier: str, cve_id: str) -> RescanResult:
        device = self.db.get(SimDevice, device_id) if device_id else None
        if device is None:
            device = self.db.scalar(select(SimDevice).where(SimDevice.computer_dns_name == asset_identifier))
        now = utcnow()
        if device is None:
            return RescanResult(
                asset_identifier,
                device_id,
                cve_id,
                True,
                None,
                None,
                now,
                f"scan-{new_id()[:8]}",
                "Device not found in Defender inventory; cannot confirm remediation",
                {"device_found": False},
            )
        device.last_seen = now
        ranges = {cve_id: self.ti.known_ranges().get(cve_id, [])}
        hits = self._scan_device(device, ranges)
        sw_name = hits[0].software_name if hits else None
        sw_version = hits[0].software_version if hits else None
        if not hits:
            # Report the installed version of the product that was previously vulnerable.
            vendor_products = {(r.get("vendor"), r.get("product")) for r in ranges[cve_id]}
            for sw in device.software:
                if (sw.vendor, sw.product) in vendor_products:
                    sw_name, sw_version = sw.display_name, sw.version
                    break
        return RescanResult(
            asset_identifier=device.computer_dns_name,
            device_id=device.id,
            cve_id=cve_id,
            vulnerable=bool(hits),
            software_name=sw_name,
            software_version=sw_version,
            scanned_at=now,
            scan_id=f"scan-{new_id()[:8]}",
            detail=hits[0].extra["match_reason"] if hits else "No installed software within the NVD affected range",
            raw={"device_found": True, "software_count": len(device.software)},
        )

    def status(self) -> AdapterStatus:
        count = len(self._devices())
        return AdapterStatus(
            self.name,
            self.display_name,
            "mock",
            "Mock",
            f"Simulated tenant with {count} onboarded devices; findings derived from NVD CPE ranges.",
            ["list_findings", "get_finding", "get_affected_assets", "refresh_findings", "rescan"],
            {"devices": count},
        )
