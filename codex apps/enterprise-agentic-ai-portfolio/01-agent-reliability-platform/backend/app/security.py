from __future__ import annotations

import time
from collections import defaultdict, deque
from hmac import compare_digest
from threading import Lock

from fastapi import Header, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .config import Settings


class SlidingWindowRateLimiter:
    def __init__(self, limit: int, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests: dict[str, deque[float]] = defaultdict(deque)
        self.lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self.lock:
            bucket = self.requests[key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self.limit:
                return False
            bucket.append(now)
            return True


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'"
        return response


def make_rate_limit_middleware(limiter: SlidingWindowRateLimiter):
    async def middleware(request: Request, call_next):
        if request.url.path in {"/health", "/ready", "/metrics"}:
            return await call_next(request)
        client = request.client.host if request.client else "local"
        if not limiter.allow(client):
            return JSONResponse(status_code=429, content={"detail": "rate limit exceeded"}, headers={"Retry-After": "60"})
        return await call_next(request)
    return middleware


def auth_dependency(settings: Settings):
    async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
        if settings.api_key and (not x_api_key or not compare_digest(x_api_key, settings.api_key)):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid API key")
    return require_api_key
