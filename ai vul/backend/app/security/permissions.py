"""Role-based permissions, enforced server-side on every protected endpoint and tool."""

from __future__ import annotations

from enum import StrEnum

from app.models.enums import Role


class Permission(StrEnum):
    READ = "read"
    INVESTIGATE = "investigate"  # start/resume investigations, manual review decisions
    PLAN_EDIT = "plan:edit"
    APPROVAL_REQUEST = "approval:request"
    APPROVAL_DECIDE = "approval:decide"
    SERVICENOW_SYNC = "servicenow:sync"  # retry/refresh sync of already-approved records
    IMPORT_FINDINGS = "findings:import"
    VERIFY = "verification:submit"
    INTEGRATIONS_MANAGE = "integrations:manage"
    SIMULATION_CONTROL = "simulation:control"
    SETTINGS_MANAGE = "settings:manage"
    AUDIT_READ = "audit:read"
    EVALUATION_RUN = "evaluation:run"
    ASSISTANT = "assistant:use"


_ANALYST = {
    Permission.READ,
    Permission.INVESTIGATE,
    Permission.PLAN_EDIT,
    Permission.APPROVAL_REQUEST,
    Permission.SERVICENOW_SYNC,
    Permission.IMPORT_FINDINGS,
    Permission.VERIFY,
    Permission.SIMULATION_CONTROL,
    Permission.AUDIT_READ,
    Permission.EVALUATION_RUN,
    Permission.ASSISTANT,
}

ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    Role.ADMIN: frozenset(Permission),
    Role.ANALYST: frozenset(_ANALYST),
    Role.APPROVER: frozenset({Permission.READ, Permission.APPROVAL_DECIDE, Permission.AUDIT_READ, Permission.ASSISTANT}),
    Role.VIEWER: frozenset({Permission.READ}),
}


def has_permission(role: str, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, frozenset())


def permissions_for(role: str) -> list[str]:
    return sorted(p.value for p in ROLE_PERMISSIONS.get(role, frozenset()))
