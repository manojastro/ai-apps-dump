"""Isolated instrumented checkout demo. Never point DEMO_DATABASE_URL at the platform DB."""

import asyncio
import os
import secrets
import threading
import time
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import httpx
import psutil
from fastapi import FastAPI, Header, HTTPException, Response
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.exc import TimeoutError as PoolTimeout
from sqlalchemy.pool import QueuePool

SERVICE = os.environ.get("DEMO_SERVICE", "checkout")
DB_URL = os.environ.get("DEMO_DATABASE_URL", "sqlite:///.productionlens/demo.db")
if "platform" in DB_URL or (os.environ.get("DATABASE_URL") and DB_URL == os.environ["DATABASE_URL"]):
    raise RuntimeError("Demo and platform databases must be separate")
Path(".productionlens").mkdir(exist_ok=True)
db_engine = create_engine(
    DB_URL,
    poolclass=QueuePool,
    pool_size=3,
    max_overflow=0,
    pool_timeout=0.15,
    connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {},
)
requests = Counter("demo_requests_total", "Completed demo requests", ["service"])
errors = Counter("demo_errors_total", "Failed demo requests", ["service"])
duration = Histogram(
    "demo_duration_seconds",
    "Demo request duration",
    ["service"],
    buckets=(0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)
dependency = Histogram("demo_dependency_seconds", "Upstream duration", ["service", "dependency"])
cpu = Gauge("demo_cpu_ratio", "Process CPU utilization, cores", ["service"])
pool_usage = Gauge("demo_pool_usage", "Fraction of connections checked out", ["service"])
pool_wait = Gauge("demo_pool_wait_seconds", "Most recent connection acquisition duration", ["service"])
logs, deployments = deque(maxlen=1000), deque(maxlen=100)
state_lock = threading.Lock()
fault_state = {"fault": None, "until": 0, "revision": 0}
process = psutil.Process()
provider = TracerProvider(resource=Resource.create({"service.name": SERVICE}))
if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)
HTTPXClientInstrumentor().instrument()
tracer = trace.get_tracer("productionlens-demo")


def current_fault():
    with state_lock:
        if fault_state["until"] < time.time():
            fault_state["fault"] = None
        return fault_state["fault"]


def log(severity, message):
    context = trace.get_current_span().get_span_context()
    logs.append(
        {
            "timestamp": time.time(),
            "service": SERVICE,
            "severity": severity,
            "message": message,
            "trace_id": format(context.trace_id, "032x"),
            "span_id": format(context.span_id, "016x"),
        }
    )


def exhaust_pool(until):
    connections = []
    try:
        for _ in range(3):
            connections.append(db_engine.connect())
        while time.time() < until and current_fault() == "pool_exhaustion":
            time.sleep(0.1)
    finally:
        for connection in connections:
            connection.close()


def saturate_cpu(until):
    value = 1
    while time.time() < until and current_fault() == "cpu_saturation":
        for _ in range(10000):
            value = (value * 13 + 7) % 1000003


@asynccontextmanager
async def lifespan(app):
    stopped = asyncio.Event()

    async def sample():
        while not stopped.is_set():
            cpu.labels(SERVICE).set(process.cpu_percent() / 100)
            pool_usage.labels(SERVICE).set(db_engine.pool.checkedout() / 3)
            current_fault()
            await asyncio.sleep(0.5)

    task = asyncio.create_task(sample())
    requests.labels(SERVICE).inc(0)
    errors.labels(SERVICE).inc(0)
    pool_wait.labels(SERVICE).set(0)
    deployments.append(
        {
            "service": SERVICE,
            "revision": "demo-001",
            "timestamp": time.time(),
            "change": "Service initialized",
        }
    )
    yield
    stopped.set()
    task.cancel()
    provider.shutdown()
    db_engine.dispose()


app = FastAPI(title=f"ProductionLens demo {SERVICE}", lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app, excluded_urls="/metrics,/health,/telemetry/.*,/control/.*")


@app.get("/health")
def health():
    return {"status": "ok", "service": SERVICE}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def operation():
    fault = current_fault()
    if SERVICE == "payment":
        await asyncio.sleep(1.2 if fault == "payment_delay" else 0.025)
        return {"payment": "accepted"}
    if SERVICE == "inventory":
        await asyncio.sleep(0.01)
        return {"available": True}
    if fault == "config_regression":
        log("ERROR", "ValidationError: incompatible request schema")
        raise HTTPException(500, "Request validation failed")
    before = time.perf_counter()
    try:

        def database_read():
            with db_engine.connect() as connection:
                connection.execute(text("SELECT 1"))

        await asyncio.to_thread(database_read)
    except PoolTimeout:
        log("ERROR", "PoolTimeout: connection acquisition exceeded 150ms")
        raise HTTPException(503, "Database connection unavailable") from None
    finally:
        pool_wait.labels(SERVICE).set(time.perf_counter() - before)
    async with httpx.AsyncClient(timeout=0.4) as client:
        for name, url in [
            ("inventory", os.environ.get("INVENTORY_URL", "http://127.0.0.1:8102")),
            ("payment", os.environ.get("PAYMENT_URL", "http://127.0.0.1:8101")),
        ]:
            start = time.perf_counter()
            try:
                with tracer.start_as_current_span(f"{name}.request"):
                    result = await client.post(url + "/request")
                    result.raise_for_status()
            except httpx.HTTPError:
                log("ERROR", f"{name} upstream deadline exceeded or dependency unavailable")
                raise HTTPException(504, "Upstream dependency failed") from None
            finally:
                dependency.labels(SERVICE, name).observe(time.perf_counter() - start)
    return {"checkout": "accepted"}


@app.post("/request")
async def request():
    start = time.perf_counter()
    try:
        result = await operation()
        log("INFO", "Request accepted")
        return result
    except HTTPException:
        errors.labels(SERVICE).inc()
        raise
    finally:
        requests.labels(SERVICE).inc()
        duration.labels(SERVICE).observe(time.perf_counter() - start)


class Fault(BaseModel):
    fault: Literal["payment_delay", "config_regression", "pool_exhaustion", "cpu_saturation", "reset"]
    seconds: int = Field(default=30, ge=1, le=120)


@app.post("/control/fault")
def set_fault(body: Fault, x_demo_control: str = Header(default="")):
    token = os.environ.get("DEMO_CONTROL_TOKEN", "")
    if not token or not secrets.compare_digest(token, x_demo_control):
        raise HTTPException(403, "DEMO_CONTROLLER_ONLY")
    allowed = (
        {"payment_delay", "reset"}
        if SERVICE == "payment"
        else {"config_regression", "pool_exhaustion", "cpu_saturation", "reset"}
        if SERVICE == "checkout"
        else {"reset"}
    )
    if body.fault not in allowed:
        raise HTTPException(400, "FAULT_TARGET_INVALID")
    if current_fault() and body.fault != "reset":
        raise HTTPException(409, "Reset the active fault first")
    until = time.time() + body.seconds
    with state_lock:
        fault_state.update(
            fault=None if body.fault == "reset" else body.fault,
            until=until,
            revision=fault_state["revision"] + 1,
        )
    deployments.append(
        {
            "service": SERVICE,
            "revision": f"demo-{fault_state['revision'] + 1:03}",
            "timestamp": time.time(),
            "change": "Runtime configuration updated",
        }
    )
    if body.fault == "pool_exhaustion":
        threading.Thread(target=exhaust_pool, args=(until,), daemon=True).start()
    if body.fault == "cpu_saturation":
        threading.Thread(target=saturate_cpu, args=(until,), daemon=True).start()
    return {"scenario_id": secrets.token_hex(6), "expires_at": until, "revision": fault_state["revision"]}


@app.get("/telemetry/logs")
def search_logs():
    return {"records": [row for row in list(logs)[-40:] if time.time() - row["timestamp"] < 3600]}


@app.get("/telemetry/deployments")
def changes():
    return {"records": list(deployments)[-20:]}


@app.get("/telemetry/config")
def config():
    return {
        "previous": {"validation": "v1", "pool_size": 3},
        "current": {"validation": "v2" if current_fault() == "config_regression" else "v1", "pool_size": 3},
    }


@app.get("/telemetry/dependencies")
def dependencies():
    return {"checkout": ["payment", "inventory", "demo-db"]}


@app.get("/telemetry/runbooks")
def runbooks():
    return {
        "text": "Corroborate metrics with traces and logs. Propose no production changes. Demo controller changes require separate explicit approval."
    }
