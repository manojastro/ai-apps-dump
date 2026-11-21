from __future__ import annotations

import json
import math
import time
from contextlib import asynccontextmanager
from dataclasses import replace
from pathlib import Path
from threading import Lock
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .agents import AGENT_CATALOG
from .config import Settings, get_settings
from .database import Database
from .evaluation import AVAILABLE_VERSIONS, TOOL_CODES, Evaluator
from .schemas import ApprovalRequest, RegressionRequest, RunRequest
from .security import SecurityHeadersMiddleware, SlidingWindowRateLimiter, auth_dependency, make_rate_limit_middleware
from .simulator import SCENARIO_GROUND_TRUTH
from .workflow import ReliabilityWorkflow


class AppMetrics:
    def __init__(self):
        self.lock = Lock()
        self.requests = 0
        self.errors = 0
        self.workflow_runs = 0
        self.request_latency_ms = 0.0

    def observe(self, latency_ms: float, status_code: int) -> None:
        with self.lock:
            self.requests += 1
            self.request_latency_ms += latency_ms
            self.errors += int(status_code >= 500)


def create_app(database_path: Path | None = None) -> FastAPI:
    settings = get_settings()
    if database_path is not None:
        settings = replace(settings, database_path=database_path)
    database = Database(settings.database_path)
    metrics = AppMetrics()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        database.migrate()
        app.state.database = database
        app.state.workflow = ReliabilityWorkflow(database)
        app.state.evaluator = Evaluator(database)
        app.state.metrics = metrics
        yield

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Evidence-first evaluation and safety control plane for AI agents.",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key"],
    )
    limiter = SlidingWindowRateLimiter(settings.rate_limit_per_minute)
    app.middleware("http")(make_rate_limit_middleware(limiter))

    @app.middleware("http")
    async def instrument_requests(request, call_next):
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            metrics.observe((time.perf_counter() - started) * 1000, status_code)

    protected = auth_dependency(settings)
    static_dir = Path(__file__).with_name("static")
    app.mount("/assets", StaticFiles(directory=static_dir), name="assets")

    @app.get("/", include_in_schema=False)
    @app.get("/dashboard", include_in_schema=False)
    async def dashboard():
        return FileResponse(static_dir / "index.html")

    @app.get("/health", tags=["platform"])
    async def health():
        return {"status": "healthy", "service": "agent-reliability-platform", "version": app.version}

    @app.get("/ready", tags=["platform"])
    async def readiness():
        ready = database.ping()
        if not ready:
            raise HTTPException(status_code=503, detail="database unavailable")
        return {"status": "ready", "database": "sqlite", "llm_mode": settings.llm_mode}

    @app.get("/metrics", response_class=Response, tags=["platform"])
    async def prometheus_metrics():
        runs = database.query_one("SELECT COUNT(*) AS count FROM agent_runs") or {"count": 0}
        incidents = database.query_one("SELECT COUNT(*) AS count FROM incidents") or {"count": 0}
        average = metrics.request_latency_ms / metrics.requests if metrics.requests else 0
        body = "\n".join([
            "# HELP arp_http_requests_total Total HTTP requests.",
            "# TYPE arp_http_requests_total counter",
            f"arp_http_requests_total {metrics.requests}",
            "# HELP arp_http_errors_total Total server errors.",
            "# TYPE arp_http_errors_total counter",
            f"arp_http_errors_total {metrics.errors}",
            "# HELP arp_http_request_latency_ms_avg Average request latency.",
            "# TYPE arp_http_request_latency_ms_avg gauge",
            f"arp_http_request_latency_ms_avg {average:.3f}",
            "# HELP arp_agent_runs_total Persisted agent runs.",
            "# TYPE arp_agent_runs_total gauge",
            f"arp_agent_runs_total {runs['count']}",
            "# HELP arp_incidents_total Persisted incidents.",
            "# TYPE arp_incidents_total gauge",
            f"arp_incidents_total {incidents['count']}",
        ]) + "\n"
        return Response(content=body, media_type="text/plain; version=0.0.4")

    @app.get("/api/v1/platform", tags=["platform"])
    async def platform_info():
        return {
            "name": settings.app_name, "version": app.version,
            "llm_mode": settings.llm_mode, "llm_model": settings.llm_model,
            "persistence": "sqlite", "auth_mode": "api-key" if settings.api_key else "disabled-local",
        }

    @app.get("/api/v1/agents", tags=["agents"])
    async def agents():
        return [item.__dict__ for item in AGENT_CATALOG]

    @app.get("/api/v1/scenarios", tags=["demo"])
    async def scenarios():
        return [{"name": name, "ground_truth": sorted(labels)} for name, labels in SCENARIO_GROUND_TRUTH.items()]

    @app.post("/api/v1/demo/run", tags=["demo"], dependencies=[Depends(protected)])
    async def run_demo(request: RunRequest):
        try:
            result = app.state.workflow.run(request.scenario, request.agent_version)
            metrics.workflow_runs += 1
            return result.model_dump(mode="json")
        except Exception as exc:
            database.audit(incident_id=None, agent="Workflow Controller", tool="none", action="workflow_error", input_data=request.model_dump(), output_data={"error_type": type(exc).__name__}, decision="FAIL_CLOSED")
            raise HTTPException(status_code=500, detail="workflow failed safely") from exc

    @app.get("/api/v1/runs", tags=["investigations"])
    async def list_runs(limit: int = 50):
        if not 1 <= limit <= 200:
            raise HTTPException(status_code=422, detail="limit must be between 1 and 200")
        rows = database.query_all("SELECT run_id, agent_id, agent_version, scenario, status, started_at, completed_at, total_cost_usd, latency_ms FROM agent_runs ORDER BY created_at DESC LIMIT ?", (limit,))
        return rows

    @app.get("/api/v1/runs/{run_id}", tags=["investigations"])
    async def get_run(run_id: str):
        row = database.query_one("SELECT * FROM agent_runs WHERE run_id = ?", (run_id,))
        if not row:
            raise HTTPException(status_code=404, detail="run not found")
        row["trace"] = json.loads(row.pop("trace_json"))
        return row

    @app.get("/api/v1/incidents", tags=["investigations"])
    async def list_incidents(limit: int = 50):
        if not 1 <= limit <= 200:
            raise HTTPException(status_code=422, detail="limit must be between 1 and 200")
        return database.query_all("SELECT incident_id, run_id, severity, status, title, root_cause, confidence, created_at FROM incidents ORDER BY created_at DESC LIMIT ?", (limit,))

    @app.get("/api/v1/incidents/{incident_id}", tags=["investigations"])
    async def get_incident(incident_id: str):
        row = database.query_one("SELECT * FROM incidents WHERE incident_id = ?", (incident_id,))
        if not row:
            raise HTTPException(status_code=404, detail="incident not found")
        row["detections"] = json.loads(row.pop("detections_json"))
        row["rca"] = json.loads(row.pop("rca_json"))
        row["actions"] = database.query_all("SELECT action_id, action_type, risk, required_approval, status, created_at FROM actions WHERE incident_id = ?", (incident_id,))
        row["validations"] = [dict(item, result=json.loads(item.pop("result_json"))) for item in database.query_all("SELECT * FROM validations WHERE incident_id = ? ORDER BY created_at", (incident_id,))]
        return row

    @app.get("/api/v1/actions", tags=["governance"])
    async def list_actions():
        return database.query_all("SELECT action_id, incident_id, action_type, risk, required_approval, status, created_at, updated_at FROM actions ORDER BY created_at DESC")

    @app.post("/api/v1/actions/{action_id}/approval", tags=["governance"], dependencies=[Depends(protected)])
    async def approve_action(action_id: str, request: ApprovalRequest):
        try:
            return app.state.workflow.approve(action_id, request.approver, request.decision, request.reason)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/v1/actions/{action_id}/execute", tags=["governance"], dependencies=[Depends(protected)])
    async def execute_action(action_id: str):
        try:
            return app.state.workflow.execute(action_id)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/v1/evaluations/run", tags=["evaluation"], dependencies=[Depends(protected)])
    async def run_evaluation():
        return app.state.evaluator.run_detector_benchmark()

    @app.post("/api/v1/regression/compare", tags=["evaluation"], dependencies=[Depends(protected)])
    async def compare_versions(request: RegressionRequest):
        try:
            return app.state.evaluator.compare_versions(request.current_version, request.candidate_version)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/api/v1/evaluations", tags=["evaluation"])
    async def list_evaluations():
        rows = database.query_all("SELECT * FROM evaluations ORDER BY created_at DESC LIMIT 50")
        for row in rows:
            row["metrics"] = json.loads(row.pop("metrics_json"))
        return rows

    @app.get("/api/v1/audit", tags=["governance"])
    async def audit_log(limit: int = 50):
        if not 1 <= limit <= 200:
            raise HTTPException(status_code=422, detail="limit must be between 1 and 200")
        return database.query_all("SELECT event_id, timestamp, incident_id, agent, tool, action, decision, approval, execution_result, validation_result FROM audit_events ORDER BY timestamp DESC LIMIT ?", (limit,))

    @app.get("/api/v1/dashboard", tags=["dashboard"])
    async def dashboard_data():
        runs = database.query_all("SELECT * FROM agent_runs ORDER BY created_at DESC")
        all_incidents = database.query_all("SELECT * FROM incidents ORDER BY created_at DESC")
        incidents = all_incidents[:10]
        evaluations = database.query_all("SELECT evaluation_id, kind, subject, passed, metrics_json, created_at FROM evaluations ORDER BY created_at DESC LIMIT 5")
        latencies = sorted([row["latency_ms"] for row in runs])
        costs = [row["total_cost_usd"] for row in runs]
        passed = sum(row["status"] == "PASSED" for row in runs)
        scenario_count = max(len(runs), 1)
        success_count = max(passed, 1)
        return {
            "mode": settings.llm_mode,
            "fleet": {
                "total_runs": len(runs), "success_rate": round(passed / scenario_count, 3) if runs else 0,
                "cost_per_task": round(sum(costs) / scenario_count, 5) if runs else 0,
                "cost_per_success": round(sum(costs) / success_count, 5) if passed else 0,
                "p50_latency_ms": percentile(latencies, .50), "p95_latency_ms": percentile(latencies, .95),
                "tool_accuracy": label_derived_tool_accuracy(runs, all_incidents),
                "loop_rate": detection_rate(all_incidents, len(runs), "AGENT_LOOP"),
                "hallucinated_success_rate": detection_rate(all_incidents, len(runs), "HALLUCINATED_SUCCESS"),
                "failed_trajectories": len(runs) - passed,
            },
            "incidents": [{key: row[key] for key in ("incident_id", "run_id", "severity", "status", "title", "root_cause", "confidence", "created_at")} for row in incidents],
            "actions": database.query_all("SELECT action_id, incident_id, action_type, risk, required_approval, status FROM actions ORDER BY created_at DESC LIMIT 10"),
            "evaluations": [dict(row, metrics=json.loads(row.pop("metrics_json"))) for row in evaluations],
            "available_versions": list(AVAILABLE_VERSIONS),
        }

    return app


def percentile(values: list[int], p: float) -> int:
    if not values:
        return 0
    index = max(0, math.ceil(len(values) * p) - 1)
    return values[index]


def detection_rate(incidents: list[dict[str, Any]], run_count: int, code: str) -> float:
    matches = sum(
        any(item.get("code") == code for item in json.loads(row["detections_json"]))
        for row in incidents
    )
    return round(matches / max(run_count, 1), 3)


def label_derived_tool_accuracy(runs: list[dict[str, Any]], incidents: list[dict[str, Any]]) -> float:
    if not runs:
        return 0
    detected_by_run = {
        row["run_id"]: {item.get("code") for item in json.loads(row["detections_json"])}
        for row in incidents
    }
    correct = 0
    for run in runs:
        predicted = detected_by_run.get(run["run_id"], set()) & TOOL_CODES
        expected = SCENARIO_GROUND_TRUTH.get(run["scenario"], set()) & TOOL_CODES
        correct += int(predicted == expected)
    return round(correct / len(runs), 3)


app = create_app()
