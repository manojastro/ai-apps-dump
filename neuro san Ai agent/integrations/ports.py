"""Provider ports (M4): adapter interfaces behind which real and mock
enterprise systems hide. Agents/coded tools depend ONLY on these.

No simulation logic here. No credentials here (transports own auth).
All IDs are aliases (USER_*/DEVICE_*) — see D006.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


# ---------------------------------------------------------------- DTOs

@dataclass(frozen=True)
class DeviceHealth:
    device_id: str
    cpu_pct: float = 0.0
    ram_pct: float = 0.0
    disk_pct: float = 0.0
    boot_secs: float = 0.0
    compliant: bool = True
    summary: str = ""


@dataclass(frozen=True)
class ProcessEntry:
    name: str
    mem_mb: float = 0.0
    cpu_pct: float = 0.0


@dataclass(frozen=True)
class SoftwareItem:
    app_id: str
    name: str = ""
    version: str = ""
    healthy: bool = True


@dataclass(frozen=True)
class ChangeEntry:
    change_id: str
    target: str = ""
    kind: str = ""
    at: str = ""
    summary: str = ""


@dataclass(frozen=True)
class NetworkHealth:
    device_id: str
    latency_ms: float = 0.0
    loss_pct: float = 0.0
    dns_ok: bool = True
    proxy_ok: bool = True
    path_ok: bool = True
    summary: str = ""


@dataclass(frozen=True)
class VPNState:
    device_id: str
    connected: bool = True
    gateway: str = ""
    last_error: str = ""


@dataclass(frozen=True)
class IdentityState:
    user_id: str
    account_state: str = "active"
    mfa_ok: bool = True
    locked: bool = False
    last_signin: str = ""


@dataclass(frozen=True)
class ActionRequest:
    action_id: str  # approved script id, e.g. SCR-018 (never raw shell)
    device_id: str = ""
    params: str = "{}"


@dataclass(frozen=True)
class ActionResult:
    ok: bool
    output: str = ""
    changed: bool = False


@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    before: str = "{}"
    after: str = "{}"
    failed_postconditions: str = "[]"


@dataclass(frozen=True)
class IncidentDTO:
    sys_id: str = ""
    number: str = ""
    state: str = ""
    short_description: str = ""
    extra: str = "{}"


@dataclass(frozen=True)
class ProblemDTO:
    sys_id: str = ""
    number: str = ""
    state: str = ""
    short_description: str = ""
    extra: str = "{}"


# ---------------------------------------------------------------- Ports

@runtime_checkable
class EndpointProvider(Protocol):
    source: str
    def get_device_health(self, device_id: str) -> DeviceHealth: ...
    def get_processes(self, device_id: str) -> list[ProcessEntry]: ...
    def get_recent_changes(self, device_id: str) -> list[ChangeEntry]: ...


@runtime_checkable
class SoftwareProvider(Protocol):
    source: str
    def get_inventory(self, device_id: str) -> list[SoftwareItem]: ...
    def get_recent_changes(self, device_id: str) -> list[ChangeEntry]: ...
    def get_patch_history(self, device_id: str) -> list[ChangeEntry]: ...


@runtime_checkable
class NetworkProvider(Protocol):
    source: str
    def get_network_health(self, device_id: str) -> NetworkHealth: ...
    def get_vpn_state(self, device_id: str) -> VPNState: ...


@runtime_checkable
class IdentityProvider(Protocol):
    source: str
    def get_identity(self, user_id: str) -> IdentityState: ...
    def get_signin_history(self, user_id: str,
                           limit: int = 10) -> list[dict[str, Any]]: ...


@runtime_checkable
class ITSMProvider(Protocol):
    source: str
    def create_incident(self, short_description: str, description: str = ...,
                        caller_id: str = ...) -> IncidentDTO: ...
    def get_incident(self, sys_id: str) -> IncidentDTO: ...
    def search_incidents(self, query: str, limit: int = ...) -> list[IncidentDTO]: ...
    def update_incident(self, sys_id: str, fields: dict[str, Any]) -> IncidentDTO: ...
    def add_work_note(self, sys_id: str, note: str) -> IncidentDTO: ...
    def resolve_incident(self, sys_id: str, close_notes: str) -> IncidentDTO: ...
    def escalate_incident(self, sys_id: str, note: str) -> IncidentDTO: ...
    def create_problem(self, short_description: str, description: str = ...) -> ProblemDTO: ...
    def link_incident_to_problem(self, incident_sys_id: str, problem_sys_id: str) -> IncidentDTO: ...


@runtime_checkable
class RemoteExecutor(Protocol):
    source: str
    def execute_action(self, request: ActionRequest) -> ActionResult: ...
    def verify_action(self, request: ActionRequest, before: str = ...,
                      after: str = ...) -> VerificationResult: ...


@dataclass
class Providers:
    """One bundle per request/case. Mock-first when live creds absent (M4).

    estate holds the shared mock Estate when mocks are wired (M5+);
    typed Any so ports stay dependency-free (no mock-layer import here).
    """
    endpoint: EndpointProvider | None = None
    software: SoftwareProvider | None = None
    network: NetworkProvider | None = None
    identity: IdentityProvider | None = None
    itsm: ITSMProvider | None = None
    executor: RemoteExecutor | None = None
    notes: str = field(default="")
    estate: Any = None
