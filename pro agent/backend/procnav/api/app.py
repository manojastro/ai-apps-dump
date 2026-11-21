"""FastAPI application factory.

uvicorn procnav.api.app:app --port 8300
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ..core.config import REPO_ROOT, get_settings
from ..core import tracing
from . import errors
from .errors import error_body
from .routes import router

MAX_BODY_BYTES = 64 * 1024


def create_app() -> FastAPI:
    settings = get_settings()  # validates configuration at startup
    app = FastAPI(
        title="Procurement Navigator API",
        version="0.1.0",
        description="Browser-agent procurement over synthetic supplier portals. Error envelope: "
        "{error: {code, message, details}} with stable codes (see docs/api.md). Mutations with cookie "
        "sessions require the X-CSRF-Token header.",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    errors.install(app)
    tracing.setup("procnav-api", app)

    @app.middleware("http")
    async def limits_and_headers(request: Request, call_next):
        length = request.headers.get("content-length")
        if length and int(length) > MAX_BODY_BYTES:
            return JSONResponse(error_body("PAYLOAD_TOO_LARGE", "Request body too large"), status_code=413)
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("X-Frame-Options", "DENY")
        return response

    app.include_router(router)

    # Serve the built single-page app when present (production image); dev uses the Vite server.
    dist = Path(REPO_ROOT) / "frontend" / "dist"
    if dist.exists():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def spa(path: str):
            if path.startswith("api/"):
                return JSONResponse(error_body("NOT_FOUND", "Not found"), status_code=404)
            target = dist / path
            if path and target.is_file() and dist.resolve() in target.resolve().parents:
                return FileResponse(target)
            return FileResponse(dist / "index.html")

    _ = settings
    return app


app = create_app()
