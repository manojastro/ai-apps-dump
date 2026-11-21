"""Agent tests: evidence, hypotheses, RCA model contract, risk and remediation."""
from __future__ import annotations

import pytest

from app.agents.analysis_agents import (
    ChangeImpactAgent,
    RCAAgent,
    RemediationAgent,
    ValidationAgent,
)
from app.agents.network_agents import (
    ConfigAnalysisAgent,
    ReachabilityAgent,
    RoutingAgent,
    SecurityPolicyAgent,
    TopologyAgent,
)
from app.agents.base import AgentContext
from app.schemas.api import RootCauseAnalysis
from app.services.intents import IntentDef, evaluate_all
from app.services.twin import TwinRuntime, diff_matrices
from simulator.configs import DiffParser, apply_ops
from simulator.lab import build_lab_twin, SEED_INTENTS
from simulator.models import TwinPayload

BAD_DIFF = ("device fw-01\n"
            "+ip access-list APP-DB-GUARD\n"
            "+ deny tcp 10.30.0.0/24 10.30.1.0/24 eq 5432\n"
            "+ permit ip any any\n"
            "interface Vlan210\n"
            "+ ip access-group APP-DB-GUARD in\n")

ALL_AGENTS = [ConfigAnalysisAgent(), TopologyAgent(), RoutingAgent(),
              ReachabilityAgent(), SecurityPolicyAgent(), ChangeImpactAgent(),
              RCAAgent(), RemediationAgent()]


def build_ctx(diff_text: str = BAD_DIFF):
    twin = build_lab_twin()
    ops = DiffParser().parse(diff_text, twin)
    candidate, journal = apply_ops(twin, ops)
    base_rt = TwinRuntime(twin)
    cand_rt = TwinRuntime(candidate)
    intents = [IntentDef(name=s["name"], itype=s["itype"], params=s["params"])
               for s in SEED_INTENTS]
    return AgentContext(
        change_id=1,
        change_title="test",
        base_payload_dict=twin.to_dict(),
        ops=[o for o in ops if o.get("kind") != "noop"],
        journal=journal,
        candidate_payload_dict=candidate.to_dict(),
        matrix_diff=diff_matrices(base_rt.reachability_matrix(),
                                  cand_rt.reachability_matrix()),
        route_changes=_route_diff(twin.to_dict(), candidate.to_dict()),
        intent_results_base=[o.model_dump() for o in evaluate_all(intents, base_rt)],
        intent_results_candidate=[o.model_dump() for o in evaluate_all(intents, cand_rt)],
    )


def _route_diff(base_dict, cand_dict):
    from app.tools.network_tools import RoutingTableDiffInput, RoutingTableDiffTool

    return RoutingTableDiffTool().execute(
        RoutingTableDiffInput(base_payload=base_dict,
                              candidate_payload=cand_dict)).changes


def run_pipeline(ctx):
    reports = []
    for agent in ALL_AGENTS:
        reports.append(agent.run(ctx))
    reports.append(ValidationAgent().run(ctx))
    return reports


def test_all_agents_produce_reports_with_evidence_and_hypotheses() -> None:
    ctx = build_ctx()
    reports = run_pipeline(ctx)
    names = {r.agent for r in reports}
    assert {"ConfigAnalysisAgent", "TopologyAgent", "RoutingAgent", "ReachabilityAgent",
            "SecurityPolicyAgent", "ChangeImpactAgent", "RCAAgent", "RemediationAgent",
            "ValidationAgent"} == names
    evidence_total = sum(len(r.evidence) for r in reports)
    hypothesis_total = sum(len(r.hypotheses) for r in reports)
    assert evidence_total >= 1
    assert hypothesis_total >= 2
    for report in reports:
        assert report.duration_ms >= 0


def test_rca_pydantic_model_exact_contract() -> None:
    fields = set(RootCauseAnalysis.model_fields)
    assert fields == {"incident_id", "observations", "evidence", "hypotheses",
                      "rejected_hypotheses", "root_cause", "confidence",
                      "recommended_actions"}
    ctx = build_ctx()
    run_pipeline(ctx)
    assert isinstance(ctx.rca, RootCauseAnalysis)
    assert ctx.rca.incident_id == "CHG-1"
    assert 0.0 <= ctx.rca.confidence <= 1.0
    assert ctx.rca.rejected_hypotheses, "latent-issue hypothesis must be rejected"


def test_risk_bands_ordered_by_impact() -> None:
    benign = build_ctx("device core-01\n+ntp server 10.99.0.24 prefer\n")
    bad = build_ctx(BAD_DIFF)
    run_pipeline(benign)
    run_pipeline(bad)
    assert benign.risk is not None and bad.risk is not None
    assert benign.risk.band == "LOW"
    assert benign.risk.score < bad.risk.score
    assert bad.risk.band in ("HIGH", "CRITICAL")


def test_remediation_revalidates_clean() -> None:
    ctx = build_ctx(BAD_DIFF)
    run_pipeline(ctx)
    assert ctx.fix_validated is True
    fixed_runtime = TwinRuntime(TwinPayload.model_validate(
        ctx.fixed_candidate_payload_dict))
    base_runtime = TwinRuntime(TwinPayload.model_validate(ctx.base_payload_dict))
    diff = diff_matrices(base_runtime.reachability_matrix(),
                         fixed_runtime.reachability_matrix())
    assert not diff["newly_blocked"]
    assert not diff["newly_allowed"]


def test_security_agent_flags_segmentation_violations() -> None:
    ctx = build_ctx("device access-fin-01\nip access-list SEG-ISOLATE-FIN\n"
                    "- deny ip 10.50.20.0/24 10.40.10.0/24\n")
    run_pipeline(ctx)
    kinds = {r.kind for r in ctx.regressions}
    assert "INTENT_MUST_NOT_REACH_VIOLATED" in kinds
    assert "SEGMENTATION_VIOLATION" in kinds


def test_validation_agent_verdict_reflects_regressions() -> None:
    ctx = build_ctx(BAD_DIFF)
    verdict_report = run_pipeline(ctx)[-1]
    assert verdict_report.summary["verdict"] == "FAIL"
    clean = build_ctx("device core-01\n+ntp server 10.99.0.24 prefer\n")
    clean_report = run_pipeline(clean)[-1]
    assert clean_report.summary["verdict"] == "PASS"
