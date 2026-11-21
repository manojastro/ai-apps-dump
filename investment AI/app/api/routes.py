from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.constants import DISCLAIMER, RULES_VERSION
from app.data.fixtures import mock_market_snapshot
from app.db import get_db
from app.models.facts import ApiMeta
from app.models.profile import Holding, HouseholdProfile
from app.persistence import PlanRow, SourceRecordRow
from app.regulatory.regulatory_snapshot import build_mock_snapshot
from app.services import plans as plan_service

router = APIRouter()


class HoldingsParseIn(BaseModel):
    household_id: str
    text: str = Field(min_length=1, max_length=20000)


class PlanCreateIn(BaseModel):
    household_id: str
    holdings: list[Holding] | None = None


class SelectIn(BaseModel):
    scenario: str


class Envelope(BaseModel):
    data: Any
    meta: ApiMeta


def _meta(**kwargs) -> ApiMeta:
    return ApiMeta(disclaimer=DISCLAIMER, rules_version=RULES_VERSION, **kwargs)


@router.post("/ips")
def create_ips(profile: HouseholdProfile, db: Session = Depends(get_db)) -> dict:
    result = plan_service.create_ips(db, profile)
    return {"data": result, "meta": _meta().model_dump()}


@router.post("/holdings/parse")
def parse_holdings(body: HoldingsParseIn, db: Session = Depends(get_db)) -> dict:
    result = plan_service.parse_holdings(db, body.household_id, body.text)
    return {"data": result, "meta": _meta().model_dump()}


@router.post("/plans")
def create_plan(body: PlanCreateIn, db: Session = Depends(get_db)) -> dict:
    plan_id = plan_service.enqueue_plan(db, body.household_id, body.holdings)
    return {"data": {"plan_id": plan_id, "status": "queued"}, "meta": _meta().model_dump()}


@router.get("/plans/{plan_id}")
def get_plan(plan_id: str, db: Session = Depends(get_db)) -> dict:
    plan = plan_service.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(404, "plan not found")
    return {"data": plan.model_dump(mode="json"), "meta": plan.meta.model_dump()}


@router.get("/plans/{plan_id}/status")
def plan_status(plan_id: str, db: Session = Depends(get_db)) -> dict:
    status = plan_service.get_status(db, plan_id)
    if not status:
        raise HTTPException(404, "job not found")
    return {"data": status.model_dump(mode="json"), "meta": status.meta.model_dump()}


@router.post("/plans/{plan_id}/select")
def select_plan(plan_id: str, body: SelectIn, db: Session = Depends(get_db)) -> dict:
    try:
        plan = plan_service.select_scenario(db, plan_id, body.scenario)
    except KeyError:
        raise HTTPException(404, "plan not found") from None
    except ValueError:
        raise HTTPException(400, "unknown scenario") from None
    return {"data": plan.model_dump(mode="json"), "meta": plan.meta.model_dump()}


@router.get("/plans/{plan_id}/pdf")
def plan_pdf(plan_id: str, db: Session = Depends(get_db)):
    try:
        data = plan_service.pdf_bytes(db, plan_id)
    except KeyError:
        raise HTTPException(404, "plan not found") from None
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="aegis-plan-{plan_id}.pdf"'},
    )


@router.get("/market/snapshot")
def market_snapshot() -> dict:
    snap = mock_market_snapshot()
    return {"data": snap.model_dump(mode="json"), "meta": _meta(degraded=True, snapshot_id=snap.snapshot_id).model_dump()}


@router.get("/regulatory/snapshot")
def regulatory_snapshot() -> dict:
    snap = build_mock_snapshot()
    return {"data": snap.model_dump(mode="json"), "meta": _meta(degraded=True, snapshot_id=snap.snapshot_id).model_dump()}


@router.get("/sources")
def sources(plan_id: str | None = None, db: Session = Depends(get_db)) -> dict:
    q = db.query(SourceRecordRow)
    if plan_id:
        q = q.filter(SourceRecordRow.plan_id == plan_id)
    rows = q.limit(200).all()
    payload = [json.loads(r.payload) for r in rows]
    if not payload:
        payload = [s.model_dump(mode="json") for s in build_mock_snapshot().sources]
    return {"data": payload, "meta": _meta().model_dump()}


@router.get("/evals/households")
def eval_households() -> dict:
    path = Path(__file__).resolve().parents[2] / "evals" / "households.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {"data": data, "meta": _meta().model_dump()}


@router.post("/demo/seed/{fixture_id}")
def seed_fixture(fixture_id: str, db: Session = Depends(get_db)) -> dict:
    path = Path(__file__).resolve().parents[2] / "evals" / "households.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    match = next((h for h in data["households"] if h["id"] == fixture_id), None)
    if not match:
        raise HTTPException(404, "fixture not found")
    profile = HouseholdProfile.model_validate(match["profile"])
    created = plan_service.create_ips(db, profile)
    holdings = [Holding.model_validate(h) for h in profile.existing_holdings]
    pasted = match.get("pasted_holdings")
    parsed_meta = None
    if pasted:
        parsed = plan_service.parse_holdings(db, created["household_id"], pasted)
        parsed_meta = parsed["meta"]
        holdings = [Holding.model_validate(h) for h in parsed["holdings"]]
    else:
        from app.persistence import HoldingRow

        for h in holdings:
            db.add(HoldingRow(household_id=created["household_id"], payload=h.model_dump_json()))
        db.commit()
    plan_id = plan_service.enqueue_plan(db, created["household_id"], holdings)
    return {
        "data": {
            "household_id": created["household_id"],
            "ips": created["ips"],
            "plan_id": plan_id,
            "pii": parsed_meta,
        },
        "meta": _meta().model_dump(),
    }
