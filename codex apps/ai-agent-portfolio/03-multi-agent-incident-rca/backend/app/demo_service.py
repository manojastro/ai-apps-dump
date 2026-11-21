from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime

from fastapi import FastAPI, Response


SERVICE_NAME = os.getenv("DEMO_SERVICE_NAME", "checkout-api")
DEPENDENCIES = [item for item in os.getenv("DEMO_DEPENDENCIES", "").split(",") if item]
app = FastAPI(title=f"Synthetic telemetry service: {SERVICE_NAME}")


@app.get("/")
def root() -> dict[str, object]:
    return {"service": SERVICE_NAME, "status": "available", "dependencies": DEPENDENCIES}


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"service": SERVICE_NAME, "status": "ok"}


@app.get("/work")
def work(delay_ms: int = 5, fail: bool = False) -> Response:
    delay_ms = min(max(delay_ms, 0), 2_000)
    time.sleep(delay_ms / 1_000)
    status = 500 if fail else 200
    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "service": SERVICE_NAME,
        "event": "synthetic_request",
        "duration_ms": delay_ms,
        "status": status,
    }
    print(json.dumps(event, sort_keys=True), flush=True)
    return Response(json.dumps(event), status_code=status, media_type="application/json")


@app.get("/metrics")
def metrics() -> Response:
    body = "\n".join(
        [
            "# HELP demo_service_up Synthetic service availability.",
            "# TYPE demo_service_up gauge",
            f'demo_service_up{{service="{SERVICE_NAME}"}} 1',
            "# HELP demo_service_requests_total Synthetic requests.",
            "# TYPE demo_service_requests_total counter",
            f'demo_service_requests_total{{service="{SERVICE_NAME}",status="200"}} 42',
            "",
        ]
    )
    return Response(body, media_type="text/plain; version=0.0.4")

