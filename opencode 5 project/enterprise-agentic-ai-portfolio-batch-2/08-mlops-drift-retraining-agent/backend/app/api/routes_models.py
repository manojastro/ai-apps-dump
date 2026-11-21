"""Model registry and baseline training endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db import get_session
from backend.app.schemas.dto import TrainBaselineRequest, TrainBaselineResponse
from backend.app.services.baseline import train_baseline
from backend.app.tools.registry_tools import get_default_registry

router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.post("/train-baseline", response_model=TrainBaselineResponse)
def post_train_baseline(
    request: TrainBaselineRequest, session: Session = Depends(get_session)
) -> TrainBaselineResponse:
    return train_baseline(session, seed=request.seed, n_samples=request.n_samples)


@router.get("/tools")
def list_tools() -> dict:
    return {"tools": get_default_registry().list_tools()}
