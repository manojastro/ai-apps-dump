"""Forecast endpoints."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import Db, UserScope
from app.api.schemas import Forecast, ForecastChanges
from app.services import forecast

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("", response_model=Forecast)
def get_forecast(
    db: Db, scope: UserScope,
    quarter: Annotated[str | None, Query(pattern=r"^20\d{2}Q[1-4]$")] = None,
    team_id: int | None = None, region: str | None = None,
) -> dict:
    return forecast.get_forecast(db, scope, quarter, team_id, region)


@router.get("/changes", response_model=ForecastChanges)
def changes(db: Db, scope: UserScope) -> dict:
    return forecast.get_changes(db, scope)


@router.get("/backtest")
def backtest(_: UserScope) -> dict[str, Any]:
    result = forecast.backtest_results()
    if result is None:
        raise HTTPException(404, "Back-test has not been run")
    return result
