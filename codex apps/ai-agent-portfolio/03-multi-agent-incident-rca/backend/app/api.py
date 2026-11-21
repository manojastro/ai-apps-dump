from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
import os

from .config import settings
from .evaluation import evaluate_cases, load_cases
from .fixtures import SCENARIOS, default_incidents
from .graph import DependencyGraph
from .models import EvaluationSummary, Incident, IncidentCreate, Investigation, RCA
from .observability import request_span
from .repository import Repository
from .security import Principal, get_principal, require_admin, require_investigator
from .workflow import InvestigationEngine, new_incident_id, validate_citations

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

    INVESTIGATIONS = Counter(
        "rca_investigations_total", "Completed investigations", ["scenario", "result"]
    )
    INVESTIGATION_DURATION = Histogram(
        "rca_investigation_duration_seconds", "Investigation duration", ["scenario"]
    )
except ImportError:  # pragma: no cover - dependency is present in production image
    CONTENT_TYPE_LATEST = "text/plain"
    INVESTIGATIONS = INVESTIGATION_DURATION = None


repository = Repository(settings.database_url)
engine = InvestigationEngine(repository)
dependency_graph = DependencyGraph()
evaluation_cache: EvaluationSummary | None = None


def seed_if_empty() -> None:
    if repository.list_incidents():
        return
    for index, payload in enumerate(default_incidents(), start=1):
        repository.save_incident(Incident(id=f"INC-DEMO-{index:02d}", **payload))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    seed_if_empty()
    if settings.neo4j_uri != "memory://":
        dependency_graph.sync_neo4j(
            settings.neo4j_uri,
            os.getenv("NEO4J_USER", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "rca03-local-password"),
        )
    yield


app = FastAPI(
    title="Multi-Agent Incident RCA API",
    version="0.1.0",
    description=(
        "Supervisor/worker incident investigation with immutable evidence IDs, ranked hypotheses, "
        "a critic pass, and a strict citation gate."
    ),
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_methods=["GET", "POST", "PUT", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "X-User", "X-Role"],
)


@app.middleware("http")
async def trace_requests(request: Request, call_next):
    with request_span(f"{request.method} {request.url.path}"):
        response = await call_next(request)
    response.headers["X-RCA-Observability"] = "otel"
    return response


def find_incident(incident_id: str) -> Incident:
    incident = repository.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="incident not found")
    return incident


def find_investigation(incident_id: str) -> Investigation:
    investigation = repository.get_investigation(incident_id)
    if not investigation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="incident has not completed an investigation",
        )
    return investigation


@app.get("/healthz", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok", "mode": settings.llm_mode}


@app.get("/readyz", tags=["operations"])
def ready() -> dict[str, Any]:
    return {
        "status": "ready",
        "database": "connected",
        "graph": "memory" if settings.neo4j_uri == "memory://" else "neo4j",
        "llm": settings.llm_mode,
    }


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    if INVESTIGATIONS is None:
        return Response("rca_up 1\n", media_type="text/plain")
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/scenarios", tags=["demo"])
def scenarios() -> list[dict[str, str]]:
    return [
        {
            "id": scenario,
            "title": config["title"],
            "category": config["category"],
            "component": config["component"],
        }
        for scenario, config in SCENARIOS.items()
    ]


@app.get("/api/v1/incidents", response_model=list[Incident], tags=["incidents"])
def list_incidents() -> list[Incident]:
    return repository.list_incidents()


@app.post(
    "/api/v1/incidents",
    response_model=Incident,
    status_code=status.HTTP_201_CREATED,
    tags=["incidents"],
)
def create_incident(
    payload: IncidentCreate,
    principal: Annotated[Principal, Depends(get_principal)],
) -> Incident:
    require_investigator(principal)
    if payload.scenario not in SCENARIOS:
        raise HTTPException(status_code=422, detail="unknown scenario")
    incident = repository.save_incident(Incident(id=new_incident_id(), **payload.model_dump()))
    repository.audit(principal.subject, "incident.create", incident.id, {"scenario": incident.scenario})
    return incident


@app.get("/api/v1/incidents/{incident_id}", response_model=Incident, tags=["incidents"])
def get_incident(incident_id: str) -> Incident:
    return find_incident(incident_id)


@app.post(
    "/api/v1/incidents/{incident_id}/investigate",
    response_model=Investigation,
    tags=["investigations"],
)
async def investigate(
    incident_id: str,
    principal: Annotated[Principal, Depends(get_principal)],
) -> Investigation:
    require_investigator(principal)
    incident = find_incident(incident_id)
    repository.audit(principal.subject, "investigation.start", incident.id, {})
    started = datetime.now(UTC)
    try:
        result = await engine.investigate(incident)
        if INVESTIGATIONS is not None:
            INVESTIGATIONS.labels(incident.scenario, "success").inc()
            INVESTIGATION_DURATION.labels(incident.scenario).observe(
                (datetime.now(UTC) - started).total_seconds()
            )
        repository.audit(
            principal.subject,
            "investigation.complete",
            incident.id,
            {"evidence_count": len(result.evidence), "critic_overturned": result.critic.overturned},
        )
        return result
    except Exception as exc:
        if INVESTIGATIONS is not None:
            INVESTIGATIONS.labels(incident.scenario, "failed").inc()
        repository.audit(principal.subject, "investigation.failed", incident.id, {"error": str(exc)})
        raise HTTPException(status_code=500, detail="investigation failed safely") from exc


@app.get(
    "/api/v1/incidents/{incident_id}/investigation",
    response_model=Investigation,
    tags=["investigations"],
)
def get_investigation(incident_id: str) -> Investigation:
    find_incident(incident_id)
    return find_investigation(incident_id)


@app.get("/api/v1/incidents/{incident_id}/evidence", tags=["evidence"])
def evidence(incident_id: str):
    return find_investigation(incident_id).evidence


@app.get("/api/v1/incidents/{incident_id}/timeline", tags=["evidence"])
def timeline(incident_id: str):
    return find_investigation(incident_id).timeline


@app.get("/api/v1/incidents/{incident_id}/hypotheses", tags=["investigations"])
def hypotheses(incident_id: str):
    investigation = find_investigation(incident_id)
    return {"hypotheses": investigation.hypotheses, "critic": investigation.critic}


@app.get("/api/v1/incidents/{incident_id}/rca", response_model=RCA, tags=["rca"])
def get_rca(incident_id: str) -> RCA:
    return find_investigation(incident_id).rca


@app.put("/api/v1/incidents/{incident_id}/rca", response_model=RCA, tags=["rca"])
def update_rca(
    incident_id: str,
    payload: RCA,
    principal: Annotated[Principal, Depends(get_principal)],
) -> RCA:
    require_investigator(principal)
    investigation = find_investigation(incident_id)
    if payload.incident_id != incident_id:
        raise HTTPException(status_code=422, detail="incident ID mismatch")
    try:
        validate_citations(payload, investigation.evidence)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    updated = investigation.model_copy(update={"rca": payload})
    repository.save_investigation(updated)
    repository.audit(principal.subject, "rca.update", incident_id, {"citation_gate": "passed"})
    return payload


@app.get("/api/v1/graph", tags=["topology"])
def graph(service: str | None = Query(default=None, max_length=80)):
    return dependency_graph.snapshot(service)


@app.post("/api/v1/evaluations/run", response_model=EvaluationSummary, tags=["evaluation"])
async def run_evaluation(
    principal: Annotated[Principal, Depends(get_principal)],
) -> EvaluationSummary:
    require_admin(principal)
    global evaluation_cache
    evaluation_cache, _ = await evaluate_cases(load_cases())
    repository.audit(principal.subject, "evaluation.run", "evaluation", evaluation_cache.model_dump())
    return evaluation_cache


@app.get("/api/v1/evaluations/summary", tags=["evaluation"])
async def evaluation_summary():
    global evaluation_cache
    if evaluation_cache is None:
        evaluation_cache, _ = await evaluate_cases(load_cases())
    return evaluation_cache


@app.get("/api/v1/audit", tags=["security"])
def audit_log(
    principal: Annotated[Principal, Depends(get_principal)],
    limit: int = Query(default=100, ge=1, le=500),
):
    require_admin(principal)
    return repository.list_audit(limit)
