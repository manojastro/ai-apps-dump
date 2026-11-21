from __future__ import annotations

import os
from pathlib import Path
from threading import Lock
from time import perf_counter
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from .database import Repository
from .models import ApprovalRequest, EvaluationSummary, ScenarioInfo
from .simulator import SCENARIOS
from .workflow import IncidentNotFound, ReliabilityWorkflow, WorkflowConflict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class RequestMetrics:
    def __init__(self) -> None:
        self.requests = 0
        self.errors = 0
        self.total_latency = 0.0
        self.lock = Lock()

    def observe(self, status_code: int, latency_seconds: float) -> None:
        with self.lock:
            self.requests += 1
            self.errors += int(status_code >= 500)
            self.total_latency += latency_seconds


def create_app(db_path: str | Path | None = None) -> FastAPI:
    database_path = Path(db_path or os.getenv("DATABASE_PATH", PROJECT_ROOT / "data" / "streaming.db"))
    repository = Repository(database_path)
    repository.initialize()
    workflow = ReliabilityWorkflow(repository)
    request_metrics = RequestMetrics()
    auth_mode = os.getenv("AUTH_MODE", "open")
    api_key = os.getenv("API_KEY", "")
    approver_api_key = os.getenv("APPROVER_API_KEY", "")
    executor_api_key = os.getenv("EXECUTOR_API_KEY", "")
    if auth_mode == "api_key" and (
        not api_key or not approver_api_key or not executor_api_key
        or len({api_key, approver_api_key, executor_api_key}) != 3
    ):
        raise RuntimeError("api_key mode requires three distinct viewer, approver, and executor keys")

    app = FastAPI(
        title="Kafka Streaming Reliability Agent",
        version="0.1.0",
        description="Evidence-based RCA and approval-gated remediation for synthetic Kafka incidents.",
    )
    app.state.repository = repository
    app.state.workflow = workflow
    app.state.request_metrics = request_metrics
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:8104").split(",")],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key"],
    )

    @app.middleware("http")
    async def observe_requests(request: Request, call_next):
        started = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            request_metrics.observe(500, perf_counter() - started)
            raise
        request_metrics.observe(response.status_code, perf_counter() - started)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    def authorize(x_api_key: Annotated[str | None, Header()] = None) -> None:
        valid_keys = {api_key, approver_api_key, executor_api_key}
        if auth_mode == "api_key" and x_api_key not in valid_keys:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid API key")

    def require_approver(x_api_key: Annotated[str | None, Header()] = None) -> str:
        if auth_mode == "open":
            return "open-demo"
        if x_api_key != approver_api_key:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="approver role required")
        return "authenticated-approver"

    def require_executor(x_api_key: Annotated[str | None, Header()] = None) -> str:
        if auth_mode == "open":
            return "open-demo"
        if x_api_key != executor_api_key:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="executor role required")
        return "authenticated-executor"

    @app.exception_handler(IncidentNotFound)
    async def incident_not_found(_: Request, exc: IncidentNotFound):
        return JSONResponse(status_code=404, content={"detail": f"incident {exc.args[0]} not found"})

    @app.exception_handler(WorkflowConflict)
    async def workflow_conflict(_: Request, exc: WorkflowConflict):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "healthy", "service": "kafka-streaming-reliability-agent", "llm_mode": "mock"}

    @app.get("/ready")
    def ready() -> dict[str, str]:
        try:
            repository.counts()
        except Exception as exc:
            raise HTTPException(status_code=503, detail="database unavailable") from exc
        return {"status": "ready", "adapter": "synthetic-kafka", "database": "sqlite"}

    @app.get("/metrics", response_class=PlainTextResponse)
    def metrics() -> str:
        counts = repository.counts()
        evaluation = repository.evaluation_summary()
        average_latency = (request_metrics.total_latency / request_metrics.requests
                           if request_metrics.requests else 0.0)
        return "\n".join([
            "# HELP kafka_agent_incidents_total Investigated synthetic incidents.",
            "# TYPE kafka_agent_incidents_total counter",
            f"kafka_agent_incidents_total {counts['incidents']}",
            "# HELP kafka_agent_validations_total Successful remediation validations.",
            "# TYPE kafka_agent_validations_total counter",
            f"kafka_agent_validations_total {counts['validated']}",
            "# HELP kafka_agent_rca_accuracy Root-cause classification accuracy.",
            "# TYPE kafka_agent_rca_accuracy gauge",
            f"kafka_agent_rca_accuracy {evaluation['rca_accuracy']}",
            "# HELP kafka_agent_consumer_lag_detection_rate Labeled lag incidents correctly detected.",
            "# TYPE kafka_agent_consumer_lag_detection_rate gauge",
            f"kafka_agent_consumer_lag_detection_rate {evaluation['consumer_lag_detection_rate']}",
            "# HELP kafka_agent_mttd_milliseconds_mean Mean simulated incident time to detection.",
            "# TYPE kafka_agent_mttd_milliseconds_mean gauge",
            f"kafka_agent_mttd_milliseconds_mean {evaluation['mean_mttd_ms']}",
            "# HELP kafka_agent_mttr_milliseconds_mean Mean simulated incident time to validated remediation.",
            "# TYPE kafka_agent_mttr_milliseconds_mean gauge",
            f"kafka_agent_mttr_milliseconds_mean {evaluation['mean_mttr_ms']}",
            "# HELP http_requests_total HTTP requests observed by this process.",
            "# TYPE http_requests_total counter",
            f"http_requests_total {request_metrics.requests}",
            "# HELP http_request_latency_seconds_mean Mean HTTP request latency.",
            "# TYPE http_request_latency_seconds_mean gauge",
            f"http_request_latency_seconds_mean {average_latency:.6f}",
            "",
        ])

    @app.get("/api/v1/scenarios", response_model=list[ScenarioInfo])
    def scenarios(_: None = Depends(authorize)) -> list[ScenarioInfo]:
        return [ScenarioInfo(name=item.name, description=item.description,
                             ground_truth_root_cause=item.root_cause) for item in SCENARIOS.values()]

    @app.post("/api/v1/scenarios/{scenario}/inject", status_code=201)
    def inject(scenario: str, _: None = Depends(authorize)):
        if scenario not in SCENARIOS:
            raise HTTPException(status_code=404, detail="unknown scenario")
        return workflow.investigate(scenario)

    @app.get("/api/v1/incidents")
    def incidents(limit: int = Query(default=50, ge=1, le=200), _: None = Depends(authorize)):
        return repository.list_incidents(limit)

    @app.get("/api/v1/incidents/{incident_id}")
    def incident(incident_id: str, _: None = Depends(authorize)):
        return workflow.get(incident_id)

    @app.post("/api/v1/incidents/{incident_id}/approval")
    def approve(incident_id: str, approval: ApprovalRequest, actor: str = Depends(require_approver)):
        effective_approval = (approval.model_copy(update={"approved_by": actor})
                              if auth_mode == "api_key" else approval)
        return workflow.approve(incident_id, effective_approval)

    @app.post("/api/v1/incidents/{incident_id}/execute")
    def execute(incident_id: str, _: str = Depends(require_executor)):
        return workflow.execute_and_validate(incident_id)

    @app.get("/api/v1/evaluations/summary", response_model=EvaluationSummary)
    def evaluation(_: None = Depends(authorize)):
        return repository.evaluation_summary()

    @app.get("/api/v1/activity")
    def activity(limit: int = Query(default=50, ge=1, le=200), _: None = Depends(authorize)):
        return repository.activity(limit)

    frontend = PROJECT_ROOT / "frontend"
    app.mount("/assets", StaticFiles(directory=frontend), name="assets")

    @app.get("/", include_in_schema=False)
    def dashboard():
        return FileResponse(frontend / "index.html")

    return app


app = create_app()
