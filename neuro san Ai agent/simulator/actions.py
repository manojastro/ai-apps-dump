"""Simulated endpoint actions (M16): deterministic state transitions.

Owns WHAT changes on a device for an approved action_id. Whether an action
MAY run is the execution controller's job (control_plane/execution.py) —
this module never checks policy. Params arrive as plain dicts (parsed JSON).
"""

from __future__ import annotations

import json
from typing import Any

from simulator.estate import Estate, EstateChange, EstateSoftware


def _note(device, text: str) -> None:
    device.recent_changes.append(EstateChange(
        f"CHG-{device.device_id}-EX", "remediation", "action",
        "2026-09-07T12:00:00+00:00", text))


def apply_effect(estate: Estate, action_id: str, device_id: str,
                 params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Mutate one device per the approved action. Returns a summary.

    Raises LookupError (unknown device) or ValueError (unknown action).
    """
    params = params or {}
    device = estate.get(device_id)
    if action_id == "SCR-018":
        for proc in device.processes:
            if proc.name == "Teams":
                proc.mem_mb = 640.0
                proc.cpu_pct = 4.0
        device.cpu_pct = 22.0
        device.ram_pct = 54.0
        for sw in device.software:
            if sw.app_id == "APP_TEAMS":
                sw.healthy = True
        if "teams_memory" in device.issues:
            device.issues.remove("teams_memory")
        _note(device, "SCR-018 Clear Teams Cache executed")
        return {"cpu_pct": 22.0, "ram_pct": 54.0, "teams_mb": 640.0}
    if action_id == "SCR-VPN-RECONNECT":
        device.vpn_connected = True
        device.vpn_last_error = ""
        if "vpn_stale_token" in device.issues:
            device.issues.remove("vpn_stale_token")
        _note(device, "SCR-VPN-RECONNECT executed, token refreshed")
        return {"vpn_connected": True}
    if action_id == "SCR-DISK-CLEANUP":
        device.disk_pct = 48.0
        _note(device, "SCR-DISK-CLEANUP executed")
        return {"disk_pct": 48.0}
    if action_id == "SCR-CLEAR-TEMP":
        device.cpu_pct = max(15.0, round(device.cpu_pct - 10.0, 1))
        device.ram_pct = max(30.0, round(device.ram_pct - 8.0, 1))
        _note(device, "SCR-CLEAR-TEMP executed")
        return {"cpu_pct": device.cpu_pct, "ram_pct": device.ram_pct}
    if action_id == "SCR-RESTART-APP":
        app = str(params.get("app", ""))
        if not app:
            raise ValueError("SCR-RESTART-APP requires params.app")
        for proc in device.processes:
            if proc.name.lower() == app.lower():
                proc.mem_mb = 450.0
                proc.cpu_pct = 3.0
                _note(device, f"SCR-RESTART-APP restarted {proc.name}")
                return {"app": proc.name, "mem_mb": 450.0}
        raise ValueError(f"app {app} not running on {device_id}")
    if action_id == "SCR-INSTALL":
        app = str(params.get("app", ""))
        if not app:
            raise ValueError("SCR-INSTALL requires params.app")
        if all(s.name.lower() != app.lower() for s in device.software):
            device.software.append(EstateSoftware(f"APP-{app.upper()}", app, "1.0", True))
        _note(device, f"SCR-INSTALL installed {app}")
        return {"app": app, "installed": True}
    raise ValueError(f"no simulated effect for {action_id}")


def snapshot(device_id: str, estate: Estate) -> str:
    """Compact before/after state for remediation_runs + verification (M17)."""
    device = estate.get(device_id)
    teams = next((p.mem_mb for p in device.processes if p.name == "Teams"), 0.0)
    return json.dumps({"cpu_pct": device.cpu_pct, "ram_pct": device.ram_pct,
                       "disk_pct": device.disk_pct, "teams_mb": teams,
                       "vpn_connected": device.vpn_connected,
                       "issues": sorted(device.issues)})
