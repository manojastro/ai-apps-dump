"""FastAPI application entry point: `uv run uvicorn spreadlens.main:app --port 8000`."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from spreadlens.api import routes_auth, routes_documents, routes_internal, routes_ops, routes_spreads
from spreadlens.api.deps import J
from spreadlens.config import get_settings
from spreadlens.observability import configure, correlation_id, log, new_correlation_id, span

logger = logging.getLogger("spreadlens.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    configure(s.log_level, s.otel_exporter_otlp_endpoint)
    worker = None
    if s.run_worker_in_api and s.env != "test":
        from spreadlens.workflow.worker import Worker

        worker = Worker(s)
        worker.start()
        log(logger, logging.INFO, "in-process worker started", concurrency=s.worker_concurrency)
    log(logger, logging.INFO, "engine started", agent_mode=s.agent_mode, ocr=s.ocr_provider, storage=s.storage_backend)
    yield
    if worker:
        worker.stop()


app = FastAPI(title="SpreadLens AI engine", version="0.1.0", lifespan=lifespan,
              description="Document processing, deterministic checks, workflow coordination, analyst review and exports.")
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"], expose_headers=["x-correlation-id", "X-Page-Width-Pt", "X-Page-Height-Pt"])


@app.middleware("http")
async def correlation(request: Request, call_next):
    cid = request.headers.get("x-correlation-id") or new_correlation_id()
    token = correlation_id.set(cid[:64])
    t0 = time.monotonic()
    try:
        with span("http.request", method=request.method, route=request.url.path):
            response = await call_next(request)
        response.headers["x-correlation-id"] = cid
        response.headers["X-Content-Type-Options"] = "nosniff"
        log(logger, logging.INFO, "request", method=request.method, path=request.url.path, status=response.status_code,
            ms=int((time.monotonic() - t0) * 1000))
        return response
    finally:
        correlation_id.reset(token)


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    return J({"detail": exc.detail, "correlation_id": correlation_id.get()}, exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return J({"detail": [{"loc": e.get("loc"), "msg": e.get("msg")} for e in exc.errors()], "correlation_id": correlation_id.get()}, 422)


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    logger.exception("unhandled error", extra={"fields": {"path": request.url.path, "exc_type": type(exc).__name__}})
    return J({"detail": "Internal error", "correlation_id": correlation_id.get()}, 500)


for r in (routes_auth, routes_documents, routes_spreads, routes_ops, routes_internal):
    app.include_router(r.router)
