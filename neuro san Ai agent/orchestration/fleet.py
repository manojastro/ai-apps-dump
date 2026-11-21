"""Fleet intelligence (M23): one confirmed root cause → every at-risk device.

Derive a failure signature, search the estate, classify each match by state
(AFFECTED/EARLY/AT_RISK) and by per-device policy (auto/approval/blocked).
Policy is evaluated PER DEVICE — never cached across the fleet. Matches
persist to fleet_matches. Proactive execution is M24; this module never
mutates devices.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Any

AFFECTED, EARLY, AT_RISK = "affected", "early", "at_risk"
AUTO, NEEDS_APPROVAL, BLOCKED = "auto_remediate", "approval_required", "blocked"


def derive_failure_signature(root_cause: str, evidence: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Root-cause title (+ supporting evidence) → stable signature + context."""
    lowered = root_cause.lower()
    version = ""
    for item in evidence or []:
        if item.get("measurement") == "software_version" and "teams" in str(item.get("entity", "")).lower():
            version = str(item.get("value", ""))
    if "teams" in lowered and "memory" in lowered:
        return {"signature": "teams_memory", "version": version}
    if "token" in lowered or "vpn" in lowered:
        return {"signature": "vpn_stale_token", "version": version}
    if "disk" in lowered:
        return {"signature": "disk_pressure", "version": version}
    return {"signature": "unknown_cause", "version": version}


def _teams_mem(device: Any) -> float:
    for proc in device.processes:
        if proc.name == "Teams":
            return float(proc.mem_mb)
    return 0.0


def _teams_version(device: Any) -> str:
    for sw in device.software:
        if sw.app_id == "APP_TEAMS":
            return str(sw.version)
    return ""


def search_fleet_for_signature(estate: Any, signature: str,
                               version: str = "") -> list[dict[str, Any]]:
    """Scan every device. Returns [{device_id, match_state, detail}]. Read-only."""
    matches = []
    for device_id in sorted(estate.devices):
        device = estate.devices[device_id]
        state, detail = "", ""
        if signature == "teams_memory":
            mem = _teams_mem(device)
            if mem >= 3000:
                state, detail = AFFECTED, f"Teams {mem}MB"
            elif mem >= 1500:
                state, detail = EARLY, f"Teams {mem}MB rising"
            elif version and _teams_version(device) == version:
                state, detail = AT_RISK, f"Teams {version} without symptoms"
        elif signature == "vpn_stale_token":
            if not device.vpn_connected and "stale" in device.vpn_last_error:
                state, detail = AFFECTED, device.vpn_last_error
            elif not device.vpn_connected:
                state, detail = EARLY, device.vpn_last_error or "vpn down"
        elif signature == "disk_pressure":
            if device.disk_pct >= 80:
                state, detail = AFFECTED, f"disk {device.disk_pct}%"
            elif device.disk_pct >= 70:
                state, detail = EARLY, f"disk {device.disk_pct}%"
        if state:
            matches.append({"device_id": device_id, "match_state": state, "detail": detail})
    return matches


@dataclass
class FleetScan:
    signature: str
    scanned: int = 0
    matches: list[dict[str, Any]] = field(default_factory=list)
    auto: list[str] = field(default_factory=list)
    approval: list[str] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)

    @property
    def matching(self) -> int:
        return len(self.matches)


def classify_fleet(conn: sqlite3.Connection, estate: Any, case_id: str,
                   signature: str, action_id: str,
                   matches: list[dict[str, Any]]) -> FleetScan:
    """Per-device policy → buckets. Persists fleet_matches. Mutates nothing."""
    from control_plane.policy import DENY, PolicyInput, evaluate
    from control_plane import registry as script_registry

    action = script_registry.lookup_script(conn, action_id) or {}
    autonomy = str(action.get("autonomy_level", "L1"))
    scan = FleetScan(signature=signature, scanned=len(estate.devices), matches=matches)
    for match in matches:
        device = estate.get(match["device_id"])
        verdict = evaluate(conn, PolicyInput(
            user_id=device.user_id, device_id=device.device_id,
            device_group=device.device_group,
            device_compliant=device.compliance_state == "compliant",
            action_id=action_id)).decision
        if verdict == DENY or autonomy in ("L0", "L1"):
            bucket, policy = BLOCKED, "DENY"
        elif verdict == "ALLOW" and autonomy in ("L3", "L4") and match["match_state"] == AFFECTED:
            bucket, policy = AUTO, "ALLOW"
        else:
            bucket, policy = NEEDS_APPROVAL, verdict
        getattr(scan, {"auto_remediate": "auto", "approval_required": "approval",
                       "blocked": "blocked"}[bucket]).append(match["device_id"])
        match["bucket"] = bucket
        conn.execute(
            "INSERT OR REPLACE INTO fleet_matches(match_id, case_id, device_id, "
            "match_state, policy_decision) VALUES (?,?,?,?,?)",
            (f"FM-{case_id}-{match['device_id']}", case_id, match["device_id"],
             match["match_state"], policy))
    conn.commit()
    return scan


def scan_fleet(conn: sqlite3.Connection, estate: Any, case_id: str, root_cause: str,
               action_id: str, evidence: list[dict[str, Any]] | None = None) -> FleetScan:
    """Derive → search → classify. The M23 entry point."""
    derived = derive_failure_signature(root_cause, evidence)
    matches = search_fleet_for_signature(estate, derived["signature"], derived["version"])
    return classify_fleet(conn, estate, case_id, derived["signature"], action_id, matches)
