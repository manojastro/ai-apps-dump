"""Network twin API: snapshots, faults, topology, reachability, intents, KPIs."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.entities import KpiSnapshot, Regression, SnapshotModel, ValidationRun
from app.repositories.repo import (
    ChangeRepository,
    IntentRepository,
    RunRepository,
    SnapshotRepository,
)
from app.schemas.api import (
    FaultSubmitRequest,
    ReachabilityOut,
    ReachabilityRow,
    SnapshotSeedRequest,
    TopologyEdge,
    TopologyNode,
    TopologyOut,
)
from app.services.intents import IntentDef, evaluate_all
from app.services.metrics import METRICS
from app.services.twin import TwinRuntime
from simulator.faults import FAULT_CATALOG
from simulator.models import TwinPayload, norm_cidr

router = APIRouter(prefix="/network", tags=["network"])
views = APIRouter(tags=["network-views"])


@router.post("/snapshot")
def post_snapshot(request: SnapshotSeedRequest | None = None,
                  session: Session = Depends(get_db)) -> dict[str, Any]:
    from app.services.validation import seed_network

    if request and request.payload:
        payload = TwinPayload.model_validate(request.payload).to_dict()
        snap = SnapshotRepository(session).create(version="CURRENT", payload=payload,
                                                  is_current=True)
    else:
        snap_id = seed_network(session)
        snap = SnapshotRepository(session).get(snap_id)
        assert snap is not None
    METRICS.incr("snapshots_seeded_total")
    return {"snapshot_id": snap.id, "version": "CURRENT",
            "devices": len(snap.payload.get("devices", []))}


@router.get("/snapshot")
def get_snapshot(session: Session = Depends(get_db)) -> dict[str, Any]:
    snap = SnapshotRepository(session).current()
    if snap is None:
        raise HTTPException(status_code=404, detail="no snapshot found; seed first")
    return {"snapshot_id": snap.id, "version": snap.version,
            "payload": snap.payload}


@router.get("/faults")
def list_faults() -> dict[str, Any]:
    catalog = FAULT_CATALOG.all_faults()
    return {"faults": [
        {"name": spec.name, "title": spec.title, "description": spec.description,
         "category": spec.category, "benign": spec.benign}
        for spec in catalog.values()
    ]}


@router.post("/faults/{name}")
def inject_fault(name: str, request: FaultSubmitRequest | None = None,
                 session: Session = Depends(get_db)) -> dict[str, Any]:
    from app.services.validation import submit_change

    try:
        spec = FAULT_CATALOG.get(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"unknown fault '{name}'")
    requested_by = request.requested_by if request else "netops"
    change = submit_change(session, title=f"[fault:{name}] {spec.title}",
                           config_diff=spec.diff_text, requested_by=requested_by,
                           fault_name=name)
    run = RunRepository(session).latest_for_change(change.id)
    regression_count = 0
    if run is not None:
        regression_count = session.query(Regression).filter(
            Regression.run_id == run.id).count()
    return {
        "change_id": change.id,
        "status": change.status,
        "risk_band": change.risk_band,
        "risk_score": change.risk_score,
        "verdict": run.verdict if run else None,
        "regressions": regression_count,
    }


@views.get("/topology", response_model=TopologyOut)
def topology(change_id: int | None = None,
             session: Session = Depends(get_db)) -> TopologyOut:
    payload = _payload_for(session, change_id)
    twin = TwinPayload.model_validate(payload)
    nodes = [TopologyNode(name=d.name, role=d.role, zone=d.zone, enabled=d.enabled)
             for d in twin.devices]
    members_by_subnet: dict[str, list[str]] = {}
    for iface in twin.interfaces:
        if iface.cidr and iface.enabled:
            members_by_subnet.setdefault(norm_cidr(iface.cidr),
                                         []).append(iface.device)
    edges: list[TopologyEdge] = []
    for cidr, members in sorted(members_by_subnet.items()):
        unique = list(dict.fromkeys(members))
        for i in range(len(unique) - 1):
            edges.append(TopologyEdge(source=unique[i], target=unique[i + 1],
                                      subnet=cidr, kind="segment"))
    return TopologyOut(version="CANDIDATE" if change_id else "CURRENT",
                       nodes=nodes, edges=edges,
                       subnets=[s.model_dump() for s in twin.subnets],
                       services=[s.model_dump() for s in twin.services])


@views.get("/reachability", response_model=ReachabilityOut)
def reachability(change_id: int | None = None,
                 session: Session = Depends(get_db)) -> ReachabilityOut:
    payload = _payload_for(session, change_id)
    runtime = TwinRuntime(TwinPayload.model_validate(payload))
    rows = runtime.reachability_matrix()
    blocked = sum(1 for r in rows if r["status"] != "allowed")
    asym = sum(1 for r in rows if r["asymmetric"])
    return ReachabilityOut(
        version="CANDIDATE" if change_id else "CURRENT",
        rows=[ReachabilityRow(**r) for r in rows],
        summary={"total": len(rows), "allowed": len(rows) - blocked,
                 "blocked": blocked, "asymmetric": asym},
    )


@views.get("/intents")
def intents(change_id: int | None = None,
            session: Session = Depends(get_db)) -> dict[str, Any]:
    repo = IntentRepository(session)
    intent_defs = [
        IntentDef(name=row.name, itype=row.itype, params=row.params,
                  severity=row.severity, enabled=bool(row.enabled))
        for row in repo.all_enabled()
    ]
    payload = _payload_for(session, change_id)
    runtime = TwinRuntime(TwinPayload.model_validate(payload))
    outcomes = [o.model_dump() for o in evaluate_all(intent_defs, runtime)]
    passed = sum(1 for o in outcomes if o["passed"])
    return {
        "version": "CANDIDATE" if change_id else "CURRENT",
        "results": outcomes,
        "compliance_pct": round(passed * 100.0 / len(outcomes), 1) if outcomes else 100.0,
    }


@views.get("/kpis")
def kpis(session: Session = Depends(get_db)) -> dict[str, Any]:
    changes = ChangeRepository(session).list(limit=500)
    by_status: dict[str, int] = {}
    for c in changes:
        by_status[c.status] = by_status.get(c.status, 0) + 1
    failed_runs = session.query(ValidationRun).filter(
        ValidationRun.verdict == "FAIL").count()
    total_runs = session.query(ValidationRun).count()
    durations = [row[0] for row in session.execute(
        select(ValidationRun.duration_ms)).all()]
    avg_duration = round(sum(durations) / len(durations), 1) if durations else 0.0
    latest_kpi = session.scalar(
        select(KpiSnapshot).order_by(KpiSnapshot.id.desc()).limit(1))
    compliance = latest_kpi.metrics.get("intent_compliance_pct") if latest_kpi else None
    prevented = by_status.get("REJECTED", 0) + failed_runs
    return {
        "changes_total": len(changes),
        "changes_by_status": by_status,
        "validation_runs_total": total_runs,
        "failed_validations_total": failed_runs,
        "unsafe_changes_prevented": prevented,
        "intent_compliance_pct": compliance,
        "avg_validation_duration_ms": avg_duration,
    }


def _payload_for(session: Session, change_id: int | None) -> dict[str, Any]:
    snaps = SnapshotRepository(session)
    if change_id is not None:
        change = ChangeRepository(session).get(change_id)
        if change is None:
            raise HTTPException(status_code=404, detail=f"change {change_id} not found")
        if change.candidate_snapshot_id:
            cand = snaps.get(change.candidate_snapshot_id)
            if cand is not None:
                return cand.payload
    current = snaps.current()
    if current is None:
        raise HTTPException(status_code=404,
                            detail="no current snapshot; POST /network/snapshot first")
    return current.payload


_ = (SnapshotModel,)
