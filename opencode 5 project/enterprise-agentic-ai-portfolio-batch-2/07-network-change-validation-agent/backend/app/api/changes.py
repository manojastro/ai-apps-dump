"""Change workflow API: submit, validate, fix, approve, reject, apply, rollback."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.entities import (
    EvidenceRec,
    HypothesisRec,
    Investigation,
    RcaRecord,
    ValidationRun,
)
from app.repositories.repo import ChangeRepository, RunRepository
from app.schemas.api import (
    ApprovalRequest,
    ChangeCreate,
    IntentResultOut,
    RegressionOut,
    RejectRequest,
    RiskAssessment,
    RootCauseAnalysis,
    ValidationReport,
)
from app.services.state_machine import IllegalTransition
from app.services.validation import (
    approve_change,
    apply_change,
    reject_change,
    rollback_change,
    run_validation,
)

router = APIRouter(prefix="/changes", tags=["changes"])


@router.post("")
def submit(request: ChangeCreate, session: Session = Depends(get_db)) -> dict[str, Any]:
    from app.services.validation import submit_change

    change = submit_change(session, title=request.title,
                           config_diff=request.config_diff,
                           requested_by=request.requested_by)
    run = RunRepository(session).latest_for_change(change.id)
    return _change_payload(session, change.id, run.id if run else None)


@router.get("")
def list_changes(limit: int = 50,
                 session: Session = Depends(get_db)) -> list[dict[str, Any]]:
    changes = ChangeRepository(session).list(limit=limit)
    return [
        {
            "id": c.id, "title": c.title, "status": c.status,
            "risk_band": c.risk_band, "risk_score": c.risk_score,
            "requested_by": c.requested_by, "fault_name": c.fault_name,
            "fix_validated": c.fix_validated, "created_at": str(c.created_at),
        }
        for c in changes
    ]


@router.get("/{change_id}")
def get_change(change_id: int, session: Session = Depends(get_db)) -> dict[str, Any]:
    _require_change(session, change_id)
    run = RunRepository(session).latest_for_change(change_id)
    return _change_payload(session, change_id, run.id if run else None)


@router.get("/{change_id}/validation", response_model=ValidationReport)
def get_validation(change_id: int, session: Session = Depends(get_db)) -> ValidationReport:
    _require_change(session, change_id)
    run = RunRepository(session).latest_for_change(change_id)
    if run is None:
        raise HTTPException(status_code=404, detail="no validation run for this change")
    return build_validation_report(session, change_id, run.id)


@router.post("/{change_id}/validate")
def revalidate(change_id: int, session: Session = Depends(get_db)) -> dict[str, Any]:
    from app.services.validation import run_validation as rerun

    _require_change(session, change_id)
    rerun(session, change_id)
    run = RunRepository(session).latest_for_change(change_id)
    return _change_payload(session, change_id, run.id if run else None)


@router.post("/{change_id}/propose-fix")
def propose_fix(change_id: int, session: Session = Depends(get_db)) -> dict[str, Any]:
    _require_change(session, change_id)
    change = ChangeRepository(session).get(change_id)
    assert change is not None
    if not change.proposed_fix_diff:
        raise HTTPException(status_code=409,
                            detail="no proposed fix available; validation must run first")
    run_validation(session, change_id)
    session.refresh(change)
    run = RunRepository(session).latest_for_change(change_id)
    payload = _change_payload(session, change_id, run.id if run else None)
    payload["fix_validated"] = change.fix_validated
    payload["proposed_fix_diff"] = change.proposed_fix_diff
    return payload


@router.post("/{change_id}/approve")
def approve(change_id: int, request: ApprovalRequest,
            session: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        change = approve_change(session, change_id, request.approver, request.comment,
                                request.justification)
    except IllegalTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    session.refresh(change)
    return {"id": change.id, "status": change.status}


@router.post("/{change_id}/reject")
def reject(change_id: int, request: RejectRequest,
           session: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        change = reject_change(session, change_id, request.actor, request.reason)
    except IllegalTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    session.refresh(change)
    return {"id": change.id, "status": change.status}


@router.post("/{change_id}/apply")
def apply(change_id: int, session: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        result = apply_change(session, change_id)
    except IllegalTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"id": change_id, **result}


@router.post("/{change_id}/rollback")
def rollback(change_id: int, actor: str = "netops",
             session: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        result = rollback_change(session, change_id, actor=actor)
    except IllegalTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"id": change_id, **result}


def _require_change(session: Session, change_id: int) -> None:
    if ChangeRepository(session).get(change_id) is None:
        raise HTTPException(status_code=404, detail="change not found")


def _change_payload(session: Session, change_id: int, run_id: int | None) -> dict[str, Any]:
    change = ChangeRepository(session).get(change_id)
    assert change is not None
    payload: dict[str, Any] = {
        "id": change.id,
        "title": change.title,
        "status": change.status,
        "risk_band": change.risk_band,
        "risk_score": change.risk_score,
        "requested_by": change.requested_by,
        "fault_name": change.fault_name,
        "fix_validated": change.fix_validated,
        "proposed_fix_diff": change.proposed_fix_diff,
        "config_diff": change.config_diff,
        "created_at": str(change.created_at),
        "validation": None,
    }
    if run_id is not None:
        payload["validation"] = build_validation_report(
            session, change_id, run_id).model_dump()
    return payload


def build_validation_report(session: Session, change_id: int,
                            run_id: int) -> ValidationReport:
    runs = RunRepository(session)
    run = session.get(ValidationRun, run_id)
    assert run is not None
    regressions = runs.regressions_for_run(run_id)
    intent_rows = runs.intents_for_run(run_id)
    investigations = session.query(Investigation).filter(
        Investigation.run_id == run_id).all()
    evidence_count = session.query(EvidenceRec).join(
        Investigation, EvidenceRec.investigation_id == Investigation.id).filter(
        Investigation.run_id == run_id).count()
    hypothesis_rows = session.query(HypothesisRec).join(
        Investigation, HypothesisRec.investigation_id == Investigation.id).filter(
        Investigation.run_id == run_id).all()
    rca_row = session.query(RcaRecord).filter(RcaRecord.run_id == run_id).first()

    summary = run.summary or {}
    passed_intents = sum(1 for i in intent_rows if i.passed)
    compliance = (round(passed_intents * 100.0 / len(intent_rows), 1)
                  if intent_rows else 100.0)
    rca = RootCauseAnalysis.model_validate(rca_row.payload) if rca_row else None
    change = ChangeRepository(session).get(change_id)
    return ValidationReport(
        change_id=change_id,
        run_id=run_id,
        verdict=run.verdict,
        risk=RiskAssessment(score=run.risk_score, band=run.risk_band,
                            components=summary.get("risk_components", {}),
                            confidence=run.confidence),
        regressions=[
            RegressionOut(kind=r.kind, severity=r.severity, source=r.source,
                          destination=r.destination, message=r.message, detail=r.detail)
            for r in regressions
        ],
        intents=[
            IntentResultOut(name=i.intent_name,
                            itype=str((i.detail or {}).get("itype", "unknown")),
                            passed=i.passed,
                            detail=str((i.detail or {}).get("detail", "")))
            for i in intent_rows
        ],
        intent_compliance_pct=compliance,
        matrix_diff_summary=summary.get("matrix_diff", {}),
        routing_changes=summary.get("route_changes", []),
        topology_findings=summary.get("topology_findings", []),
        blast_radius_devices=summary.get("blast_radius_devices", []),
        rca=rca,
        proposed_fix_diff=change.proposed_fix_diff if change else None,
        fix_validated=bool(change.fix_validated) if change else False,
        duration_ms=run.duration_ms,
        narration=run.narration,
        stages=summary.get("stages", []),
        investigations=[
            {"agent": inv.agent, "duration_ms": inv.duration_ms, "summary": inv.summary}
            for inv in investigations
        ],
        evidence_count=evidence_count,
        hypotheses=[
            {"statement": h.statement, "status": h.status, "score": h.score}
            for h in hypothesis_rows
        ],
    )
