"""FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.api.observability import router as observability_router
from app.api.v1 import api_v1_router
from app.db import dispose_engine, init_db, session_scope
from app.services.metrics import METRICS


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with session_scope() as session:
        from app.repositories.repo import SnapshotRepository

        if SnapshotRepository(session).current() is None:
            from app.services.validation import seed_network

            seed_network(session)
    yield
    dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Network Digital Twin & Change Validation Agent",
        version="1.0.0",
        description="Validates every network change against a digital twin before production.",
        lifespan=lifespan,
    )
    app.include_router(observability_router)
    app.include_router(api_v1_router)

    @app.middleware("http")
    async def count_requests(request: Request, call_next):
        response = await call_next(request)
        METRICS.incr("http_requests_total",
                     {"method": request.method,
                      "path": _route_template(request),
                      "status": str(response.status_code)})
        return response

    return app


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    return getattr(route, "path", request.url.path) if route else request.url.path


app = create_app()
