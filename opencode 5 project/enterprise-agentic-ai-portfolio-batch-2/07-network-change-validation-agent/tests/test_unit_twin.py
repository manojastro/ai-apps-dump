"""Unit tests for the twin engine: routing, ACLs, firewall, MTU, asymmetry."""
from __future__ import annotations

from simulator.configs import DiffParser, apply_ops
from simulator.lab import build_lab_twin
from simulator.models import (
    Device,
    Interface,
    OspfConfig,
    StaticRoute,
    TwinPayload,
)
from app.services.twin import TwinRuntime


def base_runtime() -> TwinRuntime:
    return TwinRuntime(build_lab_twin())


def test_longest_prefix_match_beats_default() -> None:
    rt = base_runtime()
    wan = rt.routing_table("wan-edge-01")
    assert any(r.prefix == "0.0.0.0/0" for r in wan)
    route = rt.route_lookup("wan-edge-01", "10.99.0.24")
    assert route is not None and route.prefix != "0.0.0.0/0"


def test_admin_distance_prefers_bgp_over_ospf() -> None:
    twin = build_lab_twin()
    twin.static_routes.append(StaticRoute(
        device="core-01", prefix="10.80.0.0/24", next_hop="10.200.2.1", distance=200))
    runtime = TwinRuntime(twin)
    core = [r for r in runtime.routing_table("core-01") if r.prefix == "10.80.0.0/24"]
    assert {r.protocol for r in core} == {"bgp", "static"}
    best = runtime.route_lookup("core-01", "10.80.0.55")
    assert best is not None and best.protocol == "bgp"


def test_acl_first_match_and_implicit_deny() -> None:
    rt = base_runtime()
    result = rt.simulate_flow("dev-vm-01", "10.40.10.55", "tcp", 22)
    assert result.status == "denied_acl"
    assert "SEG-ISOLATE-FIN" in (result.reason or "")


def test_firewall_default_deny_blocks_branch_to_db() -> None:
    rt = base_runtime()
    result = rt.simulate_flow("branch-pc", "10.30.1.21", "tcp", 5432)
    assert result.status == "denied_fw"
    assert result.drop_at == "fw-01"


def test_mtu_violation_detected_on_ingress() -> None:
    twin = build_lab_twin()
    for iface in twin.interfaces:
        if iface.device == "fw-01" and iface.name == "Vlan210":
            iface.mtu = 1300
    result = TwinRuntime(twin).simulate_flow("app-01", "10.30.1.21", "tcp", 5432)
    assert result.status == "mtu_blocked"
    assert "Vlan210" in (result.reason or "")


def test_asymmetric_route_detection_after_static_pinning() -> None:
    twin = build_lab_twin()
    ops = DiffParser().parse("device core-01\n+ip route 10.50.20.0/24 10.200.1.1\n",
                             twin)
    candidate, _ = apply_ops(twin, ops)
    runtime = TwinRuntime(candidate)
    assert runtime.reverse_path_differs("dns-01", "10.50.20.66", "udp", 53)


def test_baseline_paths_are_symmetric() -> None:
    rt = base_runtime()
    assert not rt.reverse_path_differs("dns-01", "10.50.20.66", "udp", 53)
    assert not rt.reverse_path_differs("app-01", "10.30.1.21", "tcp", 5432)


def test_ospf_shortest_path_uses_lower_cost() -> None:
    rt = base_runtime()
    dist, first = rt._ospf_dijkstra("core-01")
    assert dist.get("dist-02") == 10
    assert first.get("access-dev-01") == "dist-02"
    routes = {r.prefix: r for r in rt.routing_table("core-01")
              if r.protocol == "ospf" and r.prefix.startswith("10.50.20")}
    assert routes, "core must learn dev subnet via OSPF"
    route = next(iter(routes.values()))
    assert route.cost == 20 and route.next_hop == "10.200.0.6"


def test_no_route_when_prefix_withdrawn() -> None:
    twin = build_lab_twin()
    for iface in twin.interfaces:
        if iface.device == "access-dev-01":
            iface.ospf = OspfConfig(enabled=False)
    result = TwinRuntime(twin).simulate_flow("mgmt-jump-01", "10.50.20.66", "tcp", 22)
    assert result.status in ("no_route", "ttl_exceeded")


def test_gateway_outside_subnet_rejected() -> None:
    twin = build_lab_twin()
    for device in twin.devices:
        if device.name == "fin-app-01":
            device.default_gateway = "10.99.0.1"
    result = TwinRuntime(twin).simulate_flow("fin-app-01", "10.30.1.21", "tcp", 5432)
    assert result.status == "no_gateway"
    assert "outside local subnet" in (result.reason or "")


def test_vlan_mismatch_breaks_l2_adjacency() -> None:
    twin = build_lab_twin()
    for iface in twin.interfaces:
        if iface.device == "access-fin-01" and iface.name == "Vlan110":
            iface.vlan = 111
    result = TwinRuntime(twin).simulate_flow("fin-app-01", "10.30.1.21", "tcp", 5432)
    assert result.status == "no_gateway"
    assert "vlan-mismatch" in (result.reason or "")


def test_host_down_status_for_disabled_endpoint() -> None:
    twin = build_lab_twin()
    for iface in twin.interfaces:
        if iface.device == "dns-01":
            iface.enabled = False
    result = TwinRuntime(twin).simulate_flow("app-01", "10.99.0.24", "udp", 53)
    assert result.status == "host_down"


def test_matrix_shape_and_summary_counts() -> None:
    rows = base_runtime().reachability_matrix()
    assert len(rows) == 7 * 6 * 4
    blocked = sum(1 for r in rows if r["status"] != "allowed")
    allowed = len(rows) - blocked
    assert blocked > 0 and allowed > 0


def test_small_line_topology_ospf_propagation() -> None:
    payload = TwinPayload(
        devices=[
            Device(name="r1", role="core", zone="transit"),
            Device(name="r2", role="core", zone="transit"),
            Device(name="r3", role="core", zone="transit"),
        ],
        interfaces=[
            Interface(device="r1", name="e0", cidr="192.168.1.1/30"),
            Interface(device="r2", name="e0", cidr="192.168.1.2/30",
                      ospf=OspfConfig(cost=5)),
            Interface(device="r2", name="e1", cidr="192.168.2.1/30"),
            Interface(device="r3", name="e1", cidr="192.168.2.2/30"),
        ],
        subnets=[],
    )
    runtime = TwinRuntime(payload)
    dist, _ = runtime._ospf_dijkstra("r1")
    assert dist["r3"] == 20
    table = {r.prefix: r for r in runtime.routing_table("r1") if r.protocol == "ospf"}
    assert "192.168.2.0/30" in table
    route = table["192.168.2.0/30"]
    assert route.cost == 10
    assert route.next_hop == "192.168.1.2"
