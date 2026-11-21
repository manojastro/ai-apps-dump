"""Microsoft Defender for Endpoint API adapter (real tenant).

Uses the documented Defender for Endpoint APIs with an Entra ID app registration
(client-credentials flow) holding the *Vulnerability.Read.All* and *Machine.Read.All*
application permissions. Vulnerability-management APIs require a Defender Vulnerability
Management entitlement - this adapter reports ``Unverified`` until ``test_connection``
succeeds against a real tenant, and is never shown as operational before that.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import Settings
from app.integrations.http import request_with_retry
from app.integrations.scanners.base import AdapterStatus, VulnerabilityScannerAdapter
from app.services.normalization import RawFinding

TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"  # noqa: S105 - URL, not a secret
MAX_PAGES = 50


class DefenderApiAdapter(VulnerabilityScannerAdapter):
    name = "defender"
    display_name = "Microsoft Defender for Endpoint"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._token: str | None = None
        self._token_exp = 0.0
        self._machines: dict[str, dict[str, Any]] = {}
        self.last_verified: bool = False

    # ---------------------------------------------------------------- auth
    def _get_token(self) -> str:
        if self._token and time.time() < self._token_exp - 60:
            return self._token
        s = self.settings
        resp = request_with_retry(
            "POST",
            TOKEN_URL.format(tenant=s.defender_tenant_id),
            data={
                "client_id": s.defender_client_id,
                "client_secret": s.defender_client_secret.get_secret_value(),
                "scope": f"{s.defender_api_base.rstrip('/')}/.default",
                "grant_type": "client_credentials",
            },
            timeout=20,
        )
        if resp.status_code != 200:
            raise PermissionError(f"Entra ID token request failed with HTTP {resp.status_code}")
        body = resp.json()
        self._token = body["access_token"]
        self._token_exp = time.time() + int(body.get("expires_in", 3600))
        return self._token

    def _get(self, path_or_url: str) -> dict[str, Any]:
        url = path_or_url if path_or_url.startswith("https://") else f"{self.settings.defender_api_base.rstrip('/')}{path_or_url}"
        resp = request_with_retry("GET", url, headers={"Authorization": f"Bearer {self._get_token()}"}, timeout=30)
        if resp.status_code == 401:
            self._token = None
            raise PermissionError("Defender API rejected the token (401)")
        if resp.status_code == 403:
            raise PermissionError("Defender API permission denied (403): check Vulnerability.Read.All / Machine.Read.All")
        resp.raise_for_status()
        return resp.json()

    def _paged(self, path: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        url: str | None = path
        pages = 0
        while url and pages < MAX_PAGES:
            data = self._get(url)
            items.extend(data.get("value", []))
            url = data.get("@odata.nextLink")
            pages += 1
        return items

    def _machine(self, machine_id: str) -> dict[str, Any]:
        if machine_id not in self._machines:
            self._machines[machine_id] = self._get(f"/api/machines/{machine_id}")
        return self._machines[machine_id]

    # ---------------------------------------------------------------- contract
    def _to_raw(self, row: dict[str, Any]) -> RawFinding:
        machine = self._machine(row["machineId"]) if row.get("machineId") else {}
        return RawFinding(
            scanner=self.name,
            scanner_finding_id=row.get("id"),
            cve_id=row.get("cveId"),
            asset_identifier=machine.get("computerDnsName"),
            ip_address=machine.get("lastIpAddress"),
            device_id=row.get("machineId"),
            software_vendor=row.get("productVendor"),
            software_name=row.get("productName"),
            software_version=row.get("productVersion"),
            severity=row.get("severity"),
            extra={"fixingKbId": row.get("fixingKbId"), "osPlatform": machine.get("osPlatform")},
        )

    def list_findings(self) -> list[RawFinding]:
        return [self._to_raw(r) for r in self._paged("/api/vulnerabilities/machinesVulnerabilities")]

    def refresh_findings(self) -> list[RawFinding]:
        self._machines.clear()
        return self.list_findings()

    def get_finding(self, finding_id: str) -> RawFinding | None:
        return next((f for f in self.list_findings() if f.scanner_finding_id == finding_id), None)

    def get_affected_assets(self, finding_id: str) -> list[dict[str, Any]]:
        return self._paged(f"/api/vulnerabilities/{finding_id}/machineReferences")

    def test_connection(self) -> dict[str, Any]:
        try:
            self._get("/api/machines?$top=1")
            self.last_verified = True
            return {"ok": True, "detail": "Authenticated and listed machines"}
        except (PermissionError, httpx.HTTPError, ValueError) as exc:
            self.last_verified = False
            return {"ok": False, "detail": str(exc)}

    def status(self) -> AdapterStatus:
        if not self.settings.defender_configured:
            return AdapterStatus(
                self.name,
                self.display_name,
                "live",
                "Not Configured",
                "Set DEFENDER_TENANT_ID, DEFENDER_CLIENT_ID and DEFENDER_CLIENT_SECRET.",
            )
        return AdapterStatus(
            self.name,
            self.display_name,
            "live",
            "Connected" if self.last_verified else "Unverified",
            "Credentials present. Run the connection test to verify tenant access and licensing.",
            ["list_findings", "get_finding", "get_affected_assets", "refresh_findings"],
        )
