"""Security & compliance advisor tools (M7): advisory ONLY.

These tools interpret posture and requirements. They NEVER authorize
execution — authorization belongs to the deterministic control plane (M12).
Every response carries the advisory-only disclaimer.
"""

from __future__ import annotations

from typing import Any

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.digital_workplace._ctx import get_bundle, resolve_ids

DISCLAIMER = ("advisory only — final authorization belongs to the "
              "deterministic control plane, never to an LLM")

# Static action tiers from the spec (governed registry lands in M13).
_ACTION_TIERS = {
    "diagnostics": {"risk": "NONE", "autonomy": "L4"},
    "SCR-018": {"risk": "LOW", "autonomy": "L3"},
    "SCR-INSTALL": {"risk": "MEDIUM", "autonomy": "L2"},
    "SCR-VPN": {"risk": "MEDIUM", "autonomy": "L2"},
    "SCR-FIREWALL": {"risk": "HIGH", "autonomy": "L1"},
    "SCR-DISABLE-PROTECTION": {"risk": "CRITICAL", "autonomy": "L0"},
}


class GetSecurityContext(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data)
        try:
            seed = int(args.get("seed", 42))
        except (TypeError, ValueError):
            seed = 42
        health = get_bundle(seed).endpoint.get_device_health(ids["device_id"])  # type: ignore[union-attr]
        return {"device_id": ids["device_id"], "compliant": health.compliant,
                "action_id": str(args.get("action_id", "")),
                "disclaimer": DISCLAIMER}


class CheckDeviceCompliance(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data)
        bundle = get_bundle(42)
        health = bundle.endpoint.get_device_health(ids["device_id"])  # type: ignore[union-attr]
        return {"device_id": ids["device_id"], "compliant": health.compliant,
                "compliance_state": ("compliant" if health.compliant
                                     else "non-compliant"),
                "disclaimer": DISCLAIMER}


class CheckComplianceRequirements(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        action_id = str(args.get("action_id", "diagnostics"))
        tier = _ACTION_TIERS.get(action_id, {"risk": "UNKNOWN", "autonomy": "L1"})
        return {"action_id": action_id, **tier,
                "requirements": ["corporate device", "authorized user",
                                 "compliant device", "approved script"],
                "disclaimer": DISCLAIMER}


class CheckPrivilegedActionRequirements(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        action_id = str(args.get("action_id", ""))
        tier = _ACTION_TIERS.get(action_id, {"risk": "UNKNOWN", "autonomy": "L1"})
        privileged = tier["autonomy"] in ("L0", "L1")
        return {"action_id": action_id, "privileged": privileged, **tier,
                "requires": ("DENY" if tier["autonomy"] == "L0"
                             else "human approval" if privileged
                             else "policy check"),
                "disclaimer": DISCLAIMER}
