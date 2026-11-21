"""Validation engine tests: intent evaluation, matrix diff, risk bands, state gate."""
from __future__ import annotations

import pytest

from app.agents.analysis_agents import ChangeImpactAgent
from app.agents.base import AgentContext
from app.services.intents import IntentDef, evaluate_all
from app.services.state_machine import IllegalTransition, transition
from app.services.twin import TwinRuntime, diff_matrices
from simulator.configs import DiffParser, apply_ops
from simulator.lab import build_lab_twin, SEED_INTENTS


def intents_from_seed() -> list[IntentDef]:
    return [IntentDef(name=s["name"], itype=s["itype"], params=s["params"],
                      severity=s.get("severity", "HIGH")) for s in SEED_INTENTS]


def test_baseline_intent_compliance_is_100_percent() -> None:
    runtime = TwinRuntime(build_lab_twin())
    outcomes = evaluate_all(intents_from_seed(), runtime)
    assert len(outcomes) == 11
    failed = [o for o in outcomes if not o.passed]
    assert not failed


def test_dns_outage_breaks_three_intents() -> None:
    twin = build_lab_twin()
    for iface in twin.interfaces:
        if iface.device == "dns-01":
            iface.enabled = False
    outcomes = {o.name: o for o in evaluate_all(intents_from_seed(),
                                                TwinRuntime(twin))}
    for name in ("app-to-dns", "finance-to-dns", "branch-to-dns"):
        assert outcomes[name].passed is False


def test_bgp_withdrawal_breaks_route_redundancy_only() -> None:
    twin = build_lab_twin()
    ops = DiffParser().parse(
        "device core-01\nrouter bgp 65000\n"
        "- neighbor 10.200.3.5 advertised-prefixes 10.80.0.0/24\n", twin)
    candidate, _ = apply_ops(twin, ops)
    outcomes = {o.name: o for o in evaluate_all(intents_from_seed(),
                                                TwinRuntime(candidate))}
    assert outcomes["branch-primary-and-backup"].passed is False
    reachability_intents = [n for n, o in outcomes.items()
                            if o.itype == "must_reach" and not o.passed]
    assert not reachability_intents


def test_diff_matrices_classification() -> None:
    def row(src, dst, status, asym=False):
        return {"src": src, "dst": dst, "proto": "tcp", "port": 22,
                "status": status, "reason": None, "path": [], "asymmetric": asym}

    base = [row("a", "b", "allowed"), row("a", "c", "denied_fw"),
            row("b", "a", "allowed")]
    cand = [row("a", "b", "denied_acl"), row("a", "c", "allowed"),
            row("b", "a", "allowed", asym=True)]
    diff = diff_matrices(base, cand)
    assert len(diff["newly_blocked"]) == 1
    assert diff["newly_blocked"][0]["flow"]["src"] == "a"
    assert len(diff["newly_allowed"]) == 1
    assert len(diff["asymmetric_new"]) == 1
    assert diff["total_probes"] == 3


def test_risk_band_boundaries() -> None:
    from app.agents.network_agents import (
        ConfigAnalysisAgent,
        ReachabilityAgent,
        RoutingAgent,
        SecurityPolicyAgent,
        TopologyAgent,
    )
    from app.tools.network_tools import RoutingTableDiffInput, RoutingTableDiffTool

    twin = build_lab_twin()
    empty = AgentContext(change_id=1, change_title="t",
                         base_payload_dict=twin.to_dict())
    ChangeImpactAgent().execute(empty)
    assert empty.risk.band == "LOW"
    assert empty.risk.score < 20

    ops = DiffParser().parse(
        "device fw-01\n+ip access-list G\n"
        "+ deny tcp 10.30.0.0/24 10.30.1.0/24 eq 5432\n"
        "+ permit ip any any\ninterface Vlan210\n"
        "+ ip access-group G in\n", twin)
    candidate, journal = apply_ops(twin, ops)
    base_rt = TwinRuntime(twin)
    cand_rt = TwinRuntime(candidate)
    intents = intents_from_seed()
    ctx = AgentContext(
        change_id=1,
        change_title="t",
        base_payload_dict=twin.to_dict(),
        ops=[o for o in ops if o.get("kind") != "noop"],
        journal=journal,
        candidate_payload_dict=candidate.to_dict(),
        matrix_diff=diff_matrices(base_rt.reachability_matrix(),
                                  cand_rt.reachability_matrix()),
        route_changes=RoutingTableDiffTool().execute(
            RoutingTableDiffInput(base_payload=twin.to_dict(),
                                  candidate_payload=candidate.to_dict())).changes,
        intent_results_base=[o.model_dump() for o in evaluate_all(intents, base_rt)],
        intent_results_candidate=[o.model_dump() for o in
                                  evaluate_all(intents, cand_rt)],
    )
    for agent in (ConfigAnalysisAgent(), TopologyAgent(), RoutingAgent(),
                  ReachabilityAgent(), SecurityPolicyAgent()):
        agent.run(ctx)
    ChangeImpactAgent().execute(ctx)
    assert ctx.risk.band in ("HIGH", "CRITICAL")


def test_state_machine_gate_rejects_shortcuts() -> None:
    with pytest.raises(IllegalTransition):
        transition("AWAITING_APPROVAL", "EXECUTING")
    with pytest.raises(IllegalTransition):
        transition("VALIDATING", "COMPLETED")
    with pytest.raises(IllegalTransition):
        transition("ROLLED_BACK", "APPROVED")
