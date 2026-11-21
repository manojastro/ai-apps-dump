"""Deterministic seeded lab topology for the network digital twin."""
from __future__ import annotations

from simulator.models import (
    Acl,
    AclRule,
    BgpNeighbor,
    BgpProcess,
    Device,
    FirewallDef,
    FirewallRule,
    Interface,
    OspfConfig,
    ServiceDef,
    StaticRoute,
    SubnetDef,
    TwinPayload,
    Vlan,
)


def build_lab_twin() -> TwinPayload:
    devices = [
        Device(name="core-01", role="core", zone="transit"),
        Device(name="dist-01", role="distribution", zone="transit"),
        Device(name="dist-02", role="distribution", zone="transit"),
        Device(name="access-fin-01", role="access", zone="finance"),
        Device(name="access-dev-01", role="access", zone="dev"),
        Device(name="fw-01", role="firewall", zone="prod-edge", firewall=True),
        Device(name="wan-edge-01", role="wan", zone="wan"),
        Device(name="wan-edge-02", role="wan", zone="wan"),
        Device(name="mgmt-jump-01", role="jump", zone="mgmt", default_gateway="10.99.0.1"),
        Device(name="dns-01", role="server", zone="mgmt", default_gateway="10.99.0.1"),
        Device(name="fin-app-01", role="server", zone="finance", default_gateway="10.40.10.1"),
        Device(name="dev-vm-01", role="server", zone="dev", default_gateway="10.50.20.1"),
        Device(name="app-01", role="server", zone="prod-app", default_gateway="10.30.0.1"),
        Device(name="db-01", role="server", zone="prod-db", default_gateway="10.30.1.1"),
        Device(name="branch-pc", role="host", zone="branch", vendor="generic-endpoint",
               default_gateway="10.80.0.1"),
    ]

    def ifc(device: str, name: str, cidr: str | None, *, mtu: int = 1500, vlan: int | None = None,
            ospf: bool = True, cost: int = 10, acl_in: str | None = None,
            acl_out: str | None = None, enabled: bool = True) -> Interface:
        return Interface(device=device, name=name, cidr=cidr, mtu=mtu, vlan=vlan,
                         ospf=OspfConfig(enabled=ospf, area=0, cost=cost),
                         acl_in=acl_in, acl_out=acl_out, enabled=enabled)

    interfaces = [
        ifc("core-01", "Vlan10", "10.99.0.1/24", vlan=10, acl_out="PROTECT-MGMT"),
        ifc("core-01", "Ethernet1/1", "10.200.0.1/30", cost=10),
        ifc("core-01", "Ethernet1/2", "10.200.0.5/30", cost=10),
        ifc("core-01", "Ethernet1/3", "10.200.2.2/30", cost=10),
        ifc("core-01", "Ethernet1/4", "10.200.3.6/30", cost=10),
        ifc("core-01", "Ethernet1/9", "10.200.9.2/30", cost=10),
        ifc("dist-01", "Ethernet1/1", "10.200.0.2/30", cost=10),
        ifc("dist-01", "Ethernet1/2", "10.200.1.1/24", cost=10),
        ifc("dist-01", "Ethernet1/3", "10.200.4.2/30", cost=5),
        ifc("dist-02", "Ethernet1/1", "10.200.0.6/30", cost=10),
        ifc("dist-02", "Ethernet1/2", "10.200.5.1/24", cost=10),
        ifc("dist-02", "Ethernet1/3", "10.200.4.1/30", cost=5),
        ifc("access-fin-01", "Vlan110", "10.40.10.1/24", vlan=110, acl_out="SEG-ISOLATE-FIN"),
        ifc("access-fin-01", "Ethernet1/1", "10.200.1.55/24", cost=10),
        ifc("access-dev-01", "Vlan120", "10.50.20.1/24", vlan=120, acl_out="SEG-ISOLATE-DEV"),
        ifc("access-dev-01", "Ethernet1/1", "10.200.5.66/24", cost=10),
        ifc("fw-01", "Vlan210", "10.30.0.1/24", vlan=210),
        ifc("fw-01", "Vlan220", "10.30.1.1/24", vlan=220),
        ifc("fw-01", "Ethernet1/9", "10.200.9.1/30", cost=10),
        ifc("wan-edge-01", "Ethernet1/1", "10.200.2.1/30", cost=10),
        ifc("wan-edge-01", "Ethernet1/2", "10.80.0.1/24", ospf=False),
        ifc("wan-edge-01", "Ethernet1/3", None, ospf=False, enabled=False),
        ifc("wan-edge-02", "Ethernet1/1", "10.200.3.5/30", cost=10),
        ifc("wan-edge-02", "Ethernet1/2", "10.80.0.3/24", ospf=False),
        ifc("mgmt-jump-01", "eth0", "10.99.0.10/24", vlan=10, ospf=False),
        ifc("dns-01", "eth0", "10.99.0.24/24", vlan=10, ospf=False),
        ifc("fin-app-01", "eth0", "10.40.10.55/24", vlan=110, ospf=False),
        ifc("dev-vm-01", "eth0", "10.50.20.66/24", vlan=120, ospf=False),
        ifc("app-01", "eth0", "10.30.0.11/24", vlan=210, ospf=False),
        ifc("db-01", "eth0", "10.30.1.21/24", vlan=220, ospf=False),
        ifc("branch-pc", "eth0", "10.80.0.55/24", ospf=False),
    ]

    vlans = [
        Vlan(id=10, name="mgmt", subnet="10.99.0.0/24"),
        Vlan(id=110, name="finance", subnet="10.40.10.0/24"),
        Vlan(id=120, name="dev", subnet="10.50.20.0/24"),
        Vlan(id=210, name="prod-app", subnet="10.30.0.0/24"),
        Vlan(id=220, name="prod-db", subnet="10.30.1.0/24"),
    ]

    subnets = [
        SubnetDef(cidr="10.99.0.0/24", vlan_id=10, zone="mgmt", label="management"),
        SubnetDef(cidr="10.40.10.0/24", vlan_id=110, zone="finance", label="finance-vlan"),
        SubnetDef(cidr="10.50.20.0/24", vlan_id=120, zone="dev", label="dev-vlan"),
        SubnetDef(cidr="10.30.0.0/24", vlan_id=210, zone="prod-app", label="prod-app-tier"),
        SubnetDef(cidr="10.30.1.0/24", vlan_id=220, zone="prod-db", label="prod-db-tier"),
        SubnetDef(cidr="10.80.0.0/24", vlan_id=None, zone="branch", label="branch-office"),
        SubnetDef(cidr="10.200.0.0/30", vlan_id=None, zone="transit", label="core-dist1-p2p"),
        SubnetDef(cidr="10.200.0.4/30", vlan_id=None, zone="transit", label="core-dist2-p2p"),
        SubnetDef(cidr="10.200.1.0/24", vlan_id=None, zone="transit", label="dist1-fin-link"),
        SubnetDef(cidr="10.200.4.0/30", vlan_id=None, zone="transit", label="dist1-dist2-p2p"),
        SubnetDef(cidr="10.200.5.0/24", vlan_id=None, zone="transit", label="dist2-devlink"),
        SubnetDef(cidr="10.200.9.0/30", vlan_id=None, zone="transit", label="core-fw-p2p"),
        SubnetDef(cidr="10.200.2.0/30", vlan_id=None, zone="transit", label="core-wan1-p2p"),
        SubnetDef(cidr="10.200.3.4/30", vlan_id=None, zone="transit", label="core-wan2-p2p"),
    ]

    acls = [
        Acl(name="PROTECT-MGMT", rules=[
            AclRule(seq=5, action="permit", proto="udp", src="any", dst="10.99.0.24/32",
                    dst_port=53, note="dns queries allowed from anywhere"),
            AclRule(seq=10, action="permit", proto="ip", src="10.99.0.0/24",
                    dst="10.99.0.0/24", note="intra-mgmt"),
            AclRule(seq=20, action="deny", proto="ip", src="any", dst="10.99.0.0/24",
                    note="mgmt hosts reachable only from mgmt subnet"),
        ]),
        Acl(name="SEG-ISOLATE-FIN", rules=[
            AclRule(seq=10, action="deny", proto="ip", src="10.50.20.0/24",
                    dst="10.40.10.0/24", note="block dev to finance"),
            AclRule(seq=20, action="permit", proto="ip", src="any", dst="any"),
        ]),
        Acl(name="SEG-ISOLATE-DEV", rules=[
            AclRule(seq=10, action="deny", proto="ip", src="10.40.10.0/24",
                    dst="10.50.20.0/24", note="block finance to dev"),
            AclRule(seq=20, action="permit", proto="ip", src="any", dst="any"),
        ]),
    ]

    static_routes = [
        StaticRoute(device="wan-edge-01", prefix="0.0.0.0/0", next_hop="10.200.2.2", distance=1),
        StaticRoute(device="wan-edge-02", prefix="0.0.0.0/0", next_hop="10.200.3.6", distance=1),
    ]

    bgp_processes = [
        BgpProcess(device="core-01", local_as=65000, neighbors=[
            BgpNeighbor(ip="10.200.2.1", remote_as=65100, advertised_prefixes=["10.80.0.0/24"]),
            BgpNeighbor(ip="10.200.3.5", remote_as=65100, advertised_prefixes=["10.80.0.0/24"]),
        ]),
    ]

    firewalls = [
        FirewallDef(device="fw-01", default_action="deny", rules=[
            FirewallRule(seq=10, action="permit", src="10.30.0.0/24", dst="10.30.1.0/24",
                         proto="tcp", dst_port=5432, label="app-to-postgres"),
            FirewallRule(seq=15, action="permit", src="10.40.10.0/24", dst="10.30.1.0/24",
                         proto="tcp", dst_port=5432, label="finance-to-postgres"),
            FirewallRule(seq=20, action="permit", src="10.99.0.0/24", dst="10.30.0.0/24",
                         proto="tcp", dst_port=22, label="jump-admin-ssh"),
            FirewallRule(seq=30, action="permit", src="any", dst="10.99.0.24/32",
                         proto="udp", dst_port=53, label="dns-any-source"),
            FirewallRule(seq=40, action="permit", src="any", dst="10.99.0.24/32",
                         proto="tcp", dst_port=53, label="dns-tcp-any-source"),
            FirewallRule(seq=1000, action="deny", src="any", dst="any", proto="ip",
                         label="explicit-default-deny"),
        ])
    ]

    services = [
        ServiceDef(name="dns", endpoint_ip="10.99.0.24", port=53, proto="udp"),
        ServiceDef(name="postgres", endpoint_ip="10.30.1.21", port=5432, proto="tcp"),
        ServiceDef(name="app-ssh", endpoint_ip="10.30.0.11", port=22, proto="tcp"),
        ServiceDef(name="app-web", endpoint_ip="10.30.0.11", port=8443, proto="tcp"),
    ]

    return TwinPayload(
        name="lab-core-twin",
        devices=devices,
        interfaces=interfaces,
        vlans=vlans,
        subnets=subnets,
        acls=acls,
        static_routes=static_routes,
        bgp_processes=bgp_processes,
        firewalls=firewalls,
        services=services,
    )


SEED_INTENTS: list[dict] = [
    {"name": "app-tier-to-postgres", "itype": "must_reach", "severity": "CRITICAL",
     "params": {"src_subnet": "10.30.0.0/24", "dst_ip": "10.30.1.21", "proto": "tcp", "port": 5432}},
    {"name": "no-direct-db-from-branch", "itype": "must_not_reach", "severity": "CRITICAL",
     "params": {"src_subnet": "10.80.0.0/24", "dst_ip": "10.30.1.21"}},
    {"name": "dev-isolated-from-finance", "itype": "must_not_reach", "severity": "HIGH",
     "params": {"src_subnet": "10.50.20.0/24", "dst_ip": "10.40.10.55"}},
    {"name": "finance-isolated-from-dev", "itype": "must_not_reach", "severity": "HIGH",
     "params": {"src_subnet": "10.40.10.0/24", "dst_ip": "10.50.20.66"}},
    {"name": "branch-primary-and-backup", "itype": "route_exists", "severity": "HIGH",
     "params": {"device": "core-01", "prefix": "10.80.0.0/24", "min_routes": 2}},
    {"name": "mgmt-jump-restricted", "itype": "only_from_subnet", "severity": "HIGH",
     "params": {"dst_ip": "10.99.0.10", "allowed_src_subnets": ["10.99.0.0/24"]}},
    {"name": "ops-reach-dev", "itype": "must_reach", "severity": "MEDIUM",
     "params": {"src_subnet": "10.99.0.0/24", "dst_ip": "10.50.20.66", "proto": "tcp", "port": 22}},
    {"name": "app-to-dns", "itype": "must_reach", "severity": "HIGH",
     "params": {"src_subnet": "10.30.0.0/24", "dst_ip": "10.99.0.24", "proto": "udp", "port": 53}},
    {"name": "finance-to-dns", "itype": "must_reach", "severity": "HIGH",
     "params": {"src_subnet": "10.40.10.0/24", "dst_ip": "10.99.0.24", "proto": "udp", "port": 53}},
    {"name": "branch-to-dns", "itype": "must_reach", "severity": "HIGH",
     "params": {"src_subnet": "10.80.0.0/24", "dst_ip": "10.99.0.24", "proto": "udp", "port": 53}},
    {"name": "jump-admin-to-app", "itype": "must_reach", "severity": "HIGH",
     "params": {"src_subnet": "10.99.0.0/24", "dst_ip": "10.30.0.11", "proto": "tcp", "port": 22}},
]
