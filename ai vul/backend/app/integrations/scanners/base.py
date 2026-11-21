"""Generic scanner adapter contract.

The stack is synchronous end to end (SQLAlchemy sessions + LangGraph worker threads), so
the contract is synchronous as well; adapters perform blocking I/O with strict timeouts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.services.normalization import RawFinding


@dataclass
class AdapterStatus:
    name: str
    display_name: str
    mode: str  # mock | live | file
    status: str  # Mock | Connected | Not Configured | Error | Unsupported | Unverified
    detail: str = ""
    capabilities: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class RescanResult:
    asset_identifier: str
    device_id: str | None
    cve_id: str
    vulnerable: bool
    software_name: str | None
    software_version: str | None
    scanned_at: Any
    scan_id: str
    detail: str
    raw: dict[str, Any] = field(default_factory=dict)


class VulnerabilityScannerAdapter(ABC):
    name: str = "scanner"
    display_name: str = "Scanner"

    @abstractmethod
    def list_findings(self) -> list[RawFinding]: ...

    @abstractmethod
    def get_finding(self, finding_id: str) -> RawFinding | None: ...

    @abstractmethod
    def get_affected_assets(self, finding_id: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def refresh_findings(self) -> list[RawFinding]: ...

    @abstractmethod
    def status(self) -> AdapterStatus: ...

    def rescan(self, device_id: str | None, asset_identifier: str, cve_id: str) -> RescanResult:
        raise NotImplementedError(f"{self.display_name} does not support targeted rescans")


class UnsupportedScannerAdapter(VulnerabilityScannerAdapter):
    """Extension point for scanners that are designed for but not implemented (Tenable, Qualys)."""

    def __init__(self, name: str, display_name: str, docs: str) -> None:
        self.name = name
        self.display_name = display_name
        self.docs = docs

    def _unsupported(self) -> NotImplementedError:
        return NotImplementedError(f"{self.display_name} adapter is an extension point and is not implemented")

    def list_findings(self) -> list[RawFinding]:
        raise self._unsupported()

    def get_finding(self, finding_id: str) -> RawFinding | None:
        raise self._unsupported()

    def get_affected_assets(self, finding_id: str) -> list[dict[str, Any]]:
        raise self._unsupported()

    def refresh_findings(self) -> list[RawFinding]:
        raise self._unsupported()

    def status(self) -> AdapterStatus:
        return AdapterStatus(
            self.name,
            self.display_name,
            "none",
            "Unsupported",
            f"Extension point only. Implement VulnerabilityScannerAdapter using {self.docs}; "
            "map results to RawFinding and register it in integrations/registry.py.",
        )
