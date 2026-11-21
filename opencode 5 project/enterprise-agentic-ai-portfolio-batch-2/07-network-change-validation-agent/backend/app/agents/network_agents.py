"""Perception agents: config analysis, topology, routing, security, reachability."""
from __future__ import annotations

from collections import Counter
from typing import Any

from app.agents.base import AgentContext, BaseAgent
from app.schemas.api import Evidence, Hypothesis, RegressionOut
from simulator.models import TwinPayload, norm_cidr

FLOW_KIND_MAP = {
    "denied_acl": ("ACL_BLACKHOLE", "HIGH"),
    "denied_fw": ("FW_BLOCKED_FLOW", "HIGH"),
    "mtu_blocked": ("MTU_VIOLATION", "HIGH"),
    "no_route": ("NO_ROUTE", "HIGH"),
    "no_gateway": ("GATEWAY_UNREACHABLE", "HIGH"),
    "host_down": ("HOST_ISOLATED", "HIGH"),
    "no_host": ("NO_ROUTE", "MEDIUM"),
    "ttl_exceeded": ("ROUTE_LOOP", "HIGH"),
}
HOST_ENDPOINT_ROLES = ("jump", "server", "host")
USER_ZONES = {"mgmt", "finance", "dev", "prod-app", "prod-db", "branch"}
INFRASTRUCTURE_ZONES = {"transit", "prod-edge"}


class ConfigAnalysisAgent(BaseAgent):
    name = "ConfigAnalysisAgent"

    def execute(self, ctx: AgentContext) -> dict[str, Any]:
        kinds = Counter(op.get("kind") for op in ctx.ops)
        risky = [op for op in ctx.ops if is_risky_op(op)]
        return {
            "total_ops": len(ctx.ops),
            "op_kinds": dict(kinds),
            "risky_ops": len(risky),
            "noop_ops": sum(1 for op in ctx.ops if op.get("kind") == "noop"),
        }

    def hypotheses(self, ctx: AgentContext) -> list[Hypothesis]:
        material = [op for op in ctx.ops if op.get("kind") != "noop"]
        if not material:
            return []
        return [Hypothesis(
            id="H-CONFIG",
            statement=(f"The submitted diff alters {len(material)} configuration "
                       "objects; behavior change is plausible"),
            status="proposed",
            score=min(0.9, 0.3 + 0.1 * len(material)),
        )]


def is_risky_op(op: dict[str, Any]) -> bool:
    if op.get("kind") == "noop":
        return False
    if op.get("remove"):
        return True
    if op.get("kind") == "acl_rule" and op.get("action") == "deny":
        return True
    if op.get("kind") == "firewall_policy":
        return True
    if op.get("kind") == "interface" and op.get("attr") in ("enabled", "cidr", "mtu", "vlan"):
        return True
    return False


class TopologyAgent(BaseAgent):
    name = "TopologyAgent"

    def execute(self, ctx: AgentContext) -> dict[str, Any]:
        findings: list[dict[str, Any]] = []
        touched: set[str] = set()
        for entry in ctx.journal:
            dev = entry.get("device") or ""
            if dev:
                touched.add(dev)
            if entry.get("kind") == "interface":
                findings.append({
                    "type": "interface_change",
                    "device": dev,
                    "iface": entry.get("iface"),
                    "attr": entry.get("attr"),
                    "before": entry.get("before"),
                    "after": entry.get("after"),
                })
            elif entry.get("kind") == "acl_delete":
                findings.append({"type": "acl_removed", "acl": entry.get("acl"),
                                 "message": f"access-list {entry.get('acl')} deleted"})
        candidate = TwinPayload.model_validate(ctx.candidate_payload_dict or ctx.base_payload_dict)
        findings.extend(self._duplicate_ip_findings(candidate))
        findings.extend(self._zone_conflict_findings(candidate))
        for f in findings:
            if f["type"] in ("duplicate_ip", "subnet_zone_overlap"):
                touched.add(f.get("device") or f["devices"][0] if isinstance(
                    f.get("devices"), list) else f.get("device", ""))
                ctx.regressions.append(RegressionOut(
                    kind="SUBNET_OVERLAP",
                    severity="CRITICAL",
                    source=str(f.get("device") or (f.get("devices") or [""])[0]),
                    destination=f.get("subnet", f.get("ip", "")),
                    message=f.get("message", str(f)),
                    detail=f,
                ))
        ctx.topology_findings = findings
        ctx.blast_radius_devices = sorted(touched)
        return {
            "findings": len(findings),
            "devices_touched": sorted(touched),
            "overlap_findings": sum(1 for f in findings
                                    if f["type"] in ("duplicate_ip", "subnet_zone_overlap")),
        }

    @staticmethod
    def _duplicate_ip_findings(candidate: TwinPayload) -> list[dict[str, Any]]:
        seen: dict[str, str] = {}
        out: list[dict[str, Any]] = []
        for iface in candidate.interfaces:
            if not iface.cidr or not iface.enabled:
                continue
            ip = iface.cidr.split("/")[0]
            if ip in seen and seen[ip] != iface.device:
                out.append({
                    "type": "duplicate_ip",
                    "subnet": iface.cidr,
                    "ip": ip,
                    "devices": [seen[ip], iface.device],
                    "device": iface.device,
                    "message": (f"duplicate gateway address {ip} claimed on both "
                                f"{seen[ip]} and {iface.device}"),
                })
            else:
                seen.setdefault(ip, iface.device)
        return out

    @staticmethod
    def _zone_conflict_findings(candidate: TwinPayload) -> list[dict[str, Any]]:
        registry = {norm_cidr(s.cidr): s.zone for s in candidate.subnets}
        device_zone = {d.name: d.zone for d in candidate.devices}
        out: list[dict[str, Any]] = []
        for iface in candidate.interfaces:
            if not iface.cidr or not iface.enabled:
                continue
            expected = registry.get(norm_cidr(iface.cidr))
            actual = device_zone.get(iface.device)
            if actual == "wan" and expected == "branch":
                continue
            if (expected in USER_ZONES
                    and actual is not None
                    and actual != expected
                    and actual not in INFRASTRUCTURE_ZONES):
                out.append({
                    "type": "subnet_zone_overlap",
                    "subnet": norm_cidr(iface.cidr),
                    "expected_zone": expected,
                    "device": iface.device,
                    "device_zone": actual,
                    "message": (f"{iface.device} (zone {actual}) claims {norm_cidr(iface.cidr)} "
                                f"which belongs to zone {expected}: overlapping subnet"),
                })
        return out

    def evidence(self, ctx: AgentContext) -> list[Evidence]:
        return [
            Evidence(id=f"E-TOPO-{i + 1}", source=self.name,
                     kind=str(f.get("type", "topology")),
                     summary=str(f.get("message") or f.get("type")), data=f)
            for i, f in enumerate(ctx.topology_findings[:12])
        ]


class RoutingAgent(BaseAgent):
    name = "RoutingAgent"

    def execute(self, ctx: AgentContext) -> dict[str, Any]:
        base = TwinPayload.model_validate(ctx.base_payload_dict)
        internal_prefixes = {norm_cidr(s.cidr) for s in base.subnets}
        removals: list[dict[str, Any]] = []
        hijacks: list[dict[str, Any]] = []
        for change_item in ctx.route_changes:
            prefix = norm_cidr(change_item["prefix"])
            if change_item["change"] == "removed":
                removals.append(change_item)
                ctx.regressions.append(RegressionOut(
                    kind="ROUTE_MISSING",
                    severity="HIGH",
                    source=change_item["device"],
                    destination=change_item["prefix"],
                    message=(f"route {change_item['prefix']} via {change_item['next_hop']} "
                             f"[{change_item['protocol']}] removed at {change_item['device']}"),
                    detail=change_item,
                ))
            elif (prefix in internal_prefixes
                    and change_item["protocol"] in ("bgp", "static")
                    and int(change_item.get("distance", 99)) <= 20):
                hijacks.append(change_item)
                ctx.regressions.append(RegressionOut(
                    kind="ROUTE_HIJACK",
                    severity="CRITICAL",
                    source=change_item["device"],
                    destination=change_item["prefix"],
                    message=(f"internal prefix {change_item['prefix']} learned via "
                             f"{change_item['protocol']} next-hop {change_item['next_hop']} "
                             f"at {change_item['device']}: possible route leak/hijack"),
                    detail=change_item,
                ))
        return {"route_changes": len(ctx.route_changes), "removed": len(removals),
                "added_or_changed": len(ctx.route_changes) - len(removals),
                "hijacks": len(hijacks)}

    def evidence(self, ctx: AgentContext) -> list[Evidence]:
        return [
            Evidence(id=f"E-ROUTE-{i + 1}", source=self.name,
                     kind="routing_table_change",
                     summary=(f"{c['device']}: {c['change']} {c['prefix']} via "
                              f"{c['next_hop']} [{c['protocol']}]"), data=c)
            for i, c in enumerate(ctx.route_changes[:12])
        ]


class SecurityPolicyAgent(BaseAgent):
    name = "SecurityPolicyAgent"

    def execute(self, ctx: AgentContext) -> dict[str, Any]:
        base_map = {r["name"]: r for r in ctx.intent_results_base}
        new_violations = 0
        passed = 0
        for result in ctx.intent_results_candidate:
            if result["passed"]:
                passed += 1
                continue
            was_ok = base_map.get(result["name"], {}).get("passed", True)
            if result["itype"] == "route_exists":
                kind = "INTENT_ROUTE_MISSING"
                seg = False
            elif result["itype"] in ("must_not_reach", "only_from_subnet"):
                kind = "INTENT_MUST_NOT_REACH_VIOLATED"
                seg = ("isolated" in result["name"]
                       or "restricted" in result["name"])
            else:
                kind = "INTENT_MUST_REACH_BROKEN"
                seg = False
            if was_ok:
                new_violations += 1
                severity = "CRITICAL" if kind == "INTENT_MUST_NOT_REACH_VIOLATED" else "HIGH"
                ctx.regressions.append(RegressionOut(
                    kind=kind,
                    severity=severity,
                    source=result["name"],
                    destination=result.get("evidence", {}).get("dst", ""),
                    message=f"intent policy '{result['name']}' violated: {result['detail']}",
                    detail=result.get("evidence", {}),
                ))
                if seg:
                    ctx.regressions.append(RegressionOut(
                        kind="SEGMENTATION_VIOLATION",
                        severity="CRITICAL",
                        source=result["name"],
                        message=(f"segmentation control bypassed by change: "
                                 f"'{result['name']}' now permits forbidden traffic"),
                        detail=result.get("evidence", {}),
                    ))
        total = len(ctx.intent_results_candidate)
        compliance = round(passed * 100.0 / total, 1) if total else 100.0
        return {"intents_evaluated": total, "new_violations": new_violations,
                "compliance_pct": compliance}

    def evidence(self, ctx: AgentContext) -> list[Evidence]:
        failed = [r for r in ctx.intent_results_candidate if not r["passed"]]
        return [
            Evidence(id=f"E-SEC-{i + 1}", source=self.name, kind="intent_failure",
                     summary=f"{r['name']}: {r['detail']}", data=r)
            for i, r in enumerate(failed[:12])
        ]


class ReachabilityAgent(BaseAgent):
    name = "ReachabilityAgent"

    def execute(self, ctx: AgentContext) -> dict[str, Any]:
        service_endpoints = {
            s["endpoint_ip"]: s["name"]
            for s in (ctx.candidate_payload_dict or {}).get("services", [])
        }
        blocked_by_dst: Counter = Counter()
        gw_failures_by_src: set[str] = set()
        n_blocked = 0
        for entry in ctx.matrix_diff.get("newly_blocked", []):
            flow = entry["flow"]
            status = flow["status"]
            kind, severity = FLOW_KIND_MAP.get(status, ("UNKNOWN_BLOCK", "MEDIUM"))
            dst_ip = self._primary_ip_of(ctx, flow["dst"])
            src_host = flow["src"]
            dst_host = flow["dst"]
            if status == "host_down" and dst_ip in service_endpoints:
                kind, severity = "SERVICE_UNREACHABLE", "HIGH"
            ctx.regressions.append(RegressionOut(
                kind=kind,
                severity=severity,
                source=src_host,
                destination=dst_host,
                message=(f"{src_host}->{dst_host} {flow['proto']}/{flow['port']} BLOCKED "
                         f"[{status}] {entry.get('reason') or ''}".strip()),
                detail={"flow": flow, "reason": entry.get("reason")},
            ))
            blocked_by_dst[dst_host] += 1
            if status == "no_gateway":
                gw_failures_by_src.add(src_host)
            n_blocked += 1
        for entry in ctx.matrix_diff.get("asymmetric_new", []):
            ctx.regressions.append(RegressionOut(
                kind="ASYMMETRIC_ROUTE",
                severity="MEDIUM",
                source=entry["src"],
                destination=entry["dst"],
                message=(f"asymmetric routing {entry['src']}->{entry['dst']} "
                         f"{entry['proto']}/{entry['port']}: forward and reverse paths diverge"),
                detail={"forward_path": entry["path"]},
            ))
        endpoint_hosts = {
            d["name"] for d in (ctx.candidate_payload_dict or {}).get("devices", [])
            if d["role"] in HOST_ENDPOINT_ROLES
        }
        inbound_capacity = len(endpoint_hosts) or 1
        isolated: set[str] = set(gw_failures_by_src)
        for host, count in blocked_by_dst.items():
            if host in endpoint_hosts and count >= min(4, inbound_capacity):
                isolated.add(host)
        for host in sorted(isolated):
            ctx.regressions.append(RegressionOut(
                kind="HOST_ISOLATED",
                severity="HIGH",
                source=host,
                message=f"host {host} lost network connectivity across multiple flows",
                detail={},
            ))
        return {
            "candidate_probes": ctx.candidate_summary,
            "newly_blocked": n_blocked,
            "newly_allowed": len(ctx.matrix_diff.get("newly_allowed", [])),
            "asymmetric_new": len(ctx.matrix_diff.get("asymmetric_new", [])),
            "isolated_hosts": sorted(isolated),
        }

    @staticmethod
    def _primary_ip_of(ctx: AgentContext, device: str) -> str | None:
        for iface in (ctx.candidate_payload_dict or {}).get("interfaces", []):
            if iface["device"] == device and iface.get("cidr") and iface["enabled"]:
                return iface["cidr"].split("/")[0]
        return None

    def hypotheses(self, ctx: AgentContext) -> list[Hypothesis]:
        hs: list[Hypothesis] = []
        kinds = {r.kind for r in ctx.regressions}
        if "ACL_BLACKHOLE" in kinds:
            hs.append(Hypothesis(id="H-FLOW-ACL",
                                 statement="A new or modified ACL denies previously allowed flows",
                                 score=0.8))
        if "FW_BLOCKED_FLOW" in kinds:
            hs.append(Hypothesis(id="H-FLOW-FW",
                                 statement="A firewall policy change blocks required traffic",
                                 score=0.8))
        if kinds & {"NO_ROUTE", "ROUTE_MISSING", "ROUTE_LOOP"}:
            hs.append(Hypothesis(id="H-FLOW-RT",
                                 statement="Routing changes removed or misdirected required paths",
                                 score=0.75))
        if "GATEWAY_UNREACHABLE" in kinds:
            hs.append(Hypothesis(id="H-FLOW-GW",
                                 statement="Host gateway configuration or L2 adjacency broke",
                                 score=0.7))
        return hs
