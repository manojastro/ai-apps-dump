"""Multi-vendor flavored config rendering, unified diff parsing and candidate application."""
from __future__ import annotations

import re
from typing import Any

from simulator.models import (
    Acl,
    AclRule,
    BgpNeighbor,
    BgpProcess,
    Device,
    FirewallRule,
    Interface,
    OspfConfig,
    StaticRoute,
    TwinPayload,
    cidr_contains,
    cidrs_equal,
)

DEVICE_LINE = re.compile(r"^(?:hostname|device)\s+(\S+)$")
INTERFACE_LINE = re.compile(r"^interface\s+(\S+)$")
ACL_CTX_LINE = re.compile(r"^ip\s+access-list\s+(?:extended\s+)?(\S+)$")
NO_ACL_LINE = re.compile(r"^no\s+ip\s+access-list\s+(?:extended\s+)?(\S+)\s*$")
OSPF_LINE = re.compile(r"^router\s+ospf\s+\d+$")
BGP_LINE = re.compile(r"^router\s+bgp\s+(\d+)$")
FIREWALL_POLICY = re.compile(
    r"^firewall\s+policy\s+(\d+)\s+(permit|deny)\s+(\S+)\s+(\S+)\s+(ip|tcp|udp|icmp)"
    r"(?:\s+eq\s+(\d+))?(?:\s+label\s+(.+))?\s*$"
)
SERVICE_LINE = re.compile(r"^service\s+(\S+)$")


class ConfigError(ValueError):
    pass


def _rule_key(action: str, proto: str, src: str, dst: str, port: int | None) -> tuple:
    return (action, proto, src, dst, port)


class DiffParser:
    """Parses +/- unified diff lines against a device-context state machine."""

    def parse(self, diff_text: str, payload: TwinPayload) -> list[dict[str, Any]]:
        ops: list[dict[str, Any]] = []
        ctx: dict[str, Any] = {
            "device": None,
            "iface": None,
            "acl": None,
            "bgp_asn": None,
            "ospf": False,
            "service": None,
        }
        devices = {d.name for d in payload.devices}

        for lineno, raw in enumerate(diff_text.splitlines(), start=1):
            line = raw.rstrip()
            if not line.strip() or line.strip().startswith(("!", "#")):
                continue
            mode = "context"
            body = line.strip()
            if body.startswith(("+", "-")) and not body.startswith(("+++", "---")):
                mode = "add" if body[0] == "+" else "remove"
                body = body[1:].strip()
            if not body:
                continue

            m = DEVICE_LINE.match(body)
            if m:
                if m.group(1) not in devices:
                    raise ConfigError(f"line {lineno}: unknown device {m.group(1)}")
                ctx = {"device": m.group(1), "iface": None, "acl": None, "bgp_asn": None,
                       "ospf": False, "service": None}
                continue
            m = INTERFACE_LINE.match(body)
            if m:
                ctx["iface"] = m.group(1)
                ctx["acl"] = None
                self._require_iface(payload, ctx["device"], ctx["iface"], lineno)
                continue
            m = ACL_CTX_LINE.match(body)
            if m:
                ctx["acl"] = m.group(1)
                ctx["iface"] = None
                continue
            m = OSPF_LINE.match(body)
            if m:
                ctx["ospf"] = True
                ctx["acl"] = None
                ctx["iface"] = None
                continue
            m = BGP_LINE.match(body)
            if m:
                ctx["bgp_asn"] = int(m.group(1))
                ctx["ospf"] = False
                ctx["acl"] = None
                ctx["iface"] = None
                continue
            m = SERVICE_LINE.match(body)
            if m:
                ctx["service"] = m.group(1)
                continue

            if mode == "context":
                continue
            op = self._parse_operation(mode, body, ctx, payload, lineno)
            if op is not None:
                ops.append(op)
        return ops

    def _require_iface(self, payload: TwinPayload, device: str | None, iface: str | None, lineno: int) -> None:
        if device is None or iface is None:
            return
        names = {(i.device, i.name) for i in payload.interfaces}
        if (device, iface) not in names:
            raise ConfigError(f"line {lineno}: unknown interface {device}:{iface}")

    def _parse_operation(
        self, mode: str, body: str, ctx: dict[str, Any], payload: TwinPayload, lineno: int
    ) -> dict[str, Any] | None:
        removing = mode == "remove"

        m = NO_ACL_LINE.match(body)
        if m:
            return {"kind": "acl_delete", "acl": m.group(1)}

        if ctx.get("iface"):
            return self._iface_op(mode, body, ctx, lineno)

        if ctx.get("ospf"):
            return self._ospf_op(mode, body, ctx, lineno)

        if ctx.get("acl"):
            return self._acl_op(mode, body, ctx, lineno)

        if ctx.get("bgp_asn") is not None:
            return self._bgp_op(mode, body, ctx, lineno, removing)

        m = re.match(r"^ip\s+route\s+(\S+)\s+(\S+)(?:\s+(\d+))?\s*$", body)
        if m:
            return {
                "kind": "static_route",
                "device": ctx["device"],
                "prefix": m.group(1),
                "next_hop": m.group(2),
                "distance": int(m.group(3)) if m.group(3) else 1,
                "remove": removing,
            }

        m = re.match(r"^no\s+ip\s+route\s+(\S+)(?:\s+(\S+))?\s*$", body)
        if m:
            return {
                "kind": "static_route",
                "device": ctx["device"],
                "prefix": m.group(1),
                "next_hop": m.group(2),
                "distance": None,
                "remove": True,
            }

        m = re.match(r"^ip\s+default-gateway\s+(\S+)\s*$", body)
        if m:
            return {"kind": "gateway", "device": ctx["device"], "gateway": m.group(1)}

        m = FIREWALL_POLICY.match(body)
        if m:
            return {
                "kind": "firewall_policy",
                "device": ctx["device"],
                "seq": int(m.group(1)),
                "action": m.group(2),
                "src": m.group(3),
                "dst": m.group(4),
                "proto": m.group(5),
                "port": int(m.group(6)) if m.group(6) else None,
                "label": (m.group(7) or "").strip(),
                "remove": removing,
            }

        m = re.match(r"^no\s+firewall\s+policy\s+(\d+)\s*$", body)
        if m:
            return {"kind": "firewall_policy", "device": ctx["device"], "seq": int(m.group(1)), "remove": True}

        if ctx.get("service"):
            m = re.match(r"^(shutdown|enable)\s*$", body)
            if m:
                return {
                    "kind": "service_state",
                    "service": ctx["service"],
                    "enabled": m.group(1) == "enable",
                }

        if re.match(r"^(ntp server|snmp-server|logging|banner)\b", body) or body.startswith("description"):
            return {"kind": "noop", "line": body, "note": "recognized but unmodeled feature"}

        return {"kind": "unknown", "line": body, "note": f"unparsed at line {lineno}"}

    def _iface_op(self, mode: str, body: str, ctx: dict[str, Any], lineno: int) -> dict[str, Any]:
        base = {"kind": "interface", "device": ctx["device"], "iface": ctx["iface"]}
        m = re.match(r"^ip\s+address\s+(\S+)\s*$", body)
        if m:
            return {**base, "attr": "cidr", "value": m.group(1), "remove": False}
        if re.match(r"^no\s+ip\s+address\s*$", body):
            return {**base, "attr": "cidr", "value": None, "remove": True}
        if re.match(r"^shutdown\s*$", body):
            return {**base, "attr": "enabled", "value": False}
        if re.match(r"^no\s+shutdown\s*$", body):
            return {**base, "attr": "enabled", "value": True}
        m = re.match(r"^mtu\s+(\d+)\s*$", body)
        if m:
            return {**base, "attr": "mtu", "value": int(m.group(1))}
        m = re.match(r"^switchport\s+access\s+vlan\s+(\d+)\s*$", body)
        if m:
            return {**base, "attr": "vlan", "value": int(m.group(1))}
        m = re.match(r"^ip\s+access-group\s+(\S+)\s+(in|out)\s*$", body)
        if m:
            return {**base, "attr": f"acl_{m.group(2)}", "value": m.group(1), "remove": False}
        m = re.match(r"^no\s+ip\s+access-group\s+(\S+)\s+(in|out)\s*$", body)
        if m:
            return {**base, "attr": f"acl_{m.group(2)}", "value": None, "remove": True}
        if body.startswith("description"):
            return {"kind": "noop", "line": body, "note": "interface description"}
        raise ConfigError(f"line {lineno}: unsupported interface command '{body}'")

    def _ospf_op(self, mode: str, body: str, ctx: dict[str, Any], lineno: int) -> dict[str, Any]:
        m = re.match(r"^(?:no\s+)?network\s+(\S+)(?:\s+area\s+\d+)?\s*$", body)
        if not m:
            raise ConfigError(f"line {lineno}: unsupported ospf command '{body}'")
        return {
            "kind": "ospf_network",
            "device": ctx["device"],
            "prefix": m.group(1),
            "remove": mode == "remove",
        }

    def _acl_op(self, mode: str, body: str, ctx: dict[str, Any], lineno: int) -> dict[str, Any]:
        m = re.match(
            r"^(?:no\s+)?(permit|deny)\s+(ip|tcp|udp|icmp)\s+(\S+)\s+(\S+)(?:\s+eq\s+(\d+))?\s*(.*)$",
            body,
        )
        if not m:
            raise ConfigError(f"line {lineno}: unsupported ace '{body}'")
        note = (m.group(6) or "").strip()
        return {
            "kind": "acl_rule",
            "acl": ctx["acl"],
            "action": m.group(1),
            "proto": m.group(2),
            "src": m.group(3),
            "dst": m.group(4),
            "port": int(m.group(5)) if m.group(5) else None,
            "remove": mode == "remove",
            "note": note,
        }

    def _bgp_op(self, mode: str, body: str, ctx: dict[str, Any], lineno: int, removing: bool) -> dict[str, Any]:
        m = re.match(r"^(?:no\s+)?neighbor\s+(\S+)\s+remote-as\s+(\d+)\s*$", body)
        if m:
            return {
                "kind": "bgp_neighbor",
                "device": ctx["device"],
                "local_as": ctx["bgp_asn"],
                "peer": m.group(1),
                "remote_as": int(m.group(2)),
                "remove": removing,
            }
        m = re.match(r"^(?:no\s+)?neighbor\s+(\S+)\s+advertised-prefixes\s+(\S+)\s*$", body)
        if m:
            return {
                "kind": "bgp_prefix",
                "device": ctx["device"],
                "local_as": ctx["bgp_asn"],
                "peer": m.group(1),
                "prefix": m.group(2),
                "remove": removing,
            }
        m = re.match(r"^(?:no\s+)?network\s+(\S+)\s*$", body)
        if m:
            return {
                "kind": "bgp_network",
                "device": ctx["device"],
                "local_as": ctx["bgp_asn"],
                "prefix": m.group(1),
                "remove": removing,
            }
        raise ConfigError(f"line {lineno}: unsupported bgp command '{body}'")


def apply_ops(payload: TwinPayload, ops: list[dict[str, Any]]) -> tuple[TwinPayload, list[dict[str, Any]]]:
    """Apply parsed operations to a copy of the payload, returning a change journal."""
    twin = payload.model_copy(deep=True)
    journal: list[dict[str, Any]] = []

    def dev(name: str | None) -> Device:
        for d in twin.devices:
            if d.name == name:
                return d
        raise ConfigError(f"unknown device {name}")

    def iface(device: str, name: str) -> Interface:
        for i in twin.interfaces:
            if i.device == device and i.name == name:
                return i
        raise ConfigError(f"unknown interface {device}:{name}")

    for op in ops:
        kind = op["kind"]
        if kind == "noop":
            journal.append({"kind": "noop", "line": op.get("line", ""), "after": None, "before": None})
            continue
        if kind == "unknown":
            raise ConfigError(f"unparsed config line: {op.get('line')}")
        if kind == "interface":
            target = iface(op["device"], op["iface"])
            attr = op["attr"]
            before = getattr(target, attr)
            setattr(target, attr, op["value"])
            journal.append({"kind": "interface", "device": op["device"], "iface": op["iface"],
                            "attr": attr, "before": before, "after": op["value"]})
        elif kind == "acl_delete":
            twin.acls = [a for a in twin.acls if a.name != op["acl"]]
            for i in twin.interfaces:
                if i.acl_in == op["acl"]:
                    i.acl_in = None
                if i.acl_out == op["acl"]:
                    i.acl_out = None
            journal.append({"kind": "acl_delete", "acl": op["acl"], "before": op["acl"], "after": None})
        elif kind == "acl_rule":
            acl = _ensure_acl(twin, op["acl"])
            key = _rule_key(op["action"], op["proto"], op["src"], op["dst"], op["port"])
            existing = next((r for r in acl.rules if _rule_key(r.action, r.proto, r.src, r.dst, r.dst_port) == key), None)
            if op["remove"]:
                if existing:
                    acl.rules.remove(existing)
                journal.append({"kind": "acl_rule", "acl": op["acl"], "before": key, "after": None})
            else:
                if not existing:
                    seq = max((r.seq for r in acl.rules), default=0) + 10
                    acl.rules.append(AclRule(seq=seq, action=op["action"], proto=op["proto"],
                                             src=op["src"], dst=op["dst"], dst_port=op["port"]))
                journal.append({"kind": "acl_rule", "acl": op["acl"], "before": None, "after": key})
        elif kind == "static_route":
            table = [r for r in twin.static_routes if r.device == op["device"]]
            match = next((r for r in table if r.prefix == op["prefix"]
                          and (op.get("next_hop") is None or r.next_hop == op["next_hop"])), None)
            if op["remove"]:
                if match:
                    twin.static_routes.remove(match)
                journal.append({"kind": "static_route", "device": op["device"],
                                "before": match.prefix if match else None, "after": None})
            else:
                if match:
                    before = match.next_hop
                    match.next_hop = op["next_hop"]
                    match.distance = op["distance"] or match.distance
                else:
                    before = None
                    twin.static_routes.append(StaticRoute(device=op["device"], prefix=op["prefix"],
                                                          next_hop=op["next_hop"], distance=op["distance"]))
                journal.append({"kind": "static_route", "device": op["device"], "prefix": op["prefix"],
                                "before": before, "after": op["next_hop"]})
        elif kind == "gateway":
            d = dev(op["device"])
            before = d.default_gateway
            d.default_gateway = op["gateway"]
            journal.append({"kind": "gateway", "device": op["device"], "before": before, "after": op["gateway"]})
        elif kind == "ospf_network":
            changed = 0
            for i in twin.interfaces:
                if i.device != op["device"] or i.cidr is None:
                    continue
                if cidr_contains(op["prefix"], i.cidr) or cidrs_equal(op["prefix"], i.cidr):
                    before = i.ospf.enabled
                    i.ospf = OspfConfig(enabled=not op["remove"], area=0, cost=i.ospf.cost)
                    changed += 1
                    journal.append({"kind": "ospf_network", "device": op["device"], "iface": i.name,
                                    "prefix": op["prefix"], "before": before,
                                    "after": not op["remove"]})
            if changed == 0:
                journal.append({"kind": "ospf_network", "device": op["device"], "iface": None,
                                "prefix": op["prefix"], "before": None, "after": None})
        elif kind == "bgp_neighbor":
            proc = _ensure_bgp(twin, op["device"], op["local_as"])
            nb = next((n for n in proc.neighbors if n.ip == op["peer"]), None)
            if op["remove"]:
                if nb:
                    proc.neighbors.remove(nb)
                journal.append({"kind": "bgp_neighbor", "device": op["device"], "peer": op["peer"],
                                "before": op["peer"], "after": None})
            else:
                if not nb:
                    proc.neighbors.append(BgpNeighbor(ip=op["peer"], remote_as=op["remote_as"]))
                journal.append({"kind": "bgp_neighbor", "device": op["device"], "peer": op["peer"],
                                "before": None, "after": op["remote_as"]})
        elif kind == "bgp_prefix":
            proc = _ensure_bgp(twin, op["device"], op["local_as"])
            nb = next((n for n in proc.neighbors if n.ip == op["peer"]), None)
            if nb is None:
                raise ConfigError(f"unknown bgp neighbor {op['peer']} on {op['device']}")
            if op["remove"]:
                if op["prefix"] in nb.advertised_prefixes:
                    nb.advertised_prefixes.remove(op["prefix"])
                journal.append({"kind": "bgp_prefix", "device": op["device"], "peer": op["peer"],
                                "prefix": op["prefix"], "before": op["prefix"], "after": None})
            else:
                if op["prefix"] not in nb.advertised_prefixes:
                    nb.advertised_prefixes.append(op["prefix"])
                journal.append({"kind": "bgp_prefix", "device": op["device"], "peer": op["peer"],
                                "prefix": op["prefix"], "before": None, "after": op["prefix"]})
        elif kind == "bgp_network":
            journal.append({"kind": "bgp_network", "device": op["device"], "prefix": op["prefix"],
                            "before": None, "after": None if op["remove"] else op["prefix"]})
        elif kind == "firewall_policy":
            fw = next((f for f in twin.firewalls if f.device == op["device"]), None)
            if fw is None:
                raise ConfigError(f"device {op['device']} has no firewall policy table")
            if op["remove"]:
                before = next((r.model_dump() for r in fw.rules if r.seq == op["seq"]), None)
                fw.rules = [r for r in fw.rules if r.seq != op["seq"]]
                journal.append({"kind": "firewall_policy", "device": op["device"], "seq": op["seq"],
                                "before": before, "after": None})
            else:
                before = next((r.model_dump() for r in fw.rules if r.seq == op["seq"]), None)
                fw.rules = [r for r in fw.rules if r.seq != op["seq"]]
                fw.rules.append(FirewallRule(seq=op["seq"], action=op["action"], src=op["src"],
                                             dst=op["dst"], proto=op["proto"], dst_port=op["port"],
                                             label=op.get("label", "")))
                fw.rules.sort(key=lambda r: r.seq)
                journal.append({"kind": "firewall_policy", "device": op["device"], "seq": op["seq"],
                                "before": before, "after": op})
        elif kind == "service_state":
            svc = next((s for s in twin.services if s.name == op["service"]), None)
            if svc is None:
                raise ConfigError(f"unknown service {op['service']}")
            before = svc.enabled
            svc.enabled = op["enabled"]
            journal.append({"kind": "service_state", "service": op["service"], "before": before,
                            "after": op["enabled"]})
        else:
            raise ConfigError(f"unsupported operation kind {kind}")
    return twin, journal


def _ensure_acl(twin: TwinPayload, name: str) -> Acl:
    acl = next((a for a in twin.acls if a.name == name), None)
    if acl is None:
        acl = Acl(name=name)
        twin.acls.append(acl)
    return acl


def _ensure_bgp(twin: TwinPayload, device: str, local_as: int) -> BgpProcess:
    proc = next((b for b in twin.bgp_processes if b.device == device), None)
    if proc is None:
        proc = BgpProcess(device=device, local_as=local_as)
        twin.bgp_processes.append(proc)
    return proc


def render_config(twin: TwinPayload) -> dict[str, str]:
    """Render canonical Cisco-flavored running-config text per device."""
    output: dict[str, str] = {}
    acl_binders: dict[str, list[tuple[str, str, str]]] = {}
    for i in twin.interfaces:
        for direction in ("in", "out"):
            acl_name = getattr(i, f"acl_{direction}")
            if acl_name:
                acl_binders.setdefault(acl_name, []).append((i.device, i.name, direction))
    for device in twin.devices:
        lines = [f"! vendor: {device.vendor}", f"hostname {device.name}"]
        for i in twin.interfaces:
            if i.device != device.name:
                continue
            lines.append(f"interface {i.name}")
            if i.description:
                lines.append(f" description {i.description}")
            if i.cidr:
                lines.append(f" ip address {i.cidr}")
            lines.append(" shutdown" if not i.enabled else " no shutdown")
            lines.append(f" mtu {i.mtu}")
            if i.vlan is not None:
                lines.append(f" switchport access vlan {i.vlan}")
            if i.acl_in:
                lines.append(f" ip access-group {i.acl_in} in")
            if i.acl_out:
                lines.append(f" ip access-group {i.acl_out} out")
            if i.ospf.enabled and device.role not in ("host", "server", "jump"):
                lines.append(f" ip ospf {i.ospf.cost} area {i.ospf.area}")
        if device.default_gateway:
            lines.append(f"ip default-gateway {device.default_gateway}")
        for r in twin.static_routes:
            if r.device == device.name:
                lines.append(f"ip route {r.prefix} {r.next_hop} {r.distance}")
        for b in twin.bgp_processes:
            if b.device == device.name:
                lines.append(f"router bgp {b.local_as}")
                for nb in b.neighbors:
                    lines.append(f" neighbor {nb.ip} remote-as {nb.remote_as}")
                    for pfx in nb.advertised_prefixes:
                        lines.append(f" neighbor {nb.ip} advertised-prefixes {pfx}")
        own_acls = sorted({acl for acl, binders in acl_binders.items() if any(b[0] == device.name for b in binders)})
        for acl_name in own_acls:
            acl = next(a for a in twin.acls if a.name == acl_name)
            lines.append(f"ip access-list {acl.name}")
            for rule in sorted(acl.rules, key=lambda r: r.seq):
                port = f" eq {rule.dst_port}" if rule.dst_port else ""
                lines.append(f" {rule.action} {rule.proto} {rule.src} {rule.dst}{port}")
            for dev_name, if_name, direction in acl_binders[acl_name]:
                if dev_name == device.name:
                    lines.append(f"interface {if_name}")
                    lines.append(f" ip access-group {acl.name} {direction}")
        for fw in twin.firewalls:
            if fw.device == device.name:
                lines.append(f"! firewall default-action {fw.default_action}")
                for rule in sorted(fw.rules, key=lambda r: r.seq):
                    port = f" eq {rule.dst_port}" if rule.dst_port else ""
                    lines.append(f"firewall policy {rule.seq} {rule.action} {rule.src} {rule.dst}"
                                 f" {rule.proto}{port} label {rule.label}")
        output[device.name] = "\n".join(lines) + "\n"
    return output
