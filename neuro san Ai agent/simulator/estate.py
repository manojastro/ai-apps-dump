"""Simulated enterprise estate (M5/M6): 500 aliased devices, seeded, deterministic.

Endpoint + software (M5) plus network/identity overlays (M6).
Demo hooks: apply_demo_scenario(estate, "laptop_teams_memory" | "vpn_stale_token").
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

ESTATE_SIZE = 500
BUGGY_TEAMS_VERSION = "3.8.4"
BUGGY_COHORT = 27  # DEVICE_001..DEVICE_027 (fleet demo: 27 matching)

_DEPARTMENTS = ("Engineering", "Finance", "HR", "Sales", "IT", "Support")
_OS_POOL = (["Windows 11"] * 80 + ["macOS 14"] * 15 + ["Ubuntu 22.04"] * 5)
_HEALTHY_TEAMS = ("3.7.5", "3.7.9", "3.7.2")
_BASE_APPS = (
    ("APP_CHROME", "Chrome", "126.0"),
    ("APP_OUTLOOK", "Outlook", "16.0"),
    ("APP_CODE", "VS Code", "1.90"),
    ("APP_DEFENDER", "Defender", "4.18"),
    ("APP_VPN", "VPN Client", "5.2"),
)


@dataclass
class EstateProcess:
    name: str
    mem_mb: float = 0.0
    cpu_pct: float = 0.0


@dataclass
class EstateSoftware:
    app_id: str
    name: str = ""
    version: str = ""
    healthy: bool = True


@dataclass
class EstateChange:
    change_id: str
    target: str = ""
    kind: str = ""
    at: str = ""
    summary: str = ""


@dataclass
class EstateSignin:
    event: str = "interactive"  # interactive | password_reset | mfa_challenge | vpn_auth
    at: str = ""
    result: str = "success"  # success | failed
    detail: str = ""


@dataclass
class EstateIdentity:
    user_id: str
    account_state: str = "active"
    mfa_ok: bool = True
    locked: bool = False
    last_signin: str = ""
    signins: list[EstateSignin] = field(default_factory=list)


@dataclass
class EstateDevice:
    device_id: str
    user_id: str = ""
    os: str = "Windows 11"
    department: str = "Engineering"
    device_group: str = "corporate-laptop"
    compliance_state: str = "compliant"
    cpu_pct: float = 20.0
    ram_pct: float = 40.0
    disk_pct: float = 50.0
    boot_secs: float = 40.0
    processes: list[EstateProcess] = field(default_factory=list)
    software: list[EstateSoftware] = field(default_factory=list)
    recent_changes: list[EstateChange] = field(default_factory=list)
    patch_history: list[EstateChange] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    # M6 network/identity overlays (defaults = healthy)
    net_latency_ms: float = 30.0
    net_loss_pct: float = 0.1
    dns_ok: bool = True
    proxy_ok: bool = True
    path_ok: bool = True
    vpn_connected: bool = True
    vpn_gateway: str = "vpn-east"
    vpn_last_error: str = ""


@dataclass
class Estate:
    devices: dict[str, EstateDevice] = field(default_factory=dict)
    users: dict[str, dict[str, str]] = field(default_factory=dict)
    identities: dict[str, EstateIdentity] = field(default_factory=dict)
    seed: int = 42

    def get(self, device_id: str) -> EstateDevice:
        try:
            return self.devices[device_id]
        except KeyError:
            raise LookupError(f"device {device_id} not found") from None

    def get_identity(self, user_id: str) -> EstateIdentity:
        try:
            return self.identities[user_id]
        except KeyError:
            raise LookupError(f"identity {user_id} not found") from None

    def devices_with_teams_version(self, version: str) -> list[EstateDevice]:
        out = []
        for device in self.devices.values():
            for sw in device.software:
                if sw.app_id == "APP_TEAMS" and sw.version == version:
                    out.append(device)
                    break
        return out


def _teams_memory_cohort(rng: random.Random, index: int) -> float:
    # Deterministic 4.2-4.9GB for the buggy cohort.
    return round(4200 + rng.random() * 700, 1)


def generate_estate(seed: int = 42, n: int = ESTATE_SIZE) -> Estate:
    """Build n aliased devices. Same seed → same estate."""
    rng = random.Random(seed)
    # Separate stream for M6 overlays so M5 telemetry draws never shift.
    overlay = random.Random((seed ^ 0x9E3779B9) & 0xFFFFFFFF)
    estate = Estate(seed=seed)
    for i in range(1, n + 1):
        device_id = f"DEVICE_{i:03d}"
        user_id = f"USER_{i:03d}"
        department = _DEPARTMENTS[(i - 1) % len(_DEPARTMENTS)]
        estate.users[user_id] = {"user_id": user_id, "department": department,
                                 "role": "employee"}
        buggy = i <= BUGGY_COHORT
        teams_version = BUGGY_TEAMS_VERSION if buggy else rng.choice(_HEALTHY_TEAMS)
        teams_mem = (_teams_memory_cohort(rng, i) if buggy
                     else round(300 + rng.random() * 600, 1))
        cpu = round(20 + rng.random() * 40, 1)
        ram = round(35 + rng.random() * 35, 1)
        if buggy:
            cpu = round(70 + rng.random() * 25, 1)
            ram = round(75 + rng.random() * 20, 1)
        device = EstateDevice(
            device_id=device_id, user_id=user_id,
            os=rng.choice(_OS_POOL), department=department,
            compliance_state="compliant" if rng.random() < 0.92 else "non-compliant",
            cpu_pct=cpu, ram_pct=ram,
            disk_pct=round(30 + rng.random() * 45, 1),
            boot_secs=round(25 + rng.random() * 45, 1),
            processes=[
                EstateProcess("Teams", teams_mem, round(15 + rng.random() * 30, 1)),
                EstateProcess("Chrome", round(400 + rng.random() * 800, 1),
                              round(2 + rng.random() * 10, 1)),
                EstateProcess("Outlook", round(200 + rng.random() * 300, 1),
                              round(1 + rng.random() * 5, 1)),
                EstateProcess("Code", round(300 + rng.random() * 500, 1),
                              round(1 + rng.random() * 8, 1)),
            ],
            software=[
                EstateSoftware("APP_TEAMS", "Teams", teams_version, not buggy),
                *[EstateSoftware(app_id, name, version, True)
                  for app_id, name, version in _BASE_APPS],
            ],
            recent_changes=(
                [EstateChange(f"CHG-{device_id}-1", "Teams", "update",
                              "2026-09-05T10:00:00+00:00",
                              "Teams updated 3.7.9 to 3.8.4")]
                if buggy else
                [EstateChange(f"CHG-{device_id}-1", "Chrome", "update",
                              "2026-08-28T10:00:00+00:00",
                              "Chrome updated to 126.0")]
            ),
            patch_history=[
                EstateChange(f"KB-{device_id}-1", "OS", "patch",
                             "2026-08-20T02:00:00+00:00", "Monthly OS patch OK"),
            ],
            issues=["teams_memory"] if buggy else [],
            net_latency_ms=round(18 + overlay.random() * 42, 1),
            net_loss_pct=round(overlay.random() * 0.4, 2),
            vpn_connected=overlay.random() >= 0.05,
            vpn_gateway=overlay.choice(("vpn-east", "vpn-west")),
            vpn_last_error="",
        )
        if not device.vpn_connected:
            device.vpn_last_error = overlay.choice(("auth timeout", "gateway unreachable"))
        if overlay.random() < 0.06:
            device.net_loss_pct = round(2 + overlay.random() * 6, 1)
            device.net_latency_ms = round(200 + overlay.random() * 400, 1)
        estate.devices[device_id] = device
        estate.identities[user_id] = EstateIdentity(
            user_id=user_id,
            mfa_ok=overlay.random() < 0.9,
            locked=overlay.random() < 0.02,
            last_signin="2026-09-06T08:00:00+00:00",
            signins=[
                EstateSignin("interactive", "2026-09-06T08:00:00+00:00", "success"),
                EstateSignin("mfa_challenge", "2026-09-06T08:00:00+00:00", "success"),
            ],
        )
    apply_demo_scenario(estate, "laptop_teams_memory")
    apply_demo_scenario(estate, "vpn_stale_token")
    return estate


def apply_demo_scenario(estate: Estate, name: str) -> str:
    """Pin a demo device to exact evidence values. Returns device_id."""
    if name == "vpn_stale_token":
        return _apply_vpn_stale_token(estate)
    if name != "laptop_teams_memory":
        raise ValueError(f"unknown scenario: {name}")
    device = estate.get("DEVICE_001")
    device.cpu_pct = 94.0
    device.ram_pct = 91.0
    device.disk_pct = 42.0
    for proc in device.processes:
        if proc.name == "Teams":
            proc.mem_mb = 4812.8  # 4.7GB
            proc.cpu_pct = 38.0
    for sw in device.software:
        if sw.app_id == "APP_TEAMS":
            sw.version = BUGGY_TEAMS_VERSION
            sw.healthy = False
    if "teams_memory" not in device.issues:
        device.issues.append("teams_memory")
    return device.device_id


def _apply_vpn_stale_token(estate: Estate) -> str:
    """Demo 2: password changed OK, identity healthy, VPN token stale."""
    device = estate.get("DEVICE_002")
    device.net_latency_ms = 35.0
    device.net_loss_pct = 0.1
    device.dns_ok = True
    device.proxy_ok = True
    device.path_ok = True
    device.vpn_connected = False
    device.vpn_gateway = "vpn-east"
    device.vpn_last_error = "stale cached token after password change"
    if "vpn_stale_token" not in device.issues:
        device.issues.append("vpn_stale_token")
    identity = estate.get_identity(device.user_id)
    identity.account_state = "active"
    identity.mfa_ok = True
    identity.locked = False
    identity.last_signin = "2026-09-06T08:55:00+00:00"
    identity.signins = [
        EstateSignin("password_reset", "2026-09-06T08:50:00+00:00",
                     "success", "password changed successfully"),
        EstateSignin("interactive", "2026-09-06T08:55:00+00:00", "success"),
        EstateSignin("mfa_challenge", "2026-09-06T08:55:00+00:00", "success"),
        EstateSignin("vpn_auth", "2026-09-06T08:56:00+00:00", "failed",
                     "stale cached token"),
    ]
    return device.device_id
