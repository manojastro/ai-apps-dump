from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.agents.graph import get_graph
from app.api.routes import router
from app.config import get_settings
from app.constants import DISCLAIMER, PRODUCT_NAME
from app.db import init_db
from app.logging import configure_logging, get_logger

settings = get_settings()
configure_logging(settings.log_level)
log = get_logger(component="api")


def create_app() -> FastAPI:
    application = FastAPI(
        title=PRODUCT_NAME,
        version="0.1.0",
        description="Educational research and financial-planning simulation. Not a SEBI-registered adviser.",
    )
    application.state.data_mode = settings.data_mode
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @application.middleware("http")
    async def extras(request: Request, call_next):
        if request.headers.get("content-length"):
            try:
                if int(request.headers["content-length"]) > settings.max_request_bytes:
                    return JSONResponse({"detail": "request too large"}, status_code=413)
            except ValueError:
                pass
        request_id = request.headers.get("x-request-id") or uuid4().hex
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Aegis-Disclaimer"] = "educational-only"
        return response

    @application.get("/health")
    def health():
        return {"status": "ok", "product": PRODUCT_NAME, "disclaimer": DISCLAIMER}

    @application.get("/ready")
    def ready():
        init_db()
        graph = get_graph()
        return {
            "status": "ready",
            "database": "ok",
            "graph": bool(graph),
            "data_mode": settings.data_mode,
            "disclaimer": DISCLAIMER,
        }

    application.include_router(router, prefix="/api/v1")

    @application.on_event("startup")
    def _startup():
        init_db()
        get_graph()
        log.info("startup", data_mode=settings.data_mode)

    return application


app = create_app()
