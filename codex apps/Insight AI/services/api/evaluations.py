import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select

from packages.agent.version import version_metadata
from packages.evaluation.catalog import cases
from packages.evaluation.policy import POLICY_PATH
from services.api.auth import current_user, require
from services.api.db import CaseResult, Evaluation, Job, Session, serialize

router = APIRouter()


class EvaluationInput(BaseModel):
    candidate: Literal["script-v1", "script-regression"] = "script-regression"
    trials: int = Field(default=1, ge=1, le=3)
    case_id: str | None = None


@router.get("/api/evaluation-cases")
def catalog(user=Depends(current_user)):
    return [{k: v for k, v in c.items() if k not in {"packet", "expected", "probe"}} for c in cases()]


@router.get("/api/policy")
def policy(user=Depends(current_user)):
    return json.loads(POLICY_PATH.read_text())


@router.get("/api/evaluations")
def list_evaluations(user=Depends(current_user)):
    with Session() as db:
        return [
            serialize(e)
            for e in db.scalars(select(Evaluation).order_by(Evaluation.created_at.desc()).limit(100))
        ]


@router.post("/api/evaluations")
def create_evaluation(body: EvaluationInput, user=Depends(require("investigator"))):
    if body.case_id and body.case_id not in {c["id"] for c in cases()}:
        raise HTTPException(404, "CASE_NOT_FOUND")
    with Session() as db:
        config = body.model_dump()
        config.update(
            baseline_version=version_metadata("script-v1"), candidate_version=version_metadata(body.candidate)
        )
        evaluation = Evaluation(mode="replay", config=config)
        db.add(evaluation)
        db.flush()
        db.add(Job(kind="evaluate", target_id=evaluation.id))
        db.commit()
        return serialize(evaluation)


@router.get("/api/evaluations/{evaluation_id}")
def evaluation_detail(evaluation_id: str, user=Depends(current_user)):
    with Session() as db:
        row = db.get(Evaluation, evaluation_id)
        if not row:
            raise HTTPException(404, "EVALUATION_NOT_FOUND")
        return {
            **serialize(row),
            "results": [
                r.data
                for r in db.scalars(
                    select(CaseResult)
                    .where(CaseResult.evaluation_id == evaluation_id)
                    .order_by(CaseResult.created_at)
                )
            ],
        }


@router.post("/api/evaluations/{evaluation_id}/cancel")
def cancel(evaluation_id: str, user=Depends(require("investigator"))):
    with Session() as db:
        row = db.get(Evaluation, evaluation_id)
        if not row:
            raise HTTPException(404, "EVALUATION_NOT_FOUND")
        if row.status == "completed":
            raise HTTPException(409, "EVALUATION_ALREADY_COMPLETED")
        row.status = "cancelled"
        db.commit()
    return {"status": "cancelled"}


@router.get("/api/evaluations/{evaluation_id}/export")
def export(evaluation_id: str, user=Depends(current_user)):
    return JSONResponse(
        evaluation_detail(evaluation_id, user),
        headers={"Content-Disposition": f'attachment; filename="evaluation-{evaluation_id}.json"'},
    )
