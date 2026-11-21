"""FastAPI application."""
from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette.responses import JSONResponse

from app.api import accounts, admin, auth, churn, copilot, deals, forecast
from app.api.schemas import Health
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import get_engine

VERSION = "0.1.0"
logger = logging.getLogger("revenueos.api")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    scheduler = None
    if get_settings().enable_scheduler:
        from app.jobs.scheduler import start_scheduler

        scheduler = start_scheduler()
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(title="RevenueOS AI", version=VERSION, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in get_settings().cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def access_log(request: Request, call_next):
    """Log the route shape only. Query strings can carry search terms."""
    started = time.perf_counter()
    response = await call_next(request)
    logger.info("request", extra={"fields": {
        "method": request.method, "path": request.url.path, "status": response.status_code,
        "ms": round((time.perf_counter() - started) * 1000, 1),
    }})
    return response


@app.get("/health", response_model=Health, tags=["health"])
def health() -> Health | JSONResponse:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("select 1"))
    except Exception:
        logger.exception("health check failed")
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "database": "unreachable", "version": VERSION},
        )
    return Health(status="ok", database="ok", version=VERSION)


for module in (auth, accounts, deals, forecast, churn, copilot, admin):
    app.include_router(module.router)
