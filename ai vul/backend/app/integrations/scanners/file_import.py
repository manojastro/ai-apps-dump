"""CSV / JSON vulnerability import (generic scanner export format).

Column names are matched case-insensitively against common aliases so exports from most
scanners can be imported after minimal renaming. Content is treated as untrusted input:
sizes are bounded and every row goes through the normaliser.
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from app.services.normalization import RawFinding

MAX_BYTES = 5 * 1024 * 1024
MAX_ROWS = 10_000

ALIASES: dict[str, tuple[str, ...]] = {
    "scanner_finding_id": ("finding_id", "id", "plugin_output_id", "qid_instance", "scanner_finding_id"),
    "cve_id": ("cve", "cve_id", "cveid", "cve id", "vulnerability", "vuln_id"),
    "asset_identifier": ("hostname", "host", "asset", "asset_name", "dns_name", "fqdn", "computer_name", "device_name"),
    "ip_address": ("ip", "ip_address", "ipv4", "address"),
    "device_id": ("device_id", "machine_id", "agent_id"),
    "software_vendor": ("vendor", "software_vendor", "product_vendor"),
    "software_name": ("software", "product", "software_name", "package", "product_name"),
    "software_version": ("version", "software_version", "installed_version", "product_version"),
    "severity": ("severity", "risk", "scanner_severity"),
    "cvss_score": ("cvss", "cvss_score", "cvss3", "cvss_v3", "base_score"),
    "description": ("description", "summary", "synopsis"),
    "first_seen": ("first_seen", "first_detected", "first_found"),
    "last_seen": ("last_seen", "last_detected", "last_found"),
}


class ImportFormatError(ValueError):
    pass


def _map_row(row: dict[str, Any], scanner: str) -> RawFinding:
    lowered = {str(k).strip().lower(): v for k, v in row.items() if k is not None}
    mapped: dict[str, Any] = {"scanner": scanner}
    for field, aliases in ALIASES.items():
        for alias in aliases:
            value = lowered.get(alias)
            if value not in (None, ""):
                mapped[field] = str(value).strip()[:4000] if not isinstance(value, int | float) else value
                break
    known = {a for aliases in ALIASES.values() for a in aliases}
    mapped["extra"] = {k: str(v)[:500] for k, v in lowered.items() if k not in known}
    return RawFinding.model_validate(mapped)


def parse_csv(content: bytes, scanner: str = "csv_import") -> list[RawFinding | Exception]:
    if len(content) > MAX_BYTES:
        raise ImportFormatError(f"File exceeds {MAX_BYTES // 1024 // 1024} MB limit")
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ImportFormatError("CSV has no header row")
    rows: list[RawFinding | Exception] = []
    for i, row in enumerate(reader):
        if i >= MAX_ROWS:
            raise ImportFormatError(f"CSV exceeds {MAX_ROWS} rows")
        try:
            rows.append(_map_row(row, scanner))
        except Exception as exc:  # validation error for this row only
            rows.append(exc)
    return rows


def parse_json(content: bytes, scanner: str = "json_import") -> list[RawFinding | Exception]:
    if len(content) > MAX_BYTES:
        raise ImportFormatError(f"File exceeds {MAX_BYTES // 1024 // 1024} MB limit")
    try:
        data = json.loads(content.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ImportFormatError(f"Invalid JSON: {exc}") from exc
    if isinstance(data, dict):
        data = data.get("findings") or data.get("vulnerabilities") or data.get("value") or []
    if not isinstance(data, list):
        raise ImportFormatError("JSON must be a list of findings or an object with a 'findings' array")
    if len(data) > MAX_ROWS:
        raise ImportFormatError(f"JSON exceeds {MAX_ROWS} findings")
    rows: list[RawFinding | Exception] = []
    for item in data:
        if not isinstance(item, dict):
            rows.append(ImportFormatError("finding entry is not an object"))
            continue
        try:
            rows.append(_map_row(item, scanner))
        except Exception as exc:
            rows.append(exc)
    return rows
