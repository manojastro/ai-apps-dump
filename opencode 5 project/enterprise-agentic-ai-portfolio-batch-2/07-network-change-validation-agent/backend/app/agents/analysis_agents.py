"""Analysis agents: impact scoring, RCA, remediation and final validation report."""
from __future__ import annotations

from typing import Any

from app.agents.base import AgentContext, BaseAgent
from app.agents.network_agents import is_risky_op
from app.schemas.api import (
    Action,
    Evidence,
    Hypothesis,
    RiskAssessment,
    RootCauseAnalysis,
)
from simulator.configs import apply_ops
from simulator.models import TwinPayload


class ChangeImpactAgent(BaseAgent):
    name = "ChangeImpactAgent"

    WEIGHTS = {
        "routing": 5.0,
        "intent_blocked_flow": 10.0,
        "other_blocked_flow": 3.0,
        "opened_flow": 5.0,
        "security_violation": 15.0,
        "critical_service": 15.0,
        "blast_device": 1.0,
        "blast_app": 3.0,
    }
    CAPS = {"routing": 25.0, "reachability": 35.0, "security": 30.0, "blast": 15.0}

    def execute(self, ctx: AgentContext) -> dict[str, Any]:
        route_pts = min(self.CAPS["routing"],
                        self.WEIGHTS["routing"] * len(
                            [c for c in ctx.route_changes if c["change"] == "removed"]))
        blocked = [r for r in ctx.regressions if r.kind in (
            "ACL_BLACKHOLE", "FW_BLOCKED_FLOW", "NO_ROUTE", "MTU_VIOLATION",
            "GATEWAY_UNREACHABLE", "SERVICE_UNREACHABLE", "HOST_ISOLATED", "ROUTE_LOOP")]
        intent_blocked = [r for r in ctx.regressions
                          if r.kind in ("INTENT_MUST_REACH_BROKEN", "INTENT_ROUTE_MISSING")]
        opened = len(ctx.matrix_diff.get("newly_allowed", []))
        reach_pts = min(self.CAPS["reachability"],
                        self.WEIGHTS["intent_blocked_flow"] * len(intent_blocked)
                        + self.WEIGHTS["other_blocked_flow"] * len(blocked)
                        + self.WEIGHTS["opened_flow"] * opened) \
            if (blocked or opened or intent_blocked) else 0.0
        violations = [r for r in ctx.regressions if r.kind.endswith("VIOLATED")
                      or r.kind in ("SEGMENTATION_VIOLATION", "ROUTE_HIJACK",
                                    "SUBNET_OVERLAP")]
        affected_services = self._affected_critical_services(ctx)
        sec_pts = min(self.CAPS["security"],
                      self.WEIGHTS["security_violation"] * len(violations)
                      + self.WEIGHTS["critical_service"] * len(affected_services))
        devices = set(ctx.blast_radius_devices)
        for r in ctx.regressions:
            devices.add(r.source.split(":")[0])
            if r.destination:
                devices.add(r.destination.split("(")[0])
        apps_touched = len(affected_services)
        blast_pts = min(self.CAPS["blast"],
                        self.WEIGHTS["blast_device"] * len(devices)
                        + self.WEIGHTS["blast_app"] * min(apps_touched, 2))
        n_ops = len([op for op in ctx.ops if op.get("kind") != "noop"])
        rollback_pts = 2.0 if n_ops <= 2 else (5.0 if n_ops <= 5 else 9.0)
        evidence_count = (len(ctx.topology_findings) + len(ctx.route_changes)
                          + len(ctx.matrix_diff.get("newly_blocked", [])))
        confidence = min(0.98, 0.6 + 0.08 * min(4, evidence_count)) if evidence_count else 0.75
        confidence_penalty = round(10.0 * (1.0 - confidence), 1)
        raw = route_pts + reach_pts + sec_pts + blast_pts + rollback_pts + confidence_penalty
        score = round(min(100.0, raw), 1)
        band = ("LOW" if score < 20 else "MEDIUM" if score < 40
                else "HIGH" if score < 65 else "CRITICAL")
        components = {
            "routing_impact": round(route_pts, 1),
            "reachability_impact": round(reach_pts, 1),
            "security_violations": round(sec_pts, 1),
            "blast_radius": round(blast_pts, 1),
            "rollback_complexity": rollback_pts,
            "confidence_penalty": confidence_penalty,
            "affected_critical_services": float(len(affected_services)),
        }
        ctx.risk = RiskAssessment(score=score, band=band, components=components,
                                  confidence=confidence)
        return {"score": score, "band": band, "components": components,
                "confidence": confidence}

    @staticmethod
    def _affected_critical_services(ctx: AgentContext) -> set[str]:
        candidate = ctx.candidate_payload_dict or ctx.base_payload_dict
        ip_to_service = {}
        for svc in candidate.get("services", []):
            if svc.get("critical", True):
                ip_to_service[svc["endpoint_ip"]] = svc["name"]
        if not ip_to_service:
            return set()
        iface_ip = {}
        for iface in candidate.get("interfaces", []):
            if iface.get("cidr"):
                iface_ip[iface["device"]] = iface["cidr"].split("/")[0]
        affected: set[str] = set()
        for entry in ctx.matrix_diff.get("newly_blocked", []):
            dst_dev = entry["flow"]["dst"]
            dst_ip = iface_ip.get(dst_dev)
            if dst_ip and dst_ip in ip_to_service:
                affected.add(ip_to_service[dst_ip])
        return affected


class RCAAgent(BaseAgent):
    name = "RCAAgent"

    def execute(self, ctx: AgentContext) -> dict[str, Any]:
        observations = self._observations(ctx)
        hypotheses: list[Hypothesis] = []
        rejected: list[Hypothesis] = []
        evidence_items: list[Evidence] = []
        implicated_ops = self._implicated_ops(ctx)

        idx = 0
        for entry in ctx.journal:
            op_kind = entry.get("kind")
            if op_kind == "noop":
                continue
            idx += 1
            statement = f"config operation #{idx} ({self._describe(entry)}) caused the regressions"
            correlated = self._correlates(entry, ctx)
            hyp = Hypothesis(
                id=f"H-OP-{idx}",
                statement=statement,
                status="confirmed" if correlated else "rejected",
                score=round(0.55 + 0.4 * (1.0 if correlated else 0.0), 2),
                refuted_by=None if correlated else "no correlation with detected failures",
            )
            (hypotheses if correlated else rejected).append(hyp)
        latent = Hypothesis(
            id="H-LATENT",
            statement=("regressions stem from pre-existing network conditions "
                       "unrelated to this change"),
            status="rejected",
            score=0.05,
            refuted_by="baseline twin validated clean before candidate simulation",
        )
        rejected.append(latent)

        confirmed = sorted(hypotheses, key=lambda h: -h.score)
        if confirmed:
            root_cause = confirmed[0].statement
            confidence = min(0.97, 0.5 + 0.15 * len(confirmed))
        elif ctx.regressions:
            root_cause = "undetermined: regressions detected without a correlating config op"
            confidence = 0.3
        else:
            root_cause = "no regression detected; candidate preserves intended behavior"
            confidence = 0.9

        actions = [
            Action(name=f"revert-{i}", kind="config_revert",
                   command=line, rationale="undo implicated configuration operation")
            for i, line in enumerate(implicated_ops[:6])
        ]
        actions.append(Action(name="post-check", kind="verification",
                              command="re-run reachability matrix and intent suite on candidate",
                              rationale="confirm remediation before approval"))
        ctx.rca = RootCauseAnalysis(
            incident_id=f"CHG-{ctx.change_id}",
            observations=observations,
            evidence=evidence_items,
            hypotheses=hypotheses + rejected,
            rejected_hypotheses=rejected,
            root_cause=root_cause,
            confidence=confidence,
            recommended_actions=actions,
        )
        return {"root_cause": root_cause, "confidence": confidence,
                "hypotheses_confirmed": len(hypotheses),
                "hypotheses_rejected": len(rejected)}

    @staticmethod
    def _describe(entry: dict[str, Any]) -> str:
        kind = entry.get("kind")
        dev = entry.get("device") or entry.get("acl") or entry.get("service") or ""
        extra = entry.get("iface") or entry.get("prefix") or entry.get("seq") or ""
        return f"{kind} on {dev} {extra}".strip()

    @staticmethod
    def _correlates(entry: dict[str, Any], ctx: AgentContext) -> bool:
        if not ctx.regressions:
            return False
        return entry.get("kind") not in (None, "noop")

    def _implicated_ops(self, ctx: AgentContext) -> list[str]:
        return [self._describe(entry) for entry in ctx.journal
                if entry.get("kind") not in (None, "noop")]

    def _observations(self, ctx: AgentContext) -> list[str]:
        obs = [
            f"candidate built from {len(ctx.ops)} parsed operations",
            f"{len(ctx.matrix_diff.get('newly_blocked', []))} flows newly blocked",
            f"{len(ctx.matrix_diff.get('newly_allowed', []))} flows newly allowed",
            f"{len(ctx.route_changes)} routing table changes",
            f"{len(ctx.topology_findings)} topology findings",
        ]
        for reg in ctx.regressions[:5]:
            obs.append(reg.message)
        return obs


class RemediationAgent(BaseAgent):
    name = "RemediationAgent"

    INVERSE_TEMPLATES = {
        "interface": None,
        "gateway": None,
        "acl_rule": None,
        "firewall_policy": None,
        "static_route": None,
        "ospf_network": None,
        "bgp_prefix": None,
        "service_state": None,
        "acl_delete": None,
    }

    def execute(self, ctx: AgentContext) -> dict[str, Any]:
        inverse_ops = invert_journal(ctx.journal)
        if not inverse_ops:
            return {"proposed_fix": False, "reason": "no reversible operations"}
        fixed_payload, fix_journal = apply_ops(
            TwinPayload.model_validate(ctx.candidate_payload_dict), inverse_ops
        )
        ctx.proposed_fix_ops = inverse_ops
        ctx.proposed_fix_diff = render_fix_diff(inverse_ops)
        ctx.fixed_candidate_payload_dict = fixed_payload.to_dict()
        from app.services.twin import TwinRuntime, diff_matrices
        base_rt = TwinRuntime(TwinPayload.model_validate(ctx.base_payload_dict))
        cand_rt = TwinRuntime(TwinPayload.model_validate(fixed_payload.to_dict()))
        diff = diff_matrices(base_rt.reachability_matrix(), cand_rt.reachability_matrix())
        remaining = (len(diff["newly_blocked"]) + len(diff["newly_allowed"])
                     + len(diff["asymmetric_new"]))
        ctx.fix_validated = remaining == 0
        return {"fix_ops": len(inverse_ops), "remaining_probes_changed": remaining,
                "fix_validated": ctx.fix_validated}


def invert_journal(journal: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ops: list[dict[str, Any]] = []
    for entry in journal:
        inv = _invert_entry(entry)
        if inv:
            ops.append(inv)
    return ops


def _invert_entry(e: dict[str, Any]) -> dict[str, Any] | None:
    kind = e["kind"]
    if kind == "noop":
        return None
    before = e.get("before")
    after = e.get("after")
    if kind == "interface":
        if before == after:
            return None
        return {"kind": "interface", "device": e["device"], "iface": e["iface"],
                "attr": e["attr"], "value": before}
    if kind == "gateway":
        return ({"kind": "gateway", "device": e["device"], "gateway": before}
                if before else None)
    if kind == "acl_rule":
        target = after or before
        if not target:
            return None
        action, proto, src, dst, port = target
        return {"kind": "acl_rule", "acl": e["acl"], "action": action, "proto": proto,
                "src": src, "dst": dst, "port": port,
                "remove": bool(after)}
    if kind == "acl_delete":
        return None
    if kind == "static_route":
        if after:
            return {"kind": "static_route", "device": e["device"], "prefix": e["prefix"],
                    "next_hop": after, "distance": 1, "remove": True}
        if before:
            return {"kind": "static_route", "device": e["device"], "prefix": e["prefix"],
                    "next_hop": before, "distance": 1, "remove": False}
        return None
    if kind == "ospf_network":
        return {"kind": "ospf_network", "device": e["device"], "prefix": e["prefix"],
                "remove": bool(after)}
    if kind == "bgp_prefix":
        peer = e.get("peer")
        if peer is None and (after or before):
            return None
        if after:
            return {"kind": "bgp_prefix", "device": e["device"], "peer": peer,
                    "prefix": e["prefix"], "local_as": e.get("local_as", 65000),
                    "remove": True}
        if before:
            return {"kind": "bgp_prefix", "device": e["device"], "peer": peer,
                    "prefix": e["prefix"], "local_as": e.get("local_as", 65000),
                    "remove": False}
        return None
    if kind == "firewall_policy":
        if after:
            return {"kind": "firewall_policy", "device": e["device"], "seq": e["seq"],
                    "remove": True}
        if before:
            b = before
            return {"kind": "firewall_policy", "device": e["device"], "seq": b["seq"],
                    "action": b["action"], "src": b["src"], "dst": b["dst"],
                    "proto": b["proto"], "port": b.get("dst_port"),
                    "label": b.get("label", ""), "remove": False}
        return None
    if kind == "service_state":
        return {"kind": "service_state", "service": e["service"],
                "enabled": bool(before) if before is not None else True}
    return None


def render_fix_diff(inverse_ops: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    seen_acls: set[str] = set()
    current_dev: str | None = None
    for op in inverse_ops:
        dev = op.get("device") or ""
        if dev and dev != current_dev:
            lines.append(f"device {dev}")
            current_dev = dev
        kind = op["kind"]
        if kind == "interface":
            lines.append(f"interface {op['iface']}")
            attr = op["attr"]
            value = op.get("value")
            if attr == "enabled":
                lines.append("+ no shutdown" if value else "+ shutdown")
            elif attr == "cidr" and value:
                lines.append(f"+ ip address {value}")
            elif attr == "mtu" and value:
                lines.append(f"+ mtu {value}")
            elif attr == "vlan" and value:
                lines.append(f"+ switchport access vlan {value}")
        elif kind == "gateway" and op.get("gateway"):
            lines.append(f"+ ip default-gateway {op['gateway']}")
        elif kind == "acl_rule":
            if op["acl"] not in seen_acls:
                lines.append(f"ip access-list {op['acl']}")
                seen_acls.add(op["acl"])
            port = f" eq {op['port']}" if op.get("port") else ""
            sign = "-" if op.get("remove") else "+"
            lines.append(f"{sign} {op['action']} {op['proto']} {op['src']} {op['dst']}{port}")
        elif kind == "static_route":
            if op.get("remove"):
                lines.append(f"- ip route {op['prefix']} {op['next_hop']}")
            else:
                lines.append(f"+ ip route {op['prefix']} {op['next_hop']} {op['distance']}")
        elif kind == "ospf_network":
            lines.append("router ospf 1")
            sign = "-" if op.get("remove") else "+"
            lines.append(f"{sign} network {op['prefix']} area 0")
        elif kind == "bgp_prefix":
            lines.append(f"router bgp {op.get('local_as', 65000)}")
            sign = "-" if op.get("remove") else "+"
            lines.append(f"{sign} neighbor {op['peer']} advertised-prefixes {op['prefix']}")
        elif kind == "firewall_policy":
            if op.get("remove"):
                lines.append(f"- firewall policy {op['seq']}")
            else:
                port = f" eq {op['port']}" if op.get("port") else ""
                lines.append(f"+ firewall policy {op['seq']} {op['action']} {op['src']} "
                             f"{op['dst']} {op['proto']}{port}")
        elif kind == "service_state":
            lines.append(f"service {op['service']}")
            lines.append("+ enable" if op.get("enabled") else "+ shutdown")
    return "\n".join(lines) + "\n"


class ValidationAgent(BaseAgent):
    name = "ValidationAgent"

    def execute(self, ctx: AgentContext) -> dict[str, Any]:
        blocking_kinds = {"CRITICAL"}
        high_or_critical = [r for r in ctx.regressions if r.severity.upper() in
                            {"HIGH", "CRITICAL"} | blocking_kinds]
        failed_intents = [r for r in ctx.intent_results_candidate if not r["passed"]]
        verdict = "FAIL" if high_or_critical or failed_intents else "PASS"
        return {
            "verdict": verdict,
            "regressions": len(ctx.regressions),
            "high_or_critical": len(high_or_critical),
            "failed_intents": len(failed_intents),
            "risk_band": ctx.risk.band if ctx.risk else "UNKNOWN",
            "fix_available": bool(ctx.proposed_fix_diff),
            "fix_validated": ctx.fix_validated,
        }
