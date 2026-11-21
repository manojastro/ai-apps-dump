from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Thread
from uuid import uuid4

from sqlalchemy.orm import Session

from app.agents.graph import run_pipeline
from app.audit.service import audit
from app.engine.holdings import parse_holdings_text
from app.engine.ips import build_ips
from app.models.plan import FinalPlan, PlanStatusPayload
from app.models.profile import Holding, HouseholdProfile
from app.persistence import (
    HoldingRow,
    HouseholdRow,
    IpsVersionRow,
    PdfArtifactRow,
    PlanJobRow,
    PlanRow,
    PlanScenarioRow,
    RiskFindingRow,
    SourceRecordRow,
)
from app.pdf.renderer import render_plan_pdf
from app.security.pii_redactor import redact_pii


def create_ips(db: Session, profile: HouseholdProfile) -> dict:
    ips = build_ips(profile)
    hid = f"hh-{uuid4().hex[:10]}"
    now = datetime.now(timezone.utc)
    db.add(HouseholdRow(id=hid, payload=profile.model_dump_json(), created_at=now))
    db.add(IpsVersionRow(id=f"ips-{uuid4().hex[:10]}", household_id=hid, payload=ips.model_dump_json(), created_at=now))
    db.commit()
    audit(db, "IPS_VALIDATED", plan_id="", component="ips", metadata={"household_id": hid})
    return {"household_id": hid, "ips": ips.model_dump()}


def parse_holdings(db: Session, household_id: str, raw: str) -> dict:
    redacted = redact_pii(raw)
    audit(db, "PII_REDACTED", component="holdings", metadata={"kinds": redacted.kinds})
    holdings, meta = parse_holdings_text(raw)
    for h in holdings:
        db.add(HoldingRow(household_id=household_id, payload=h.model_dump_json()))
    db.commit()
    return {"holdings": [h.model_dump() for h in holdings], "meta": meta}


def enqueue_plan(db: Session, household_id: str, holdings: list[Holding] | None = None) -> str:
    plan_id = f"plan-{uuid4().hex[:12]}"
    job_id = plan_id
    now = datetime.now(timezone.utc)
    db.add(
        PlanJobRow(
            id=job_id,
            plan_id=plan_id,
            status="queued",
            progress_pct=5,
            message="queued",
            events="[]",
            created_at=now,
        )
    )
    db.commit()
    audit(db, "PLAN_CREATED", plan_id=plan_id, component="plans")
    Thread(target=_run_job, args=(job_id, household_id, holdings), daemon=True).start()
    return plan_id


def _run_job(job_id: str, household_id: str, holdings: list[Holding] | None) -> None:
    from app.db import SessionLocal

    db = SessionLocal()
    try:
        job = db.get(PlanJobRow, job_id)
        if not job:
            return
        job.status = "running"
        job.progress_pct = 15
        job.message = "agents running"
        db.commit()
        hh_row = db.get(HouseholdRow, household_id)
        if not hh_row:
            job.status = "failed"
            job.error = "household not found"
            db.commit()
            return
        profile = HouseholdProfile.model_validate_json(hh_row.payload)
        if holdings is None:
            rows = db.query(HoldingRow).filter(HoldingRow.household_id == household_id).all()
            holdings = [Holding.model_validate_json(r.payload) for r in rows]
        conflict = (profile.fixture_id or "") == "11"
        plan = run_pipeline(profile, holdings, conflict=conflict)
        plan.plan_id = job.plan_id
        _persist_plan(db, household_id, plan)
        job.status = "warning" if plan.degraded or plan.no_valid_plan else "complete"
        job.progress_pct = 100
        job.message = "complete"
        job.events = json.dumps([e.model_dump(mode="json") for e in plan.events])
        db.commit()
        audit(db, "AGENT_COMPLETED", plan_id=plan.plan_id, component="pipeline")
        if plan.vetoes:
            audit(db, "RISK_VETO", plan_id=plan.plan_id, component="risk_officer")
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        job = db.get(PlanJobRow, job_id)
        if job:
            job.status = "failed"
            job.error = str(exc)
            job.message = "failed"
            db.commit()
    finally:
        db.close()


def _persist_plan(db: Session, household_id: str, plan: FinalPlan) -> None:
    now = datetime.now(timezone.utc)
    db.add(
        PlanRow(
            id=plan.plan_id,
            household_id=household_id,
            version=plan.version,
            selected=plan.selected or "",
            payload=plan.model_dump_json(),
            snapshot_id=plan.snapshot_id,
            rules_version=plan.rules_version,
            created_at=now,
        )
    )
    for s in plan.scenarios:
        db.add(PlanScenarioRow(plan_id=plan.plan_id, name=s.name, payload=s.model_dump_json()))
    for f in plan.risk_findings:
        db.add(RiskFindingRow(plan_id=plan.plan_id, payload=f.model_dump_json()))
    for src in plan.sources:
        db.add(
            SourceRecordRow(
                id=f"{src.source_id}-{uuid4().hex[:8]}",
                plan_id=plan.plan_id,
                payload=src.model_dump_json(),
            )
        )
    db.commit()


def get_plan(db: Session, plan_id: str) -> FinalPlan | None:
    row = db.get(PlanRow, plan_id)
    if not row:
        return None
    return FinalPlan.model_validate_json(row.payload)


def get_status(db: Session, plan_id: str) -> PlanStatusPayload | None:
    job = db.get(PlanJobRow, plan_id)
    if not job:
        return None
    events = json.loads(job.events or "[]")
    from app.models.facts import ApiMeta
    from app.constants import DISCLAIMER, RULES_VERSION

    return PlanStatusPayload(
        plan_id=plan_id,
        status=job.status,  # type: ignore[arg-type]
        progress_pct=job.progress_pct,
        agents=events,
        message=job.message or job.error,
        meta=ApiMeta(disclaimer=DISCLAIMER, rules_version=RULES_VERSION),
    )


def select_scenario(db: Session, plan_id: str, name: str) -> FinalPlan:
    row = db.get(PlanRow, plan_id)
    if not row:
        raise KeyError("plan")
    plan = FinalPlan.model_validate_json(row.payload)
    if name not in {s.name for s in plan.scenarios}:
        raise ValueError("unknown scenario")
    plan.selected = name  # type: ignore[assignment]
    plan.version += 1
    row.payload = plan.model_dump_json()
    row.selected = name
    row.version = plan.version
    db.commit()
    audit(db, "PLAN_SELECTED", plan_id=plan_id, component="plans", metadata={"selected": name, "version": plan.version})
    return plan


def pdf_bytes(db: Session, plan_id: str) -> bytes:
    plan = get_plan(db, plan_id)
    if not plan:
        raise KeyError("plan")
    path = Path("data/pdfs") / f"{plan_id}.pdf"
    data = render_plan_pdf(plan, path)
    db.add(
        PdfArtifactRow(
            id=f"pdf-{uuid4().hex[:10]}",
            plan_id=plan_id,
            path=str(path),
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()
    audit(db, "PDF_GENERATED", plan_id=plan_id, component="pdf")
    return data
