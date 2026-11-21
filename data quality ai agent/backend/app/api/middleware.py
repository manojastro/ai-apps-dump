import hmac
import time
from collections import defaultdict, deque
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


def api_error(request: Request, status: int, code: str, message: str):
    correlation_id = getattr(request.state, "correlation_id", str(uuid4()))
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "correlation_id": correlation_id}},
        headers={"X-Correlation-ID": correlation_id},
    )


class RequestPolicy(BaseHTTPMiddleware):
    def __init__(self, app, settings):
        super().__init__(app)
        self.settings = settings
        self.windows: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request, call_next):
        request.state.correlation_id = str(uuid4())
        if request.url.path.startswith("/api/") and request.method != "OPTIONS":
            secret = self.settings.api_token.get_secret_value()
            if secret and not hmac.compare_digest(
                request.headers.get("authorization", ""), "Bearer " + secret
            ):
                return api_error(
                    request, 401, "UNAUTHORIZED", "A valid API bearer token is required"
                )
            if request.method == "POST":
                origin = request.headers.get("origin")
                if origin and origin not in self.settings.allowed_origins:
                    return api_error(
                        request, 403, "ORIGIN_DENIED", "This browser origin is not allowed"
                    )
                key = request.client.host if request.client else "local"
                timestamp = time.monotonic()
                if len(self.windows) > 1024:
                    self.windows = defaultdict(
                        deque,
                        {k: v for k, v in self.windows.items() if v and v[-1] > timestamp - 60},
                    )
                window = self.windows[key]
                while window and window[0] <= timestamp - 60:
                    window.popleft()
                if len(window) >= self.settings.write_requests_per_minute:
                    return api_error(
                        request, 429, "RATE_LIMITED", "Write request rate limit exceeded"
                    )
                window.append(timestamp)
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = request.state.correlation_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response
