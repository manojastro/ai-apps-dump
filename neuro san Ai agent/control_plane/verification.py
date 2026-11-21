"""Verification controller (M17): fresh telemetry decides resolved or not.

Reads post-remediation state through TWO independent mock providers
(Nexthink health + Tanium processes, etc.) — never trusts the execution
return value. Postconditions per action_id; every check names before/after.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

# action_id -> [(check name, predicate on fresh state, human description)]
# Predicates receive the captured state dict; see capture_state below.
POSTCONDITIONS: dict[str, list[tuple[str, str]]] = {
    "SCR-018": [("cpu_recovered", "cpu_ok"), ("ram_recovered", "ram_ok"),
                ("teams_healthy", "teams_ok")],
    "SCR-VPN-RECONNECT": [("vpn_up", "vpn_ok")],
    "SCR-DISK-CLEANUP": [("disk_recovered", "disk_ok")],
    "SCR-CLEAR-TEMP": [("cpu_recovered", "cpu_ok"), ("ram_recovered", "ram_ok")],
    "SCR-RESTART-APP": [("app_healthy", "teams_ok")],
    "SCR-INSTALL": [("app_present", "app_ok")],
}


def capture_state(estate: Any, device_id: str, action_id: str = "") -> dict[str, Any]:
    """Fresh multi-source telemetry AFTER remediation (or before, same shape)."""
    from simulator.cloudflare import MockCloudflareProvider
    from simulator.intune import MockIntuneProvider
    from simulator.nexthink import MockNexthinkProvider
    from simulator.tanium import MockTaniumProvider
    from simulator.zscaler import MockZscalerProvider

    nexthink = MockNexthinkProvider(estate).get_device_health(device_id)
    tanium_procs = MockTaniumProvider(estate).get_processes(device_id)
    health = {"cpu_pct": nexthink.cpu_pct, "ram_pct": nexthink.ram_pct,
              "disk_pct": nexthink.disk_pct, "compliant": nexthink.compliant,
              "source": "nexthink"}
    teams = next(({"mem_mb": p.mem_mb, "cpu_pct": p.cpu_pct}
                  for p in tanium_procs if p.name == "Teams"), None)
    state: dict[str, Any] = {"health": health, "teams": teams,
                             "tanium_source": "tanium", "action_id": action_id}
    if action_id in ("SCR-VPN-RECONNECT",):
        vpn = MockZscalerProvider(estate).get_vpn_state(device_id)
        state["vpn"] = {"connected": vpn.connected, "last_error": vpn.last_error}
    if action_id in ("SCR-VPN-RECONNECT", "SCR-DISK-CLEANUP", "SCR-018"):
        net = MockCloudflareProvider(estate).get_network_health(device_id)
        state["network"] = {"loss_pct": net.loss_pct, "dns_ok": net.dns_ok}
    if action_id in ("SCR-INSTALL", "SCR-018"):
        inventory = MockIntuneProvider(estate).get_inventory(device_id)
        state["apps"] = [{"app_id": s.app_id, "healthy": s.healthy} for s in inventory]
    return state


def _eval_predicate(name: str, state: dict[str, Any],
                    params: dict[str, Any] | None = None) -> tuple[bool, str]:
    health = state.get("health", {})
    if name == "cpu_ok":
        ok = float(health.get("cpu_pct", 100)) < 80
        return ok, f"cpu {health.get('cpu_pct')}%"
    if name == "ram_ok":
        ok = float(health.get("ram_pct", 100)) < 80
        return ok, f"ram {health.get('ram_pct')}%"
    if name == "disk_ok":
        ok = float(health.get("disk_pct", 100)) < 80
        return ok, f"disk {health.get('disk_pct')}%"
    if name == "teams_ok":
        teams = state.get("teams") or {}
        ok = bool(teams) and float(teams.get("mem_mb", 10 ** 9)) < 1000
        return ok, f"teams {teams.get('mem_mb', '?')}MB"
    if name == "vpn_ok":
        vpn = state.get("vpn") or {}
        ok = bool(vpn.get("connected", False))
        return ok, f"vpn connected={vpn.get('connected')}"
    if name == "app_ok":
        apps = state.get("apps", [])
        wanted = (params or {}).get("app", "")
        if wanted:
            found = [a for a in apps if str(a.get("app_id", "")).lower() == f"app-{wanted}".lower()
                     or str(a.get("app_id", "")).lower() == wanted.lower()]
            ok = bool(found) and all(a.get("healthy", False) for a in found)
            return ok, f"app {wanted} present={bool(found)}"
        ok = bool(apps)
        return ok, f"{len(apps)} apps inventoried"
    return False, f"unknown predicate {name}"


@dataclass
class VerificationResult:
    passed: bool
    checks: list[dict[str, Any]] = field(default_factory=list)

    @property
    def failed(self) -> list[str]:
        return [c["check"] for c in self.checks if not c["passed"]]


def verify_remediation(before: dict[str, Any], after: dict[str, Any],
                       action_id: str,
                       params: dict[str, Any] | None = None) -> VerificationResult:
    """Evaluate postconditions on AFTER state; report before/after per check."""
    result = VerificationResult(passed=False)
    for check_name, predicate in POSTCONDITIONS.get(action_id, []):
        passed, detail = _eval_predicate(predicate, after, params)
        before_detail = _eval_predicate(predicate, before, params)[1] if before else "n/a"
        result.checks.append({"check": check_name, "passed": passed,
                              "before": before_detail, "after": detail})
    result.passed = bool(result.checks) and all(c["passed"] for c in result.checks)
    return result


def verification_json(result: VerificationResult) -> str:
    return json.dumps({"passed": result.passed, "checks": result.checks})
