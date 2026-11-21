from __future__ import annotations

import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.catalog import SCENARIOS, get_scenario
from app.repository import Repository
from app.schemas import ApprovalRequest, AuthPrincipal, IncidentCreate
from app.seed import seed_demo
from app.settings import PROJECT_ROOT, Settings, get_settings
from services.agent import RemediationWorkflow
from services.agent.model import create_model
from services.policy import PolicyEngine
from services.tools import create_sandbox


def build_components(settings: Settings):
    repo = Repository(settings.database_url, PROJECT_ROOT / "migrations" / "001_initial.sql")
    repo.initialize()
    policy = PolicyEngine(settings.policy_path, repo)
    sandbox = create_sandbox(settings.sandbox_mode, settings.allowed_namespace)
    workflow = RemediationWorkflow(repo, policy, sandbox, create_model(settings.llm_provider))
    return repo, workflow, sandbox


def create_app(settings: Settings | None = None, *, seed: bool | None = None) -> FastAPI:
    config = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        repository, workflow, sandbox = build_components(config)
        app.state.settings = config
        app.state.repository = repository
        app.state.workflow = workflow
        app.state.sandbox = sandbox
        if config.seed_on_start if seed is None else seed:
            seed_demo(repository, workflow)
        yield
        repository.close()

    app = FastAPI(title="Self-Healing Remediation Agent", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[item.strip() for item in config.cors_origins.split(",")],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "X-Request-ID"],
    )
    request_times: dict[str, deque[float]] = defaultdict(deque)

    @app.middleware("http")
    async def operational_middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))[:100]
        now, key = time.monotonic(), request.client.host if request.client else "test"
        bucket = request_times[key]
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= 120:
            return PlainTextResponse("rate limit exceeded", status_code=429)
        bucket.append(now)
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = f"{(time.perf_counter() - started) * 1000:.2f}"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    return _register_routes(app)


def _principal(request: Request, authorization: Annotated[str | None, Header()] = None) -> AuthPrincipal:
    settings: Settings = request.app.state.settings
    token = (authorization or "").removeprefix("Bearer ")
    if token == settings.operator_token:
        return AuthPrincipal(subject="demo-operator", role="operator")
    if token == settings.viewer_token:
        return AuthPrincipal(subject="demo-viewer", role="viewer")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="valid bearer token required")


def _operator(principal: Annotated[AuthPrincipal, Depends(_principal)]) -> AuthPrincipal:
    if principal.role not in {"operator", "admin"}:
        raise HTTPException(status_code=403, detail="operator role required")
    return principal


def _csrf(request: Request, x_csrf_token: Annotated[str | None, Header()] = None) -> None:
    if x_csrf_token != request.app.state.settings.csrf_token:
        raise HTTPException(status_code=403, detail="valid CSRF token required")


def _register_routes(app: FastAPI) -> FastAPI:
    @app.get("/health/live")
    def live():
        return {"status": "ok"}

    @app.get("/health/ready")
    def ready(request: Request):
        request.app.state.repository.one("SELECT 1 AS ok")
        return {"status": "ready", "sandbox": request.app.state.settings.sandbox_mode}

    @app.get("/api/scenarios")
    def scenarios(_: Annotated[AuthPrincipal, Depends(_principal)]):
        return [scenario.model_dump(mode="json") for scenario in SCENARIOS.values()]

    @app.get("/api/incidents")
    def incidents(request: Request, _: Annotated[AuthPrincipal, Depends(_principal)]):
        return request.app.state.repository.list_incidents()

    @app.get("/api/incidents/{incident_id}")
    def incident_detail(incident_id: str, request: Request, _: Annotated[AuthPrincipal, Depends(_principal)]):
        try:
            return request.app.state.repository.incident_detail(incident_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="incident not found") from None

    @app.post("/api/incidents", status_code=201, dependencies=[Depends(_csrf)])
    def inject(payload: IncidentCreate, request: Request, principal: Annotated[AuthPrincipal, Depends(_operator)]):
        try:
            scenario = get_scenario(payload.scenario).model_dump(mode="json")
        except KeyError:
            raise HTTPException(status_code=422, detail="unknown scenario") from None
        incident = request.app.state.repository.create_incident(scenario, payload.force_verification_failure)
        request.app.state.repository.audit(incident["id"], "incident.injected", principal.subject, payload.model_dump())
        request.app.state.workflow.run(incident["id"])
        return request.app.state.repository.incident_detail(incident["id"])

    @app.post("/api/incidents/{incident_id}/approval", dependencies=[Depends(_csrf)])
    def approve(incident_id: str, payload: ApprovalRequest, request: Request,
                principal: Annotated[AuthPrincipal, Depends(_operator)]):
        try:
            incident = request.app.state.repository.get_incident(incident_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="incident not found") from None
        if incident["status"] != "PENDING_APPROVAL":
            raise HTTPException(status_code=409, detail="incident is not awaiting approval")
        request.app.state.repository.record_approval(incident_id, payload.decision.value, principal.subject, payload.comment)
        request.app.state.workflow.run(incident_id)
        return request.app.state.repository.incident_detail(incident_id)

    @app.post("/api/admin/seed", dependencies=[Depends(_csrf)])
    def reseed(request: Request, _: Annotated[AuthPrincipal, Depends(_operator)]):
        ids = seed_demo(request.app.state.repository, request.app.state.workflow, force=True)
        return {"seeded": len(ids), "incident_ids": ids}

    @app.get("/api/dashboard")
    def dashboard(request: Request, _: Annotated[AuthPrincipal, Depends(_principal)]):
        return request.app.state.repository.dashboard()

    @app.get("/api/audit")
    def audit(request: Request, _: Annotated[AuthPrincipal, Depends(_principal)]):
        return request.app.state.repository.all("SELECT * FROM audit_events ORDER BY created_at DESC LIMIT 200")

    @app.get("/metrics", response_class=PlainTextResponse)
    def metrics(request: Request):
        dashboard = request.app.state.repository.dashboard()
        lines = [
            "# HELP selfheal_incidents_total Total detected incidents.",
            "# TYPE selfheal_incidents_total gauge",
            f"selfheal_incidents_total {dashboard['total_incidents']}",
            "# HELP selfheal_active_incidents Current active incidents.",
            "# TYPE selfheal_active_incidents gauge",
            f"selfheal_active_incidents {dashboard['active_incidents']}",
            "# HELP selfheal_auto_resolution_rate Auto-resolution ratio.",
            "# TYPE selfheal_auto_resolution_rate gauge",
            f"selfheal_auto_resolution_rate {dashboard['auto_resolution_rate']}",
            f"selfheal_actions_blocked_total {dashboard['actions_blocked']}",
            f"selfheal_rollback_rate {dashboard['rollback_rate']}",
            f"selfheal_mttr_seconds {dashboard['mttr_seconds']}",
        ]
        return "\n".join(lines) + "\n"

    return app


app = create_app()
