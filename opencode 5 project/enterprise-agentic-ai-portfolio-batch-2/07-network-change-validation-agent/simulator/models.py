"""Normalized network twin data structures shared by simulator and engine."""
from __future__ import annotations

import ipaddress
from typing import Any, Literal

from pydantic import BaseModel, Field

Role = Literal["core", "distribution", "access", "firewall", "wan", "host", "server", "jump"]


class OspfConfig(BaseModel):
    enabled: bool = True
    area: int = 0
    cost: int = 10


class Interface(BaseModel):
    device: str
    name: str
    cidr: str | None = None
    mtu: int = 1500
    enabled: bool = True
    vlan: int | None = None
    ospf: OspfConfig = Field(default_factory=OspfConfig)
    acl_in: str | None = None
    acl_out: str | None = None
    description: str = ""


class Device(BaseModel):
    name: str
    role: Role
    zone: str
    vendor: str = "cisco-ios-flavor"
    enabled: bool = True
    default_gateway: str | None = None
    firewall: bool = False


class Vlan(BaseModel):
    id: int
    name: str
    subnet: str | None = None


class SubnetDef(BaseModel):
    cidr: str
    vlan_id: int | None = None
    zone: str
    label: str = ""


class AclRule(BaseModel):
    seq: int
    action: Literal["permit", "deny"]
    proto: Literal["ip", "tcp", "udp", "icmp"] = "ip"
    src: str = "any"
    dst: str = "any"
    dst_port: int | None = None
    note: str = ""


class Acl(BaseModel):
    name: str
    rules: list[AclRule] = Field(default_factory=list)


class StaticRoute(BaseModel):
    device: str
    prefix: str
    next_hop: str
    distance: int = 1


class BgpNeighbor(BaseModel):
    ip: str
    remote_as: int
    advertised_prefixes: list[str] = Field(default_factory=list)


class BgpProcess(BaseModel):
    device: str
    local_as: int
    neighbors: list[BgpNeighbor] = Field(default_factory=list)


class FirewallRule(BaseModel):
    seq: int
    action: Literal["permit", "deny"]
    src: str = "any"
    dst: str = "any"
    proto: Literal["ip", "tcp", "udp", "icmp"] = "ip"
    dst_port: int | None = None
    label: str = ""


class FirewallDef(BaseModel):
    device: str
    default_action: Literal["permit", "deny"] = "deny"
    rules: list[FirewallRule] = Field(default_factory=list)


class ServiceDef(BaseModel):
    name: str
    endpoint_ip: str
    port: int
    proto: Literal["tcp", "udp"] = "tcp"
    critical: bool = True
    enabled: bool = True


class TwinPayload(BaseModel):
    name: str = "lab"
    devices: list[Device] = Field(default_factory=list)
    interfaces: list[Interface] = Field(default_factory=list)
    vlans: list[Vlan] = Field(default_factory=list)
    subnets: list[SubnetDef] = Field(default_factory=list)
    acls: list[Acl] = Field(default_factory=list)
    static_routes: list[StaticRoute] = Field(default_factory=list)
    bgp_processes: list[BgpProcess] = Field(default_factory=list)
    firewalls: list[FirewallDef] = Field(default_factory=list)
    services: list[ServiceDef] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "TwinPayload":
        return cls.model_validate(raw)


def ip_in_subnet(ip: str, cidr: str) -> bool:
    try:
        return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        return False


def prefix_len(cidr: str) -> int:
    return ipaddress.ip_network(cidr, strict=False).prefixlen


def norm_cidr(cidr: str) -> str:
    return str(ipaddress.ip_network(cidr, strict=False))


def cidr_contains(outer: str, inner_cidr: str) -> bool:
    return ipaddress.ip_network(inner_cidr, strict=False).subnet_of(
        ipaddress.ip_network(outer, strict=False)
    )


def cidrs_equal(a: str, b: str) -> bool:
    return ipaddress.ip_network(a, strict=False) == ipaddress.ip_network(b, strict=False)


def cidr_overlap(a: str, b: str) -> bool:
    na = ipaddress.ip_network(a, strict=False)
    nb = ipaddress.ip_network(b, strict=False)
    return na.overlaps(nb)
