"""Deterministic validation pipeline orchestrating tools and agents."""
from __future__ import annotations

import time
from typing import Any

from sqlalchemy.orm import Session

from app.agents.analysis_agents import (
    ChangeImpactAgent,
    RCAAgent,
    RemediationAgent,
    ValidationAgent,
)
from app.agents.base import AgentContext, BaseAgent
from app.agents.network_agents import (
    ConfigAnalysisAgent,
    ReachabilityAgent,
    RoutingAgent,
    SecurityPolicyAgent,
    TopologyAgent,
)
from app.db import session_scope
from app.models.entities import IntentResult, Regression, ValidationRun
from app.repositories.repo import (
    AuditRepository,
    ChangeRepository,
    DiffRepository,
    InvestigationRepository,
    IntentRepository,
    KpiRepository,
    SnapshotRepository,
)
from app.services.intents import IntentDef, evaluate_all
from app.services.llm import LLM
from app.services.metrics import METRICS
from app.services.state_machine import IllegalTransition, transition
from app.services.twin import TwinRuntime, diff_matrices
from app.tools.network_tools import (
    ApplyChangeTool,
    RollbackTool,
    RoutingTableDiffInput,
    RoutingTableDiffTool,
)
from simulator.configs import DiffParser, apply_ops
from simulator.lab import SEED_INTENTS, build_lab_twin
from simulator.models import TwinPayload

AGENTS: list[BaseAgent] = [
    ConfigAnalysisAgent(),
    TopologyAgent(),
    RoutingAgent(),
    ReachabilityAgent(),
    SecurityPolicyAgent(),
    ChangeImpactAgent(),
    RCAAgent(),
    RemediationAgent(),
]


def seed_network(session: Session) -> int:
    snaps = SnapshotRepository(session)
    existing = snaps.current()
    payload = build_lab_twin().to_dict()
    if existing is not None:
        snap = snaps.create(version="CURRENT", payload=payload, is_current=True)
    else:
        snap = snaps.create(version="CURRENT", payload=payload, is_current=True)
    ensure_intents(session)
    return snap.id


def ensure_intents(session: Session) -> None:
    repo = IntentRepository(session)
    for spec in SEED_INTENTS:
        repo.upsert(name=spec["name"], itype=spec["itype"], params=spec["params"],
                    severity=spec.get("severity", "HIGH"))


def load_intents(session: Session) -> list[IntentDef]:
    repo = IntentRepository(session)
    return [
        IntentDef(name=row.name, itype=row.itype, params=row.params,
                  severity=row.severity, enabled=bool(row.enabled))
        for row in repo.all_enabled()
    ]


def _current_payload(session: Session) -> tuple[int, dict[str, Any]]:
    snap = SnapshotRepository(session).current()
    if snap is None:
        seed_network(session)
        snap = SnapshotRepository(session).current()
    assert snap is not None
    return snap.id, snap.payload


def run_validation(session: Session, change_id: int) -> ValidationRun:
    """Execute the full pipeline for one change and persist the run."""
    started = time.perf_counter()
    changes = ChangeRepository(session)
    change = changes.get(change_id)
    if change is None:
        raise ValueError(f"change {change_id} not found")
    try:
        change.status = transition(change.status, "VALIDATING")
    except IllegalTransition as exc:
        raise exc

    snapshot_id, base_payload_dict = _current_payload(session)
    parser = DiffParser()
    base_payload = TwinPayload.model_validate(base_payload_dict)
    ops = parser.parse(change.config_diff, base_payload)
    stored_fix = list(change.fix_ops_json or [])
    remediation_applied = bool(stored_fix)
    if remediation_applied:
        ops = ops + [op for op in stored_fix if op.get("kind") != "noop"]
    candidate_payload, journal = apply_ops(base_payload, ops)

    snaps = SnapshotRepository(session)
    cand_snap = snaps.create(version="CANDIDATE", payload=candidate_payload.to_dict(),
                             is_current=False, change_id=change.id)
    change.candidate_snapshot_id = cand_snap.id
    DiffRepository(session).create(change.id, change.config_diff,
                                   [op for op in ops if op.get("kind") != "noop"])

    intents = load_intents(session)
    base_rt = TwinRuntime(base_payload)
    cand_rt = TwinRuntime(candidate_payload)
    base_rows = base_rt.reachability_matrix()
    cand_rows = cand_rt.reachability_matrix()
    matrix_diff = diff_matrices(base_rows, cand_rows)
    route_changes = _route_diff(base_payload_dict, candidate_payload.to_dict())
    intent_base = [o.model_dump() for o in evaluate_all(intents, base_rt)]
    intent_cand = [o.model_dump() for o in evaluate_all(intents, cand_rt)]

    ctx = AgentContext(
        change_id=change.id,
        change_title=change.title,
        base_payload_dict=base_payload_dict,
        ops=[op for op in ops if op.get("kind") != "noop"],
        journal=journal,
        candidate_payload_dict=candidate_payload.to_dict(),
        base_summary={"blocked": sum(1 for r in base_rows if r["status"] != "allowed"),
                      "total": len(base_rows)},
        candidate_summary={"blocked": sum(1 for r in cand_rows
                                          if r["status"] != "allowed"),
                           "total": len(cand_rows)},
        matrix_diff=matrix_diff,
        route_changes=route_changes,
        intent_results_base=intent_base,
        intent_results_candidate=intent_cand,
    )

    stage_reports = []
    ctx.stages.append({"stage": "parse_diff", "ops": len(ctx.ops)})
    if remediation_applied:
        ctx.stages.append({"stage": "apply_stored_remediation",
                           "ops": len(stored_fix)})
    ctx.stages.append({"stage": "build_candidate", "journal_entries": len(journal)})
    ctx.stages.append({"stage": "reachability_matrix",
                       "probes": len(cand_rows),
                       "newly_blocked": len(matrix_diff["newly_blocked"])})

    pipeline_agents = [a for a in AGENTS
                       if not (remediation_applied
                               and isinstance(a, RemediationAgent))]
    for agent in pipeline_agents:
        report = agent.run(ctx)
        stage_reports.append(report)
        ctx.stages.append({"stage": f"agent:{report.agent}",
                           "duration_ms": report.duration_ms,
                           **{k: v for k, v in report.summary.items()
                              if isinstance(v, (int, float, str, bool))}})

    if ctx.fix_validated and ctx.fixed_candidate_payload_dict is not None:
        fixed_snap = snaps.create(version="CANDIDATE",
                                  payload=ctx.fixed_candidate_payload_dict,
                                  is_current=False, change_id=change.id)
        change.candidate_snapshot_id = fixed_snap.id
        ctx.stages.append({"stage": "adopt_fixed_candidate",
                           "snapshot_id": fixed_snap.id})
    if not remediation_applied and ctx.fix_validated and ctx.proposed_fix_ops:
        change.fix_ops_json = ctx.proposed_fix_ops

    validator = ValidationAgent()
    final_report = validator.run(ctx)
    stage_reports.append(final_report)
    verdict = str(final_report.summary["verdict"])
    duration_ms = int((time.perf_counter() - started) * 1000)

    run = ValidationRun(
        change_id=change.id,
        verdict=verdict,
        risk_score=ctx.risk.score,
        risk_band=ctx.risk.band,
        confidence=ctx.risk.confidence,
        duration_ms=duration_ms,
        summary={
            "stages": ctx.stages,
            "matrix_diff": {
                "newly_blocked": len(matrix_diff["newly_blocked"]),
                "newly_allowed": len(matrix_diff["newly_allowed"]),
                "asymmetric_new": len(matrix_diff["asymmetric_new"]),
                "total_probes": matrix_diff["total_probes"],
                "newly_blocked_detail": matrix_diff["newly_blocked"][:25],
                "newly_allowed_detail": matrix_diff["newly_allowed"][:15],
            },
            "route_changes": route_changes[:50],
            "topology_findings": ctx.topology_findings[:20],
            "blast_radius_devices": ctx.blast_radius_devices,
            "risk_components": ctx.risk.components,
            "fix_available": bool(ctx.proposed_fix_diff),
            "fix_validated": ctx.fix_validated,
        },
        narration="",
    )
    session.add(run)
    session.flush()

    inv_repo = InvestigationRepository(session)
    for report in stage_reports:
        inv_rows = inv_repo.create(run.id, report.agent, report.duration_ms, report.summary)
        for ev in report.evidence:
            inv_repo.evidence(inv_rows.id, ev.kind, ev.source,
                              {"summary": ev.summary, "data": ev.data})
        for hy in report.hypotheses:
            inv_repo.hypothesis(inv_rows.id, hy.statement, hy.status, hy.score, hy.refuted_by)

    for reg in ctx.regressions:
        session.add(Regression(run_id=run.id, kind=reg.kind, severity=reg.severity,
                               source=reg.source, destination=reg.destination,
                               message=reg.message, detail=reg.detail))
    passed_count = sum(1 for r in intent_cand if r["passed"])
    total_intents = len(intent_cand)
    for result in intent_cand:
        session.add(IntentResult(run_id=run.id, intent_name=result["name"],
                                 passed=result["passed"], detail=result))
    if ctx.rca is not None:
        InvestigationRepository(session).rca(run.id, ctx.rca.incident_id,
                                             ctx.rca.model_dump())
    if not remediation_applied:
        change.proposed_fix_diff = ctx.proposed_fix_diff
        change.fix_validated = ctx.fix_validated
    else:
        change.fix_validated = True
    change.diff_ops = ctx.ops
    change.risk_score = ctx.risk.score
    change.risk_band = ctx.risk.band

    narration = LLM.narrate_validation({
        "change_id": change.id,
        "verdict": verdict,
        "risk": {"band": ctx.risk.band},
        "regressions": [r.model_dump() for r in ctx.regressions],
        "intents": intent_cand,
        "proposed_fix_diff": ctx.proposed_fix_diff,
        "fix_validated": ctx.fix_validated,
        "rca": ctx.rca.model_dump() if ctx.rca else {},
    })
    run.narration = narration

    new_status = transition("VALIDATING", "AWAITING_APPROVAL")
    change.status = new_status
    AuditRepository(session).event(
        "change", change.id, "validated", detail={
            "run_id": run.id, "verdict": verdict, "risk": ctx.risk.band,
            "regressions": len(ctx.regressions),
        })
    METRICS.incr("validations_total", {"verdict": verdict})
    METRICS.incr("regressions_detected_total", value=len(ctx.regressions))
    METRICS.set_gauge("last_validation_duration_ms", duration_ms)

    compliance = round(passed_count * 100.0 / total_intents, 1) if total_intents else 100.0
    KpiRepository(session).save(_kpi_metrics(session, run.id, duration_ms, compliance))

    session.flush()
    return run


def _route_diff(base_dict: dict[str, Any], cand_dict: dict[str, Any]) -> list[dict[str, Any]]:
    tool = RoutingTableDiffTool()
    output = tool.execute(RoutingTableDiffInput(base_payload=base_dict,
                                                candidate_payload=cand_dict))
    return output.changes


def _kpi_metrics(session: Session, run_id: int, duration_ms: int,
                 compliance_pct: float) -> dict[str, Any]:
    runs = session.query(ValidationRun).count()
    regressions = session.query(Regression).filter(Regression.run_id == run_id).count()
    unsafe = session.query(ValidationRun).filter(
        ValidationRun.verdict == "FAIL").count()
    return {
        "validation_runs_total": runs,
        "regressions_in_run": regressions,
        "failed_validations_total": unsafe,
        "intent_compliance_pct": compliance_pct,
        "last_validation_duration_ms": duration_ms,
    }


def submit_change(session: Session, title: str, config_diff: str,
                  requested_by: str = "netops", fault_name: str | None = None):
    change = ChangeRepository(session).create(title=title, config_diff=config_diff,
                                              requested_by=requested_by,
                                              fault_name=fault_name)
    AuditRepository(session).event("change", change.id, "submitted", actor=requested_by)
    run_validation(session, change.id)
    session.refresh(change)
    return change


def approve_change(session: Session, change_id: int, approver: str, comment: str,
                   justification: str = ""):
    changes = ChangeRepository(session)
    audit = AuditRepository(session)
    change = changes.get(change_id)
    if change is None:
        raise ValueError("change not found")
    if change.status != "AWAITING_APPROVAL":
        raise IllegalTransition(change.status, "APPROVED")
    if change.risk_band in ("HIGH", "CRITICAL") and not justification:
        raise ValueError("justification required for HIGH or CRITICAL risk changes")
    change.status = transition(change.status, "APPROVED")
    change.approved_by = approver
    audit.approval(change.id, approver, "APPROVED", comment or justification,
                   "AWAITING_APPROVAL", "APPROVED")
    return change


def reject_change(session: Session, change_id: int, actor: str, reason: str = ""):
    changes = ChangeRepository(session)
    change = changes.get(change_id)
    if change is None:
        raise ValueError("change not found")
    previous = change.status
    change.status = transition(change.status, "REJECTED")
    AuditRepository(session).approval(change.id, actor, "REJECTED", reason,
                                      previous, "REJECTED")
    METRICS.incr("unsafe_changes_prevented_total")
    return change


def apply_change(session: Session, change_id: int):
    """Approval-gated apply followed by post-apply verification."""
    changes = ChangeRepository(session)
    audit = AuditRepository(session)
    change = changes.get(change_id)
    if change is None:
        raise ValueError("change not found")
    change.status = transition(change.status, "EXECUTING")
    session.commit()
    tool = ApplyChangeTool()
    result = tool.run({"change_id": change.id}, change_id=change.id, approved=True)
    session.refresh(change)
    change.status = transition(change.status, "VERIFYING")

    snap = SnapshotRepository(session).current()
    runtime = TwinRuntime(TwinPayload.model_validate(snap.payload))
    intents = load_intents(session)
    outcomes = evaluate_all(intents, runtime)
    all_pass = all(o.passed for o in outcomes)
    if all_pass:
        change.status = transition(change.status, "COMPLETED")
        audit.event("change", change.id, "verification_passed")
    else:
        failed_names = [o.name for o in outcomes if not o.passed]
        audit.event("change", change.id, "verification_failed",
                    detail={"failed_intents": failed_names})
        rollback_change(session, change.id, actor="auto-rollback",
                        reason="post-apply verification failed")
    session.commit()
    session.refresh(change)
    return {"applied": True, "status": change.status}


def rollback_change(session: Session, change_id: int, actor: str = "netops",
                    reason: str = ""):
    changes = ChangeRepository(session)
    change = changes.get(change_id)
    if change is None:
        raise ValueError("change not found")
    previous_status = change.status
    change.status = transition(change.status, "ROLLED_BACK")
    session.commit()
    tool = RollbackTool()
    result = tool.run({"change_id": change.id}, change_id=change.id, approved=True)
    AuditRepository(session).approval(change_id, actor, "ROLLED_BACK", reason,
                                      previous_status, "ROLLED_BACK")
    METRICS.incr("rollbacks_total")
    session.refresh(change)
    return result
