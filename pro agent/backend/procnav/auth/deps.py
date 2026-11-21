"""FastAPI dependencies for authentication, CSRF and role checks.

Roles are read from server-side memberships only. A client-supplied role or tenant value never
grants access.
"""

from __future__ import annotations

import secrets
import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import Depends, Request

from ..api.errors import ApiError
from .service import Principal, load_principal

SESSION_COOKIE = "procnav_session"
CSRF_COOKIE = "procnav_csrf"
CSRF_HEADER = "x-csrf-token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def current_principal(request: Request) -> Principal:
    principal = load_principal(request.cookies.get(SESSION_COOKIE))
    if principal is None:
        raise ApiError(401, "AUTH_REQUIRED", "Sign in to continue.")
    if request.method not in SAFE_METHODS:
        sent = request.headers.get(CSRF_HEADER, "")
        if not sent or not secrets.compare_digest(sent, principal.csrf_token):
            raise ApiError(403, "CSRF_FAILED", "Missing or invalid CSRF token.")
    request.state.principal = principal
    return principal


def require_role(*roles: str) -> Callable[..., Principal]:
    def dep(principal: Principal = Depends(current_principal)) -> Principal:
        if not any(principal.has(r) for r in roles):
            raise ApiError(403, "FORBIDDEN_ROLE", f"Requires role: {' or '.join(roles)}.")
        return principal

    return dep


class RateLimiter:
    """Small in-process sliding-window limiter. Deploy behind the reverse proxy limiter as well."""

    def __init__(self, limit: int, window_seconds: float):
        self.limit = limit
        self.window = window_seconds
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        q = self.hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            raise ApiError(429, "RATE_LIMITED", "Too many requests. Try again shortly.")
        q.append(now)


login_limiter = RateLimiter(limit=10, window_seconds=60)
mutation_limiter = RateLimiter(limit=120, window_seconds=60)
