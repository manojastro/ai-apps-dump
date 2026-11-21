"""Observe coded tools (M7): endpoint / software / network / identity queries.

Thin CodedTool wrappers over the shared-estate mocks. Read-only, deterministic
(seed defaults to 42), aliased ids only. Every method returns plain dicts.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.digital_workplace._ctx import get_bundle, resolve_ids
from simulator.cloudflare import MockCloudflareProvider
from simulator.tanium import MockTaniumProvider


def _seed(args: dict[str, Any]) -> int:
    try:
        return int(args.get("seed", 42))
    except (TypeError, ValueError):
        return 42


# ------------------------------------------------------------- endpoint

class QueryDeviceHealth(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data)
        health = get_bundle(_seed(args)).endpoint.get_device_health(ids["device_id"])  # type: ignore[union-attr]
        return asdict(health)


class QueryNexthink(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data)
        bundle = get_bundle(_seed(args))
        health = bundle.endpoint.get_device_health(ids["device_id"])  # type: ignore[union-attr]
        return {"source": "nexthink", **asdict(health)}


class QueryTanium(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data)
        tanium = MockTaniumProvider(get_bundle(_seed(args)).estate)
        health = tanium.get_device_health(ids["device_id"])
        return {"source": "tanium", **asdict(health)}


class QueryProcesses(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data)
        bundle = get_bundle(_seed(args))
        procs = bundle.endpoint.get_processes(ids["device_id"])  # type: ignore[union-attr]
        return {"device_id": ids["device_id"],
                "processes": [asdict(p) for p in procs]}


class QueryDiskHealth(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data)
        health = get_bundle(_seed(args)).endpoint.get_device_health(ids["device_id"])  # type: ignore[union-attr]
        status = ("critical" if health.disk_pct >= 90 else
                  "warning" if health.disk_pct >= 80 else "healthy")
        return {"device_id": ids["device_id"], "disk_pct": health.disk_pct,
                "status": status, "source": "nexthink"}


class QueryEndpointEvents(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data)
        bundle = get_bundle(_seed(args))
        changes = bundle.endpoint.get_recent_changes(ids["device_id"])  # type: ignore[union-attr]
        return {"device_id": ids["device_id"],
                "events": [asdict(c) for c in changes]}


# ------------------------------------------------------------- software

class QueryIntune(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data)
        bundle = get_bundle(_seed(args))
        inventory = bundle.software.get_inventory(ids["device_id"])  # type: ignore[union-attr]
        unhealthy = [asdict(s) for s in inventory if not s.healthy]
        return {"device_id": ids["device_id"], "source": "intune",
                "app_count": len(inventory), "unhealthy": unhealthy,
                "apps": [asdict(s) for s in inventory]}


class QuerySoftwareInventory(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data)
        bundle = get_bundle(_seed(args))
        inventory = bundle.software.get_inventory(ids["device_id"])  # type: ignore[union-attr]
        return {"device_id": ids["device_id"],
                "inventory": [asdict(s) for s in inventory]}


class QuerySoftwareCatalog(CodedTool):
    """Static approved-request catalog (governed registry lands in M13)."""

    CATALOG = (
        {"app_id": "APP_CODE", "name": "VS Code", "requestable": True},
        {"app_id": "APP_CHROME", "name": "Chrome", "requestable": True},
        {"app_id": "APP_TEAMS", "name": "Teams", "requestable": True},
        {"app_id": "APP_SAP", "name": "SAP GUI", "requestable": True},
    )

    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        query = str(args.get("query", "")).lower()
        items = [c for c in self.CATALOG if not query or query in c["name"].lower()]
        return {"source": "static-catalog", "items": items}


class QueryRecentChanges(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data)
        bundle = get_bundle(_seed(args))
        changes = bundle.software.get_recent_changes(ids["device_id"])  # type: ignore[union-attr]
        return {"device_id": ids["device_id"],
                "changes": [asdict(c) for c in changes]}


class QueryPatchHistory(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data)
        bundle = get_bundle(_seed(args))
        patches = bundle.software.get_patch_history(ids["device_id"])  # type: ignore[union-attr]
        return {"device_id": ids["device_id"],
                "patches": [asdict(p) for p in patches]}


# ------------------------------------------------------------- network

class QueryNetwork(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data)
        health = get_bundle(_seed(args)).network.get_network_health(ids["device_id"])  # type: ignore[union-attr]
        return asdict(health)


class QueryZscaler(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data)
        bundle = get_bundle(_seed(args))
        health = bundle.network.get_network_health(ids["device_id"])  # type: ignore[union-attr]
        vpn = bundle.network.get_vpn_state(ids["device_id"])  # type: ignore[union-attr]
        return {"source": "zscaler", "health": asdict(health), "vpn": asdict(vpn)}


class QueryCloudflare(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data)
        cloudflare = MockCloudflareProvider(get_bundle(_seed(args)).estate)
        health = cloudflare.get_network_health(ids["device_id"])
        return {"source": "cloudflare", **asdict(health)}


class QueryDns(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data)
        health = get_bundle(_seed(args)).network.get_network_health(ids["device_id"])  # type: ignore[union-attr]
        return {"device_id": ids["device_id"], "dns_ok": health.dns_ok,
                "source": "cloudflare"}


class QueryVpnState(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data)
        vpn = get_bundle(_seed(args)).network.get_vpn_state(ids["device_id"])  # type: ignore[union-attr]
        return asdict(vpn)


class QueryNetworkPath(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data)
        health = get_bundle(_seed(args)).network.get_network_health(ids["device_id"])  # type: ignore[union-attr]
        return {"device_id": ids["device_id"], "path_ok": health.path_ok,
                "latency_ms": health.latency_ms, "loss_pct": health.loss_pct,
                "source": "cloudflare"}


# ------------------------------------------------------------- identity

class QueryEntra(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data, need=("user_id",))
        identity = get_bundle(_seed(args)).identity.get_identity(ids["user_id"])  # type: ignore[union-attr]
        return asdict(identity)


class QuerySigninHistory(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data, need=("user_id",))
        try:
            limit = int(args.get("limit", 10))
        except (TypeError, ValueError):
            limit = 10
        history = get_bundle(_seed(args)).identity.get_signin_history(ids["user_id"], limit)  # type: ignore[union-attr]
        return {"user_id": ids["user_id"], "signins": history}


class QueryAccountState(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data, need=("user_id",))
        identity = get_bundle(_seed(args)).identity.get_identity(ids["user_id"])  # type: ignore[union-attr]
        return {"user_id": ids["user_id"], "account_state": identity.account_state,
                "locked": identity.locked, "source": "entra"}


class QueryMfaState(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data, need=("user_id",))
        identity = get_bundle(_seed(args)).identity.get_identity(ids["user_id"])  # type: ignore[union-attr]
        return {"user_id": ids["user_id"], "mfa_ok": identity.mfa_ok,
                "source": "entra"}


class QueryAccessState(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        ids = resolve_ids(args, sly_data, need=("user_id",))
        identity = get_bundle(_seed(args)).identity.get_identity(ids["user_id"])  # type: ignore[union-attr]
        granted = (identity.account_state == "active" and not identity.locked
                   and identity.mfa_ok)
        return {"user_id": ids["user_id"],
                "access": "granted" if granted else "denied",
                "account_state": identity.account_state, "mfa_ok": identity.mfa_ok,
                "locked": identity.locked, "source": "entra"}
