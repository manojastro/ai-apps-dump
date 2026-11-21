from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from time import perf_counter
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from .agents import AGENTS
from .database import Repository
from .models import ApprovalRequest, EvaluationSummary, ScenarioInfo
from .simulator import SCENARIOS
from .workflow import IncidentNotFound, RemediationWorkflow, WorkflowConflict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Principal:
    subject: str
    role: str
    demo_only: bool = False


class RequestMetrics:
    def __init__(self) -> None:
        self.requests = 0
        self.errors = 0
        self.latency = 0.0
        self.lock = Lock()

    def observe(self, status_code: int, seconds: float) -> None:
        with self.lock:
            self.requests += 1
            self.errors += int(status_code >= 500)
            self.latency += seconds


def create_app(db_path: str | Path | None = None, workspace_root: str | Path | None = None) -> FastAPI:
    repository = Repository(Path(db_path or os.getenv("DATABASE_PATH", PROJECT_ROOT / "data" / "security.db")))
    repository.initialize()
    workflow = RemediationWorkflow(
        repository, workspace_root or os.getenv("WORKSPACE_ROOT", PROJECT_ROOT / "data" / "workspaces")
    )
    metrics_state = RequestMetrics()
    auth_mode = os.getenv("AUTH_MODE", "open").lower()
    if auth_mode not in {"open", "api_key"}:
        raise RuntimeError("AUTH_MODE must be 'open' (demo-only) or 'api_key'")
    if auth_mode == "open":
        demo_approver_key = os.getenv("DEMO_APPROVER_API_KEY", "forgeguard-local-demo-approver")
        demo_executor_key = os.getenv("DEMO_EXECUTOR_API_KEY", "forgeguard-local-demo-executor")
        if not demo_approver_key or not demo_executor_key or demo_approver_key == demo_executor_key:
            raise RuntimeError("open demo mode requires distinct approver and executor credentials")
        credentials = {
            demo_approver_key: Principal(
                "local-demo-approver", "approver", True
            ),
            demo_executor_key: Principal(
                "local-demo-executor", "executor", True
            ),
        }
    else:
        configured = {
            "viewer": os.getenv("VIEWER_API_KEY", ""),
            "approver": os.getenv("APPROVER_API_KEY", ""),
            "executor": os.getenv("EXECUTOR_API_KEY", ""),
        }
        if not all(configured[role] for role in ("viewer", "approver", "executor")):
            raise RuntimeError("api_key mode requires distinct VIEWER, APPROVER, and EXECUTOR API keys")
        if len(configured.values()) != len(set(configured.values())):
            raise RuntimeError("identity credentials must be distinct")
        credentials = {
            credential: Principal(f"configured-{role}", role)
            for role, credential in configured.items() if credential
        }
    app = FastAPI(
        title="DevSecOps Remediation Agent", version="0.1.0",
        description="Approval-gated vulnerability remediation with static rescan and regression validation.",
    )
    app.state.repository, app.state.workflow = repository, workflow
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[item.strip() for item in os.getenv("CORS_ORIGINS", "http://localhost:8105").split(",")],
        allow_credentials=False, allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key"],
    )

    @app.middleware("http")
    async def observe(request: Request, call_next):
        started = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            metrics_state.observe(500, perf_counter() - started)
            raise
        metrics_state.observe(response.status_code, perf_counter() - started)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'"
        )
        return response

    def authorize(x_api_key: Annotated[str | None, Header()] = None) -> Principal:
        if x_api_key and x_api_key in credentials:
            return credentials[x_api_key]
        if auth_mode == "open" and x_api_key is None:
            return Principal("anonymous-local-demo-viewer", "viewer", True)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or missing identity credential")

    def authorize_approver(principal: Principal = Depends(authorize)) -> Principal:
        if principal.role != "approver":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="verified approver credential required")
        return principal

    def authorize_executor(principal: Principal = Depends(authorize)) -> Principal:
        if principal.role != "executor":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="verified executor credential required")
        return principal

    @app.exception_handler(IncidentNotFound)
    async def not_found(_: Request, exc: IncidentNotFound):
        return JSONResponse(status_code=404, content={"detail": f"incident {exc.args[0]} not found"})

    @app.exception_handler(WorkflowConflict)
    async def conflict(_: Request, exc: WorkflowConflict):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "healthy", "service": "devsecops-remediation-agent", "llm_mode": "mock",
                "auth_mode": "open-demo-only" if auth_mode == "open" else "api_key"}

    @app.get("/ready")
    def ready() -> dict[str, str]:
        try:
            repository.counts()
        except Exception as exc:
            raise HTTPException(status_code=503, detail="database unavailable") from exc
        return {"status": "ready", "scanner": "deterministic", "executor": "safe-exact-patch"}

    @app.get("/metrics", response_class=PlainTextResponse)
    def metrics() -> str:
        summary = repository.evaluation_summary()
        mean_latency = metrics_state.latency / metrics_state.requests if metrics_state.requests else 0.0
        return "\n".join([
            "# HELP devsecops_investigations_total Persisted security investigations.",
            "# TYPE devsecops_investigations_total counter",
            f"devsecops_investigations_total {summary['investigations']}",
            "# HELP devsecops_remediation_success_rate Successful attempted remediations.",
            "# TYPE devsecops_remediation_success_rate gauge",
            f"devsecops_remediation_success_rate {summary['remediation_success_rate']}",
            "# HELP devsecops_security_regressions_total Detected security regressions.",
            "# TYPE devsecops_security_regressions_total counter",
            f"devsecops_security_regressions_total {summary['security_regressions']}",
            "# HELP http_request_latency_seconds_mean Mean process HTTP request latency.",
            "# TYPE http_request_latency_seconds_mean gauge",
            f"http_request_latency_seconds_mean {mean_latency:.6f}", "",
        ])

    @app.get("/api/v1/scenarios", response_model=list[ScenarioInfo])
    def scenarios(_: Principal = Depends(authorize)) -> list[ScenarioInfo]:
        return [ScenarioInfo(name=item.name, title=item.title, cwe=item.cwe, description=item.description)
                for item in SCENARIOS.values()]

    @app.get("/api/v1/agents")
    def agents(_: Principal = Depends(authorize)):
        return [agent.model_dump() for agent in AGENTS]

    @app.post("/api/v1/scenarios/{scenario}/scan", status_code=201)
    def scan(scenario: str, _: Principal = Depends(authorize)):
        if scenario not in SCENARIOS:
            raise HTTPException(status_code=404, detail="unknown scenario")
        return workflow.investigate(scenario)

    @app.get("/api/v1/incidents")
    def incidents(limit: int = Query(default=50, ge=1, le=200), _: Principal = Depends(authorize)):
        return repository.list_incidents(limit)

    @app.get("/api/v1/incidents/{incident_id}")
    def incident(incident_id: str, _: Principal = Depends(authorize)):
        return workflow.get(incident_id)

    @app.post("/api/v1/incidents/{incident_id}/approval")
    def approve(
        incident_id: str,
        request: ApprovalRequest,
        principal: Principal = Depends(authorize_approver),
    ):
        return workflow.approve(
            incident_id, request, approved_by=principal.subject, approver_role=principal.role
        )

    @app.post("/api/v1/incidents/{incident_id}/remediate")
    def remediate(incident_id: str, principal: Principal = Depends(authorize_executor)):
        return workflow.remediate_and_validate(
            incident_id, executed_by=principal.subject, executor_role=principal.role
        )

    @app.get("/api/v1/evaluations/summary", response_model=EvaluationSummary)
    def evaluation(_: Principal = Depends(authorize)):
        return repository.evaluation_summary()

    @app.get("/api/v1/activity")
    def activity(limit: int = Query(default=50, ge=1, le=200), _: Principal = Depends(authorize)):
        return repository.activity(limit)

    frontend = PROJECT_ROOT / "frontend"
    app.mount("/assets", StaticFiles(directory=frontend), name="assets")

    @app.get("/", include_in_schema=False)
    def dashboard():
        return FileResponse(frontend / "index.html")

    return app


app = create_app()
