"""CMDB -> local asset inventory synchronisation through the ServiceNow adapter."""

from __future__ import annotations

import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.types import utcnow
from app.integrations.servicenow.base import ServiceNowClient
from app.integrations.servicenow.factory import get_servicenow_client
from app.models.enterprise import Asset, AssetDependency, BusinessService
from app.models.servicenow import ServiceNowSyncAttempt

CRITICALITY = {
    "1 - most critical": "critical",
    "2 - somewhat critical": "high",
    "3 - less critical": "medium",
    "4 - not critical": "low",
}
ENVIRONMENTS = {
    "production": "production",
    "prod": "production",
    "staging": "staging",
    "qa": "test",
    "test": "test",
    "development": "development",
    "dev": "development",
}
SERVER_FIELDS = [
    "sys_id",
    "asset_tag",
    "name",
    "fqdn",
    "ip_address",
    "os",
    "os_version",
    "environment",
    "busines_criticality",
    "owned_by.name",
    "support_group.name",
    "operational_status",
    "u_internet_facing",
    "location.name",
    "u_business_service",
    "u_defender_device_id",
    "sys_class_name",
    "u_cloud_provider",
]
SERVICE_FIELDS = ["sys_id", "name", "busines_criticality", "u_division", "owned_by.name", "short_description"]


def _bool(v: Any) -> bool | None:
    if v in (True, "true", "True", "1", 1):
        return True
    if v in (False, "false", "False", "0", 0):
        return False
    return None


def _asset_type(sys_class: str | None) -> str:
    return {
        "cmdb_ci_linux_server": "server",
        "cmdb_ci_win_server": "server",
        "cmdb_ci_vm_instance": "vm",
        "cmdb_ci_computer": "workstation",
        "cmdb_ci_docker_container": "container",
    }.get(sys_class or "", "server")


def sync_cmdb(db: Session, client: ServiceNowClient | None = None, actor: str = "system") -> dict[str, int]:
    client = client or get_servicenow_client()
    settings = get_settings()
    started = time.monotonic()
    stats = {"services": 0, "assets": 0, "dependencies": 0}
    try:
        services = client.query(settings.servicenow_service_table, "", SERVICE_FIELDS, 1000)
        servers = client.query(settings.servicenow_cmdb_table, "operational_status!=6", SERVER_FIELDS, 5000)
        rels = client.query("cmdb_rel_ci", "", ["sys_id", "parent", "child", "type"], 10000)
    except Exception as exc:
        db.add(
            ServiceNowSyncAttempt(
                operation="cmdb_sync",
                table_name=settings.servicenow_cmdb_table,
                outcome="error",
                error=str(exc)[:500],
                latency_ms=int((time.monotonic() - started) * 1000),
                actor=actor,
            )
        )
        raise
    now = utcnow()
    svc_by_sys: dict[str, BusinessService] = {}
    for row in services:
        svc = db.scalar(select(BusinessService).where(BusinessService.cmdb_sys_id == row["sys_id"]))
        if svc is None:
            svc = db.scalar(select(BusinessService).where(BusinessService.name == row["name"])) or BusinessService(
                name=row["name"]
            )
            db.add(svc)
        svc.cmdb_sys_id = row["sys_id"]
        svc.criticality = CRITICALITY.get(str(row.get("busines_criticality", "")).lower(), "medium")
        svc.division = row.get("u_division") or "Unassigned"
        svc.owner_team = row.get("owned_by.name")
        svc.description = row.get("short_description")
        svc.last_sync_at = now
        svc_by_sys[row["sys_id"]] = svc
        stats["services"] += 1
    db.flush()

    asset_by_sys: dict[str, Asset] = {}
    for row in servers:
        asset = db.scalar(select(Asset).where(Asset.cmdb_sys_id == row["sys_id"]))
        if asset is None:
            asset_id = row.get("asset_tag") or f"ASSET-{row['sys_id'][:8].upper()}"
            asset = db.get(Asset, asset_id) or Asset(id=asset_id, hostname=row.get("name") or asset_id, asset_type="server")
            db.add(asset)
        env = ENVIRONMENTS.get(str(row.get("environment") or "").lower())
        asset.hostname = (row.get("name") or asset.hostname).lower()
        asset.fqdn = (row.get("fqdn") or "").lower() or None
        asset.ip_address = row.get("ip_address") or None
        asset.operating_system = row.get("os") or None
        asset.os_version = row.get("os_version") or None
        asset.environment = env
        asset.business_criticality = CRITICALITY.get(str(row.get("busines_criticality") or "").lower())
        asset.owner = row.get("owned_by.name") or None
        asset.support_group = row.get("support_group.name") or None
        asset.operational_status = {"1": "operational", "2": "non-operational", "3": "repair", "6": "retired"}.get(
            str(row.get("operational_status")), str(row.get("operational_status") or "") or None
        )
        asset.internet_exposed = _bool(row.get("u_internet_facing"))
        asset.location = row.get("location.name") or None
        asset.defender_device_id = row.get("u_defender_device_id") or None
        asset.asset_type = _asset_type(row.get("sys_class_name"))
        asset.cloud_provider = row.get("u_cloud_provider") or None
        asset.cmdb_sys_id = row["sys_id"]
        svc = svc_by_sys.get(row.get("u_business_service") or "")
        asset.business_service_id = svc.id if svc else None
        asset.last_sync_at = now
        asset_by_sys[row["sys_id"]] = asset
        stats["assets"] += 1
    db.flush()

    for rel in rels:
        parent, child = asset_by_sys.get(rel.get("parent") or ""), asset_by_sys.get(rel.get("child") or "")
        if not parent or not child:
            continue
        dep_type = rel.get("type") or "Depends on::Used by"
        exists = db.scalar(
            select(AssetDependency).where(
                AssetDependency.source_asset_id == parent.id,
                AssetDependency.target_asset_id == child.id,
                AssetDependency.dependency_type == dep_type,
            )
        )
        if exists is None:
            db.add(
                AssetDependency(
                    source_asset_id=parent.id,
                    target_asset_id=child.id,
                    dependency_type=dep_type,
                    cmdb_rel_sys_id=rel.get("sys_id"),
                )
            )
        stats["dependencies"] += 1
    db.add(
        ServiceNowSyncAttempt(
            operation="cmdb_sync",
            table_name=settings.servicenow_cmdb_table,
            outcome="success",
            latency_ms=int((time.monotonic() - started) * 1000),
            actor=actor,
        )
    )
    db.flush()
    return stats
