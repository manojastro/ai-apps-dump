"""Network digital twin engine: graph build, route lookup, policy evaluation, reachability."""
from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel

from simulator.models import (
    Device,
    Interface,
    TwinPayload,
    cidrs_equal,
    ip_in_subnet,
    norm_cidr,
    prefix_len,
)

ROUTER_ROLES = ("core", "distribution", "access", "firewall", "wan")
MAX_TTL = 16
ENDPOINT_DEVICES = [
    "mgmt-jump-01",
    "dns-01",
    "fin-app-01",
    "dev-vm-01",
    "app-01",
    "db-01",
    "branch-pc",
]
MATRIX_PORTS: list[tuple[str, int]] = [("tcp", 22), ("udp", 53), ("tcp", 5432), ("tcp", 8443)]

BLOCKED_STATUSES = {
    "denied_acl",
    "denied_fw",
    "no_route",
    "no_gateway",
    "mtu_blocked",
    "host_down",
    "no_host",
    "ttl_exceeded",
}


class Route(BaseModel):
    prefix: str
    next_hop: str | None = None
    protocol: Literal["connected", "static", "ospf", "bgp"]
    distance: int = 1
    cost: int = 0


class FlowResult(BaseModel):
    src: str
    dst: str
    dst_ip: str
    proto: str
    dst_port: int
    status: str
    reason: str | None = None
    path: list[str] = field(default_factory=list)
    drop_at: str | None = None
    detail: dict = {}


class TwinRuntime:
    """Executable model of one network snapshot."""

    def __init__(self, payload: TwinPayload) -> None:
        self.payload = payload
        self.devices: dict[str, Device] = {d.name: d for d in payload.devices}
        self.interfaces: dict[tuple[str, str], Interface] = {
            (i.device, i.name): i for i in payload.interfaces
        }
        self.acls: dict[str, dict[int, object]] = {}
        for acl in payload.acls:
            self.acls[acl.name] = {r.seq: r for r in acl.rules}
        self.firewalls: dict[str, object] = {f.device: f for f in payload.firewalls}
        self._ip_owner_all: dict[str, tuple[str, str]] = {}
        for i in payload.interfaces:
            if i.cidr:
                ip = i.cidr.split("/")[0]
                self._ip_owner_all[ip] = (i.device, i.name)
        self._routing_tables: dict[str, list[Route]] = {}
        self._segments: dict[str, list[tuple[str, str]]] = {}
        for i in payload.interfaces:
            if i.cidr and i.enabled and self._device_up(i.device):
                self._segments.setdefault(norm_cidr(i.cidr), []).append((i.device, i.name))

    def _device_up(self, name: str) -> bool:
        dev = self.devices.get(name)
        return bool(dev and dev.enabled)

    def up_interfaces(self, device: str) -> list[Interface]:
        return [i for i in self.payload.interfaces
                if i.device == device and i.enabled and self._device_up(device)]

    def primary_interface(self, device: str) -> Interface | None:
        ups = self.up_interfaces(device)
        return ups[0] if ups else None

    def primary_ip(self, device: str) -> str | None:
        iface = self.primary_interface(device)
        if iface and iface.cidr:
            return iface.cidr.split("/")[0]
        return None

    def owner_of_ip(self, ip: str, include_down: bool = False) -> tuple[str, str] | None:
        hit = self._ip_owner_all.get(ip)
        if hit is None:
            return None
        iface = self.interfaces.get(hit, None)
        if iface is None:
            return None
        if not include_down and (not iface.enabled or not self._device_up(iface.device)):
            return None
        return hit

    def vlan_compatible(self, a: Interface, b: Interface) -> bool:
        if a.vlan is None or b.vlan is None:
            return True
        return a.vlan == b.vlan

    def routing_table(self, device: str) -> list[Route]:
        if device in self._routing_tables:
            return self._routing_tables[device]
        routes: list[Route] = []
        for i in self.up_interfaces(device):
            if i.cidr:
                routes.append(Route(prefix=norm_cidr(i.cidr), next_hop=None,
                                    protocol="connected", distance=0))
        routes.extend(self._static_routes(device))
        routes.extend(self._ospf_routes(device))
        routes.extend(self._bgp_routes(device))
        self._routing_tables[device] = routes
        return routes

    def _static_routes(self, device: str) -> list[Route]:
        return [
            Route(prefix=r.prefix, next_hop=r.next_hop, protocol="static",
                  distance=r.distance, cost=0)
            for r in self.payload.static_routes if r.device == device
        ]

    def _bgp_routes(self, device: str) -> list[Route]:
        routes: list[Route] = []
        proc = next((b for b in self.payload.bgp_processes if b.device == device), None)
        if proc is None:
            return routes
        local_subnets = {i.cidr for i in self.up_interfaces(device) if i.cidr}
        for nb in proc.neighbors:
            owner = self.owner_of_ip(nb.ip)
            if owner is None:
                continue
            if not any(i.cidr and ip_in_subnet(nb.ip, i.cidr) for i in self.up_interfaces(device)):
                continue
            for pfx in nb.advertised_prefixes:
                if any(ip_in_subnet(pfx, s) or ip_in_subnet(s, pfx) for s in local_subnets):
                    continue
                routes.append(Route(prefix=pfx, next_hop=nb.ip, protocol="bgp", distance=20, cost=0))
        return routes

    def _ospf_routes(self, device: str) -> list[Route]:
        if not self._is_router(device):
            return []
        dist, first_hop = self._ospf_dijkstra(device)
        own_subnets = {norm_cidr(i.cidr) for i in self.up_interfaces(device) if i.cidr}
        best: dict[str, tuple[int, str, str]] = {}
        for other, d in dist.items():
            if other == device:
                continue
            for i in self.up_interfaces(other):
                if not i.ospf.enabled or not i.cidr:
                    continue
                pfx = norm_cidr(i.cidr)
                if any(cidrs_equal(pfx, s) for s in own_subnets):
                    continue
                fh = first_hop.get(other)
                if fh is None:
                    continue
                fh_ip = self._shared_neighbor_ip(device, fh)
                if fh_ip is None:
                    continue
                cand = (d, fh, fh_ip)
                cur = best.get(pfx)
                if cur is None or (d, fh) < (cur[0], cur[1]):
                    best[pfx] = cand
        return [
            Route(prefix=pfx, next_hop=v[2], protocol="ospf", distance=110, cost=v[0])
            for pfx, v in best.items()
        ]

    def _is_router(self, device: str) -> bool:
        dev = self.devices.get(device)
        return bool(dev and dev.role in ROUTER_ROLES)

    def _ospf_dijkstra(self, source: str) -> tuple[dict[str, int], dict[str, str]]:
        adj: dict[str, list[tuple[str, int]]] = {}
        seg_members: dict[str, list[tuple[str, Interface]]] = {}
        for i in self.payload.interfaces:
            if not (i.cidr and i.enabled and i.ospf.enabled and self._device_up(i.device)):
                continue
            if not self._is_router(i.device):
                continue
            seg_members.setdefault(norm_cidr(i.cidr), []).append((i.device, i))
        for cidr, members in seg_members.items():
            for da, ia in members:
                for db, ib in members:
                    if da == db:
                        continue
                    adj.setdefault(da, []).append((db, ia.ospf.cost, ib.name))
        dist: dict[str, int] = {source: 0}
        first: dict[str, str] = {}
        heap: list[tuple[int, str, str | None]] = [(0, source, None)]
        settled: set[str] = set()
        while heap:
            d, node, fh = heapq.heappop(heap)
            if node in settled:
                continue
            settled.add(node)
            if fh:
                first[node] = fh
            for entry in adj.get(node, []):
                nb, cost = entry[0], entry[1]
                nd = d + cost
                cand_fh = fh if fh else nb
                if nd < dist.get(nb, 10**9):
                    dist[nb] = nd
                    heapq.heappush(heap, (nd, nb, cand_fh))
        return dist, first

    def _shared_neighbor_ip(self, device: str, neighbor: str) -> str | None:
        for mine in self.up_interfaces(device):
            if not mine.cidr:
                continue
            for theirs in self.up_interfaces(neighbor):
                if theirs.cidr and cidrs_equal(mine.cidr, theirs.cidr):
                    if self.vlan_compatible(mine, theirs):
                        return theirs.cidr.split("/")[0]
        return None

    def route_lookup(self, device: str, ip: str) -> Route | None:
        candidates = [r for r in self.routing_table(device) if ip_in_subnet(ip, r.prefix)]
        if not candidates:
            return None
        candidates.sort(
            key=lambda r: (-prefix_len(r.prefix), r.distance, r.cost, r.next_hop or "")
        )
        return candidates[0]

    def resolve_egress(self, current: str, next_hop: str) -> tuple[str, Interface] | None:
        """Recursively resolve the egress interface and neighbor for a next-hop IP."""
        nh = next_hop
        seen: set[str] = set()
        for _ in range(4):
            if nh in seen:
                return None
            seen.add(nh)
            owner = self.owner_of_ip(nh)
            if owner is None:
                return None
            egress = next((i for i in self.up_interfaces(current)
                           if i.cidr and ip_in_subnet(nh, i.cidr)
                           and self.vlan_compatible(i, self.interfaces[owner])), None)
            if egress is not None:
                return owner[0], egress
            route = self.route_lookup(current, nh)
            if route is None or route.next_hop is None:
                return None
            nh = route.next_hop
        return None

    def _match_addr(self, value: str, ip: str) -> bool:
        return value == "any" or ip_in_subnet(ip, value)

    def _eval_acl(self, acl_name: str, src_ip: str, dst_ip: str, proto: str,
                  dport: int, sport: int | None) -> tuple[str, int] | None:
        acl = self.acls.get(acl_name)
        if acl is None:
            return None
        for seq in sorted(acl):
            rule = acl[seq]
            if rule.proto not in ("ip", proto):
                continue
            if not self._match_addr(rule.src, src_ip):
                continue
            if not self._match_addr(rule.dst, dst_ip):
                continue
            if rule.dst_port is not None and dport != rule.dst_port and (
                sport is None or sport != rule.dst_port
            ):
                continue
            return (str(rule.action), seq)
        return ("deny", 0)

    def _eval_firewall(self, device: str, src_ip: str, dst_ip: str, proto: str,
                       dport: int, sport: int | None) -> tuple[str, str] | None:
        fw = self.firewalls.get(device)
        if fw is None:
            return None
        for rule in sorted(fw.rules, key=lambda r: r.seq):
            if rule.proto not in ("ip", proto):
                continue
            if not self._match_addr(rule.src, src_ip):
                continue
            if not self._match_addr(rule.dst, dst_ip):
                continue
            if rule.dst_port is not None and dport != rule.dst_port and (
                sport is None or sport != rule.dst_port
            ):
                continue
            return (str(rule.action), rule.label or f"seq-{rule.seq}")
        return (fw.default_action, "default")

    def simulate_flow(self, src_device: str, dst_ip: str, proto: str = "tcp",
                      dst_port: int = 80, pkt_size: int = 1500) -> FlowResult:
        tgt_owner = self.owner_of_ip(dst_ip, include_down=True)
        dst_label = tgt_owner[0] if tgt_owner else dst_ip
        base = FlowResult(src=src_device, dst=dst_label, dst_ip=dst_ip,
                          proto=proto, dst_port=dst_port, status="allowed")

        src_dev = self.devices.get(src_device)
        if src_dev is None:
            return base.model_copy(update={"status": "no_host", "reason": "unknown-source"})
        if not src_dev.enabled or self.primary_interface(src_device) is None:
            return base.model_copy(update={"status": "host_down", "reason": "source-down"})

        tgt_owner = self.owner_of_ip(dst_ip, include_down=True)
        if tgt_owner is None:
            return base.model_copy(update={"status": "no_host", "reason": "ip-unassigned"})
        tgt_dev_name, _ = tgt_owner
        tgt_iface = self.interfaces[(tgt_dev_name, _)]
        if not tgt_iface.enabled or not self._device_up(tgt_dev_name):
            return base.model_copy(update={"status": "host_down", "reason": "destination-down",
                                           "drop_at": tgt_dev_name})

        if src_device == tgt_dev_name:
            return base

        src_iface = self.primary_interface(src_device)
        assert src_iface and src_iface.cidr
        src_ip = src_iface.cidr.split("/")[0]

        if ip_in_subnet(dst_ip, src_iface.cidr):
            if not self.vlan_compatible(src_iface, tgt_iface):
                return base.model_copy(update={
                    "status": "no_gateway",
                    "reason": f"vlan-mismatch {src_iface.vlan} vs {tgt_iface.vlan}",
                    "path": [src_device],
                })
            return base.model_copy(update={"path": [src_device, tgt_dev_name]})

        gw_ip = src_dev.default_gateway
        if not gw_ip:
            return base.model_copy(update={"status": "no_gateway",
                                           "reason": "no-gateway-configured",
                                           "path": [src_device]})
        if not ip_in_subnet(gw_ip, src_iface.cidr):
            return base.model_copy(update={
                "status": "no_gateway",
                "reason": f"gateway {gw_ip} outside local subnet {src_iface.cidr}",
                "path": [src_device],
            })
        gw_owner = self.owner_of_ip(gw_ip)
        if gw_owner is None:
            return base.model_copy(update={"status": "no_gateway",
                                           "reason": f"gateway {gw_ip} unreachable",
                                           "path": [src_device]})
        gw_dev_name, gw_if_name = gw_owner
        gw_iface = self.interfaces[gw_owner]
        if not self.vlan_compatible(src_iface, gw_iface):
            return base.model_copy(update={
                "status": "no_gateway",
                "reason": f"vlan-mismatch toward gateway ({src_iface.vlan} vs {gw_iface.vlan})",
                "path": [src_device],
            })

        path = [src_device, gw_dev_name]
        current = gw_dev_name
        arrival = self.interfaces[(gw_dev_name, gw_if_name)]
        visited: set[str] = {src_device}

        for _ in range(MAX_TTL):
            if current == tgt_dev_name:
                return base.model_copy(update={"path": path})
            if current in visited:
                return base.model_copy(update={"status": "ttl_exceeded",
                                               "reason": "routing loop",
                                               "path": path, "drop_at": current})
            visited.add(current)
            src_ip_for_policy = src_ip

            if arrival.acl_in:
                verdict = self._eval_acl(arrival.acl_in, src_ip_for_policy, dst_ip,
                                         proto, dst_port, None)
                if verdict and verdict[0] == "deny":
                    return base.model_copy(update={
                        "status": "denied_acl",
                        "reason": f"{arrival.acl_in} seq {verdict[1]} inbound on "
                                  f"{current}:{arrival.name}",
                        "path": path, "drop_at": current})
            if arrival.mtu < pkt_size:
                return base.model_copy(update={
                    "status": "mtu_blocked",
                    "reason": f"mtu {arrival.mtu} < {pkt_size} on {current}:{arrival.name}",
                    "path": path, "drop_at": current})
            if current in self.firewalls:
                verdict = self._eval_firewall(current, src_ip_for_policy, dst_ip,
                                              proto, dst_port, None)
                assert verdict is not None
                if verdict[0] == "deny":
                    return base.model_copy(update={
                        "status": "denied_fw",
                        "reason": f"firewall {current} rule {verdict[1]}",
                        "path": path, "drop_at": current})

            route = self.route_lookup(current, dst_ip)
            if route is None:
                return base.model_copy(update={"status": "no_route",
                                               "reason": f"no route at {current}",
                                               "path": path, "drop_at": current})

            if route.next_hop is None:
                egress = next((i for i in self.up_interfaces(current)
                               if i.cidr and cidrs_equal(i.cidr, route.prefix)), None)
                if egress is None:
                    return base.model_copy(update={"status": "no_route",
                                                   "reason": "connected segment missing",
                                                   "path": path, "drop_at": current})
                if egress.acl_out:
                    verdict = self._eval_acl(egress.acl_out, src_ip_for_policy, dst_ip,
                                             proto, dst_port, None)
                    if verdict and verdict[0] == "deny":
                        return base.model_copy(update={
                            "status": "denied_acl",
                            "reason": f"{egress.acl_out} seq {verdict[1]} outbound on "
                                      f"{current}:{egress.name}",
                            "path": path, "drop_at": current})
                if egress.mtu < pkt_size:
                    return base.model_copy(update={
                        "status": "mtu_blocked",
                        "reason": f"mtu {egress.mtu} < {pkt_size} on {current}:{egress.name}",
                        "path": path, "drop_at": current})
                path.append(tgt_dev_name)
                return base.model_copy(update={"path": path})

            nh_owner = self.owner_of_ip(route.next_hop)
            if nh_owner is None:
                return base.model_copy(update={
                    "status": "no_route",
                    "reason": f"next-hop {route.next_hop} unresolvable at {current}",
                    "path": path, "drop_at": current})
            resolved = self.resolve_egress(current, route.next_hop)
            if resolved is None:
                return base.model_copy(update={
                    "status": "no_route",
                    "reason": f"no egress toward next-hop {route.next_hop} at {current}",
                    "path": path, "drop_at": current})
            nh_dev, egress = resolved
            nh_iface = self.interfaces[nh_owner]
            if egress.acl_out:
                verdict = self._eval_acl(egress.acl_out, src_ip_for_policy, dst_ip,
                                         proto, dst_port, None)
                if verdict and verdict[0] == "deny":
                    return base.model_copy(update={
                        "status": "denied_acl",
                        "reason": f"{egress.acl_out} seq {verdict[1]} outbound on "
                                  f"{current}:{egress.name}",
                        "path": path, "drop_at": current})
            if egress.mtu < pkt_size:
                return base.model_copy(update={
                    "status": "mtu_blocked",
                    "reason": f"mtu {egress.mtu} < {pkt_size} on {current}:{egress.name}",
                    "path": path, "drop_at": current})
            path.append(nh_dev)
            arrival = nh_iface
            current = nh_dev

        return base.model_copy(update={"status": "ttl_exceeded", "reason": "max hops exceeded",
                                       "path": path, "drop_at": current})

    def reverse_path_differs(self, src: str, dst_ip: str, proto: str, dport: int) -> bool:
        fwd = self.simulate_flow(src, dst_ip, proto, dport)
        rev_src_dev = fwd.path[-1] if fwd.path else None
        if rev_src_dev is None or fwd.status != "allowed":
            return False
        src_ip = self.primary_ip(src)
        rev = self.simulate_flow(rev_src_dev, src_ip or "", proto, dport)
        if rev.status != "allowed":
            return False
        return list(reversed(fwd.path)) != rev.path

    def reachability_matrix(self) -> list[dict]:
        rows: list[dict] = []
        targets = [(d, self.primary_ip(d)) for d in ENDPOINT_DEVICES]
        for src in ENDPOINT_DEVICES:
            for dst_dev, dst_ip in targets:
                if dst_dev == src or dst_ip is None:
                    continue
                for proto, port in MATRIX_PORTS:
                    res = self.simulate_flow(src, dst_ip, proto, port)
                    asym = self.reverse_path_differs(src, dst_ip, proto, port) \
                        if res.status == "allowed" else False
                    rows.append({
                        "src": src,
                        "dst": dst_dev,
                        "proto": proto,
                        "port": port,
                        "status": res.status,
                        "reason": res.reason,
                        "path": res.path,
                        "asymmetric": asym,
                    })
        return rows


def diff_matrices(base_rows: list[dict], candidate_rows: list[dict]) -> dict:
    def key(r: dict) -> tuple:
        return (r["src"], r["dst"], r["proto"], r["port"])

    base_map = {key(r): r for r in base_rows}
    cand_map = {key(r): r for r in candidate_rows}
    newly_blocked, newly_allowed, still_ok, asymmetric_new = [], [], [], []
    for k, cr in cand_map.items():
        br = base_map.get(k)
        was_allowed = br is not None and br["status"] == "allowed"
        now_allowed = cr["status"] == "allowed"
        if was_allowed and not now_allowed:
            newly_blocked.append({"flow": cr, "was": br["status"] if br else None,
                                  "reason": cr["reason"]})
        elif not was_allowed and now_allowed:
            newly_allowed.append({"flow": cr, "was": br["status"] if br else "none"})
        elif now_allowed and br is not None:
            still_ok.append(cr)
        if now_allowed and cr.get("asymmetric") and (
            br is None or not br.get("asymmetric")
        ):
            asymmetric_new.append(cr)
    return {
        "total_probes": len(cand_map),
        "newly_blocked": newly_blocked,
        "newly_allowed": newly_allowed,
        "unchanged_allowed": len(still_ok),
        "asymmetric_new": asymmetric_new,
    }
