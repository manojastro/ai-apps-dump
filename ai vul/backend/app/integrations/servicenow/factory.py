from __future__ import annotations

from app.core.config import get_settings
from app.integrations.servicenow.base import ServiceNowClient
from app.integrations.servicenow.mock import MockServiceNowClient

# Field-name mapping for the CMDB -> asset synchronisation (configurable per instance).
CMDB_FIELD_MAP = {
    "hostname": "name",
    "fqdn": "fqdn",
    "ip_address": "ip_address",
    "operating_system": "os",
    "os_version": "os_version",
    "environment": "environment",
    "business_criticality": "busines_criticality",  # sic: ServiceNow's field name
    "owner": "owned_by",
    "support_group": "support_group",
    "operational_status": "operational_status",
    "internet_exposed": "u_internet_facing",
    "location": "location",
    "business_service": "u_business_service",
    "defender_device_id": "u_defender_device_id",
    "asset_type": "sys_class_name",
    "cloud_provider": "u_cloud_provider",
}


def get_servicenow_client() -> ServiceNowClient:
    settings = get_settings()
    if settings.servicenow_mode == "real":
        from app.integrations.servicenow.rest import RestServiceNowClient

        return RestServiceNowClient(settings)
    return MockServiceNowClient()


def remediation_table() -> str | None:
    s = get_settings()
    if s.servicenow_remediation_table:
        return s.servicenow_remediation_table
    return "change_task" if s.servicenow_mode == "mock" else None


def write_allowlist() -> set[str]:
    s = get_settings()
    tables = {s.servicenow_change_table}
    if rt := remediation_table():
        tables.add(rt)
    return tables
