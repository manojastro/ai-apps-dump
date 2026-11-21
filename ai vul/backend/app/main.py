"""FastAPI application factory."""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, inspect, select

from app.api import routes_ai, routes_auth, routes_integrations, routes_inventory, routes_workflow
from app.core.config import get_settings
from app.core.db import get_engine, session_scope
from app.core.types import new_id
from app.observability.logging import configure_logging, correlation_id_var

log = logging.getLogger("aegis.app")


def _bootstrap() -> None:
    import app.models  # noqa: F401
    from app.graphs.runner import get_runner
    from app.models.identity import User

    settings = get_settings()
    if not inspect(get_engine()).has_table("users"):
        if settings.is_sqlite:
            from app.core.db import Base

            log.warning("SQLite database has no schema; creating tables (use Alembic for PostgreSQL)")
            Base.metadata.create_all(get_engine())
        else:
            raise RuntimeError("Database schema missing: run `alembic upgrade head` before starting the API")
    if settings.seed_on_start:
        with session_scope() as db:
            empty = not db.scalar(select(func.count()).select_from(User))
        if empty:
            from app.seed.seed import seed_all

            log.info("SEED_ON_START: seeding simulated enterprise")
            seed_all()
    runner = get_runner()
    recovered = runner.recover()
    if recovered:
        log.info("resumed %d workflow(s) from durable checkpoints", recovered)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_json)
    problems = settings.validate_for_production()
    if problems:
        raise RuntimeError("Unsafe production configuration: " + "; ".join(problems))
    _bootstrap()
    log.info(
        "AegisRemediate API started", extra={"ai_provider": settings.ai_provider, "servicenow_mode": settings.servicenow_mode}
    )
    yield
    from app.graphs.runner import set_runner

    set_runner(None)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="AegisRemediate AI",
        version="1.0.0",
        description="Agentic vulnerability remediation orchestration with human-controlled approvals.",
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "X-Requested-With", "Authorization", "Last-Event-ID"],
    )

    @app.middleware("http")
    async def correlation_and_headers(request: Request, call_next):
        cid = request.headers.get("x-correlation-id") or new_id()
        cid = cid[:64]
        token = correlation_id_var.set(cid)
        started = time.monotonic()
        try:
            response = await call_next(request)
        finally:
            correlation_id_var.reset(token)
        response.headers["X-Correlation-ID"] = cid
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = response.headers.get("Cache-Control", "no-store")
        if request.url.path.startswith("/api/") and not request.url.path.endswith("/stream"):
            log.info(
                "%s %s %s %.0fms", request.method, request.url.path, response.status_code, (time.monotonic() - started) * 1000
            )
        return response

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled error on %s", request.url.path)
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error", "correlation_id": correlation_id_var.get()}
        )

    for module in (routes_auth, routes_inventory, routes_workflow, routes_integrations, routes_ai):
        app.include_router(module.router)
    return app


app = create_app()
