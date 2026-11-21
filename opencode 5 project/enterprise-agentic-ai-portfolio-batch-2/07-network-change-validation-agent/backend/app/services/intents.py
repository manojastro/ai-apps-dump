"""Declarative intent policy conversion and deterministic evaluation."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.services.twin import ENDPOINT_DEVICES, BLOCKED_STATUSES, MATRIX_PORTS, TwinRuntime
from simulator.models import ip_in_subnet, norm_cidr


class IntentDef(BaseModel):
    name: str
    itype: str
    params: dict[str, Any]
    severity: str = "HIGH"
    enabled: bool = True


class IntentOutcome(BaseModel):
    name: str
    itype: str
    passed: bool
    detail: str
    evidence: dict[str, Any] = {}


def representative_host(runtime: TwinRuntime, subnet: str) -> str | None:
    for dev_name in ENDPOINT_DEVICES:
        iface = runtime.primary_interface(dev_name)
        if iface and iface.cidr and ip_in_subnet(iface.cidr.split("/")[0], subnet):
            return dev_name
    return None


def evaluate_intent(intent: IntentDef, runtime: TwinRuntime) -> IntentOutcome:
    p = intent.params
    if intent.itype == "must_reach":
        return _eval_must_reach(intent, runtime, p)
    if intent.itype == "must_not_reach":
        return _eval_must_not_reach(intent, runtime, p)
    if intent.itype == "route_exists":
        return _eval_route_exists(intent, runtime, p)
    if intent.itype == "only_from_subnet":
        return _eval_only_from(intent, runtime, p)
    return IntentOutcome(name=intent.name, itype=intent.itype, passed=False,
                         detail=f"unknown intent type {intent.itype}")


def evaluate_all(intents: list[IntentDef], runtime: TwinRuntime) -> list[IntentOutcome]:
    return [evaluate_intent(i, runtime) for i in intents if i.enabled]


def _eval_must_reach(intent: IntentDef, runtime: TwinRuntime,
                     p: dict[str, Any]) -> IntentOutcome:
    src = representative_host(runtime, p["src_subnet"])
    if src is None:
        return IntentOutcome(name=intent.name, itype=intent.itype, passed=False,
                             detail=f"no source host found in {p['src_subnet']}")
    proto = p.get("proto", "tcp")
    port = p.get("port")
    probes = [(proto, port)] if port else list(MATRIX_PORTS)
    for proto_p, port_p in probes:
        result = runtime.simulate_flow(src, p["dst_ip"], proto_p, int(port_p or 80))
        if result.status != "allowed":
            return IntentOutcome(
                name=intent.name, itype=intent.itype, passed=False,
                detail=(f"{src}({p['src_subnet']})->{p['dst_ip']}/{proto_p}:{port_p}"
                        f" blocked: {result.status} ({result.reason})"),
                evidence={"src": src, "status": result.status, "reason": result.reason,
                          "path": result.path},
            )
    return IntentOutcome(name=intent.name, itype=intent.itype, passed=True,
                         detail=f"{src}->{p['dst_ip']} reachable as required",
                         evidence={"src": src})


def _eval_must_not_reach(intent: IntentDef, runtime: TwinRuntime,
                         p: dict[str, Any]) -> IntentOutcome:
    src = representative_host(runtime, p["src_subnet"])
    if src is None:
        return IntentOutcome(name=intent.name, itype=intent.itype, passed=False,
                             detail=f"no source host found in {p['src_subnet']}")
    leaks = []
    for proto, port in MATRIX_PORTS:
        result = runtime.simulate_flow(src, p["dst_ip"], proto, port)
        if result.status == "allowed":
            leaks.append(f"{proto}/{port}")
    if leaks:
        return IntentOutcome(
            name=intent.name, itype=intent.itype, passed=False,
            detail=(f"FORBIDDEN flow {src}({p['src_subnet']})->{p['dst_ip']} "
                    f"allowed on {', '.join(leaks)}"),
            evidence={"src": src, "leaking_ports": leaks},
        )
    return IntentOutcome(name=intent.name, itype=intent.itype, passed=True,
                         detail=f"{src}->{p['dst_ip']} correctly isolated",
                         evidence={"src": src})


def _eval_route_exists(intent: IntentDef, runtime: TwinRuntime,
                       p: dict[str, Any]) -> IntentOutcome:
    prefix = norm_cidr(p["prefix"])
    table = runtime.routing_table(p["device"])
    matches = [r for r in table if norm_cidr(r.prefix) == prefix]
    next_hops = sorted({r.next_hop or "connected" for r in matches})
    min_routes = int(p.get("min_routes", 1))
    protocols = sorted({r.protocol for r in matches})
    if len(next_hops) >= min_routes:
        return IntentOutcome(
            name=intent.name, itype=intent.itype, passed=True,
            detail=(f"{len(next_hops)} distinct paths to {prefix} at {p['device']} "
                    f"via {next_hops} [{','.join(protocols)}]"),
            evidence={"routes": [r.model_dump() for r in matches]},
        )
    return IntentOutcome(
        name=intent.name, itype=intent.itype, passed=False,
        detail=(f"path redundancy violation: {len(next_hops)} of required {min_routes} "
                f"paths exist for {prefix} at {p['device']} (have {next_hops})"),
        evidence={"routes": [r.model_dump() for r in matches]},
    )


def _eval_only_from(intent: IntentDef, runtime: TwinRuntime,
                    p: dict[str, Any]) -> IntentOutcome:
    allowed_subnets = [norm_cidr(s) for s in p["allowed_src_subnets"]]
    dst_owner = runtime.owner_of_ip(p["dst_ip"], include_down=True)
    violators: list[dict[str, str]] = []
    if dst_owner:
        dst_dev = dst_owner[0]
    else:
        dst_dev = ""
    for dev_name in ENDPOINT_DEVICES:
        if dev_name == dst_dev:
            continue
        iface = runtime.primary_interface(dev_name)
        if not iface or not iface.cidr:
            continue
        best = None
        for proto, port in MATRIX_PORTS:
            result = runtime.simulate_flow(dev_name, p["dst_ip"], proto, port)
            if result.status == "allowed":
                best = (proto, port)
                break
        if best is None:
            continue
        src_subnet = norm_cidr(iface.cidr)
        if src_subnet not in allowed_subnets:
            violators.append({"src": dev_name, "subnet": src_subnet,
                              "open_port": f"{best[0]}/{best[1]}"})
    if violators:
        return IntentOutcome(
            name=intent.name, itype=intent.itype, passed=False,
            detail=("mgmt exposure violation: reachable from outside allowed subnets: "
                    + ", ".join(f"{v['src']}({v['subnet']}) on {v['open_port']}"
                                for v in violators)),
            evidence={"violators": violators},
        )
    return IntentOutcome(name=intent.name, itype=intent.itype, passed=True,
                         detail="reachable only from permitted source subnets",
                         evidence={"allowed_src_subnets": allowed_subnets})
