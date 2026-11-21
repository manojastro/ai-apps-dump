"""Evidence normalization (M9): every diagnostic → spec-shaped records.

Spec fields: evidence_id, case_id, source_system, tool, timestamp, entity,
measurement, value, unit, confidence, raw_reference, sanitized_summary.

Stability contract (M8 depends on it): measurement names and value formats
are unchanged from the M8 ad-hoc shape (process_memory, disk, vpn, change,
cpu, ram, software_version, signin, dns, network_path). Only new fields wrap
around them. RCA triggers in rca.py keep working untouched.
"""

from __future__ import annotations

import json
from typing import Any

from common.redaction import redact_text
from database.models import utcnow

_SOURCE = {
    "query_device_health": "nexthink", "query_nexthink": "nexthink",
    "query_processes": "nexthink", "query_disk_health": "nexthink",
    "query_endpoint_events": "nexthink", "query_tanium": "tanium",
    "query_intune": "intune", "query_software_inventory": "intune",
    "query_software_catalog": "intune", "query_recent_changes": "intune",
    "query_patch_history": "intune", "query_network": "cloudflare",
    "query_dns": "cloudflare", "query_network_path": "cloudflare",
    "query_cloudflare": "cloudflare", "query_zscaler": "zscaler",
    "query_vpn_state": "zscaler", "query_entra": "entra",
    "query_signin_history": "entra", "query_account_state": "entra",
    "query_mfa_state": "entra", "query_access_state": "entra",
}

_CONFIDENCE = {
    "tanium": 0.95, "zscaler": 0.95, "cloudflare": 0.95, "nexthink": 0.9,
    "intune": 0.9, "entra": 0.9, "static-catalog": 0.5,
}

_UNIT = {"cpu": "%", "ram": "%", "disk": "%", "loss": "%",
         "process_memory": "MB", "latency": "ms", "network_path": "ms",
         "boot": "s"}


def _raw(fragment: Any) -> str:
    try:
        return redact_text(json.dumps(fragment, default=str)[:500])
    except (TypeError, ValueError):
        return ""


def normalize(tool_name: str, result: Any, case_id: str = "",
              device_id: str = "", start: int = 1) -> list[dict[str, Any]]:
    """Flatten one tool result into spec-shaped evidence records."""
    if not isinstance(result, dict):
        return []
    source = _SOURCE.get(tool_name, result.get("source", "unknown"))
    if not isinstance(source, str):
        source = "unknown"
    confidence = _CONFIDENCE.get(source, 0.9)
    if tool_name == "query_software_catalog":
        confidence = _CONFIDENCE["static-catalog"]
    timestamp = utcnow()
    records: list[dict[str, Any]] = []

    def add(measurement: str, value: Any, summary: str, entity: str = "",
            ref: Any = None, unit: str = "") -> None:
        records.append({
            "evidence_id": f"E{len(records) + start}",
            "case_id": case_id,
            "source_system": source,
            "tool": tool_name,
            "timestamp": timestamp,
            "entity": redact_text(entity or device_id),
            "measurement": measurement,
            "value": redact_text(str(value)),
            "unit": unit or _UNIT.get(measurement, ""),
            "confidence": confidence,
            "raw_reference": _raw(ref if ref is not None else value),
            "sanitized_summary": redact_text(summary),
        })

    if "cpu_pct" in result and "ram_pct" in result and "disk_pct" in result:
        add("cpu", result["cpu_pct"], f"CPU {result['cpu_pct']}%")
        add("ram", result["ram_pct"], f"RAM {result['ram_pct']}%")
        add("disk", result["disk_pct"], f"Disk {result['disk_pct']}%")
    for proc in result.get("processes", []):
        add("process_memory", proc.get("mem_mb"),
            f"{proc.get('name')} {proc.get('mem_mb')}MB",
            entity=str(proc.get("name")), ref=proc)
    for app in result.get("apps", result.get("inventory", [])):
        add("software_version", app.get("version"),
            f"{app.get('name')} {app.get('version')}"
            f"{'' if app.get('healthy', True) else ' UNHEALTHY'}",
            entity=str(app.get("name")), ref=app)
    for change in result.get("changes", result.get("events", result.get("patches", []))):
        add("change", change.get("summary", ""),
            f"Change: {change.get('summary', '')}",
            entity=str(change.get("target", "")), ref=change)
    if "connected" in result:
        add("vpn", result["connected"],
            f"VPN {'up' if result['connected'] else 'DOWN'}: {result.get('last_error', '')}")
    if "account_state" in result:
        add("identity", result["account_state"],
            f"Account {result['account_state']} locked={result.get('locked')}")
    for signin in result.get("signins", []):
        add("signin", signin.get("result"),
            f"{signin.get('event')} {signin.get('result')}: {signin.get('detail', '')}",
            ref=signin)
    if "dns_ok" in result and "processes" not in result:
        add("dns", result["dns_ok"], f"DNS {'ok' if result['dns_ok'] else 'FAIL'}")
    if "path_ok" in result:
        add("network_path", result.get("latency_ms"),
            f"Path latency {result.get('latency_ms')}ms loss {result.get('loss_pct')}%")
    return records
