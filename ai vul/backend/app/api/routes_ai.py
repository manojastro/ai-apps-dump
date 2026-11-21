"""AI assistant and evaluation endpoints."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import serializers as ser
from app.core.db import get_db
from app.evaluation.runner import run_evaluation
from app.llm.factory import ProviderConfigError
from app.models.workflow import EvaluationCaseResult, EvaluationRun
from app.security.auth import Principal, require
from app.security.permissions import Permission
from app.services.assistant import Assistant
from app.services.audit import record_audit

router = APIRouter(tags=["ai"])


class ChatBody(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    context: dict[str, str] = Field(default_factory=dict)


@router.post("/api/assistant/chat")
def chat(body: ChatBody, principal: Principal = Depends(require(Permission.ASSISTANT)), db: Session = Depends(get_db)) -> dict:
    context = {k: v[:64] for k, v in body.context.items() if k in ("finding_id", "plan_id", "cve_id")}
    try:
        result = Assistant(db, principal).ask(body.message, context)
    except ProviderConfigError as exc:
        raise HTTPException(503, str(exc)) from exc
    record_audit(
        db,
        actor=principal,
        action="assistant_query",
        target_type="assistant",
        details={"message": body.message[:300], "tools": [c["tool"] for c in result["tool_calls"]]},
    )
    db.commit()
    return result


class EvalBody(BaseModel):
    provider: Literal["mock", "openai", "anthropic", "gemini"] | None = None
    model: str | None = Field(default=None, max_length=128)


def _run(r: EvaluationRun) -> dict[str, Any]:
    return {
        "id": r.id,
        "dataset_version": r.dataset_version,
        "provider": r.provider,
        "model": r.model,
        "status": r.status,
        "total": r.total,
        "passed": r.passed,
        "failed": r.failed,
        "metrics": r.metrics,
        "started_by": r.started_by,
        "started_at": ser.iso(r.started_at),
        "finished_at": ser.iso(r.finished_at),
    }


@router.post("/api/evaluation/run")
def start_eval(
    body: EvalBody, principal: Principal = Depends(require(Permission.EVALUATION_RUN)), db: Session = Depends(get_db)
) -> dict:
    try:
        run = run_evaluation(db, body.provider, body.model, principal.email)
    except ProviderConfigError as exc:
        raise HTTPException(422, str(exc)) from exc
    record_audit(
        db,
        actor=principal,
        action="evaluation_run",
        target_type="evaluation_run",
        target_id=run.id,
        details={"provider": run.provider, "passed": run.passed, "total": run.total},
    )
    db.commit()
    return _run(run)


@router.get("/api/evaluation/runs")
def list_runs(_: Principal = Depends(require(Permission.READ)), db: Session = Depends(get_db)) -> list[dict]:
    return [_run(r) for r in db.scalars(select(EvaluationRun).order_by(EvaluationRun.started_at.desc()).limit(50))]


@router.get("/api/evaluation/runs/{run_id}")
def get_run(run_id: str, _: Principal = Depends(require(Permission.READ)), db: Session = Depends(get_db)) -> dict:
    r = db.get(EvaluationRun, run_id)
    if r is None:
        raise HTTPException(404, "Evaluation run not found")
    cases = db.scalars(
        select(EvaluationCaseResult).where(EvaluationCaseResult.run_id == run_id).order_by(EvaluationCaseResult.case_id)
    )
    return _run(r) | {
        "cases": [
            {
                "case_id": c.case_id,
                "category": c.category,
                "passed": c.passed,
                "expected": c.expected,
                "actual": c.actual,
                "notes": c.notes,
                "latency_ms": c.latency_ms,
            }
            for c in cases
        ]
    }
