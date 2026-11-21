"""Stable API error envelope: {"error": {"code": ..., "message": ..., "details": ...}}."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Stable codes are documented in docs/api.md. Add, never repurpose.
ERROR_CODES = {
    "AUTH_REQUIRED",
    "AUTH_INVALID",
    "CSRF_FAILED",
    "FORBIDDEN_ROLE",
    "NOT_FOUND",
    "VALIDATION_FAILED",
    "RATE_LIMITED",
    "IDEMPOTENCY_CONFLICT",
    "INVALID_TRANSITION",
    "REQUEST_INCOMPLETE",
    "RUN_ACTIVE",
    "APPROVER_IS_REQUESTER",
    "APPROVAL_EXPIRED",
    "APPROVAL_NOT_PENDING",
    "QUOTE_INELIGIBLE",
    "HARD_POLICY_EXCEPTION",
    "RUN_NOT_CANCELABLE",
    "PAYLOAD_TOO_LARGE",
    "EVIDENCE_UNAVAILABLE",
    "FIXTURE_CONTROL_UNAVAILABLE",
    "CONFLICT",
}


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, details: dict[str, Any] | None = None):
        assert code in ERROR_CODES, code
        self.status = status
        self.code = code
        self.message = message
        self.details = details or {}


def error_body(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError):
        return JSONResponse(error_body(exc.code, exc.message, exc.details), status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        details = {"errors": [{"loc": list(e["loc"]), "msg": e["msg"]} for e in exc.errors()]}
        return JSONResponse(error_body("VALIDATION_FAILED", "Request validation failed.", details), status_code=422)
