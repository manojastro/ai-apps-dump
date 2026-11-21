"""FastAPI application factory for the drift and retraining agent platform."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.app.api.errors import DomainError
from backend.app.api import (
    routes_candidates,
    routes_health,
    routes_models,
    routes_monitoring,
    routes_promotions,
    routes_registry,
    routes_retraining,
    routes_shadow,
)
from backend.app.db import init_db
from backend.app.metrics import metrics


def create_app() -> FastAPI:
    app = FastAPI(
        title="MLOps Drift Detection & Safe Retraining Agent",
        version="1.0.0",
        description="Detects drift, decides IF retraining is justified, promotes candidates safely.",
    )
    app.include_router(routes_health.router)
    app.include_router(routes_models.router)
    app.include_router(routes_monitoring.router)
    app.include_router(routes_retraining.router)
    app.include_router(routes_candidates.router)
    app.include_router(routes_shadow.router)
    app.include_router(routes_promotions.router)
    app.include_router(routes_registry.router)

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    @app.middleware("http")
    async def _count_requests(request: Request, call_next):
        response = await call_next(request)
        route = request.scope.get("route")
        path_template = getattr(route, "path", request.url.path)
        metrics.inc_counter(
            "api_requests_total",
            {
                "method": request.method,
                "path": path_template,
                "status": str(response.status_code),
            },
        )
        return response

    @app.exception_handler(DomainError)
    async def _domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    return app


app = create_app()
