from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .engine import EvaluationEngine, compare_runs
from .gate import apply_gate
from .models import GateConfig, TestCase
from .store import Database
from .targets import DemoAgentTarget, HttpTarget

database = Database()


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.initialize()
    database.seed_demo()
    yield


app = FastAPI(
    title="Agent Evaluation + CI Regression Harness",
    version="0.1.0",
    lifespan=lifespan,
    description="Dataset, experiment, comparison, and CI-quality-gate API.",
)
app.add_middleware(
    CORSMiddleware, allow_origins=["http://localhost:3004"], allow_credentials=False,
    allow_methods=["*"], allow_headers=["*"],
)


class ProjectCreate(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=2, max_length=120)


class DatasetCreate(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9-]+$")
    project_id: str
    name: str
    cases: list[dict] = Field(min_length=1)


class RunCreate(BaseModel):
    dataset_id: str = "demo-200"
    mode: str = Field(default="good", pattern="^(good|bad)$")
    http_url: str | None = None
    limit: int | None = Field(default=None, ge=1, le=10000)


class GateRequest(BaseModel):
    candidate_id: str
    baseline_id: str | None = None
    config: dict = Field(default_factory=dict)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "evalharness-api"}


@app.get("/ready")
def ready() -> dict:
    database.rows("SELECT 1 AS ready")
    return {"status": "ready"}


@app.get("/api/projects")
def projects() -> list[dict]:
    return database.rows("SELECT * FROM projects ORDER BY name")


@app.post("/api/projects", status_code=201)
def create_project(request: ProjectCreate) -> dict:
    try:
        database.execute(
            "INSERT INTO projects (id,name,created_at) VALUES (?,?,?)",
            (request.id, request.name, datetime.now(UTC).isoformat()),
        )
    except Exception as exc:
        raise HTTPException(409, "project already exists") from exc
    return request.model_dump()


@app.get("/api/datasets")
def datasets(project_id: str | None = None) -> list[dict]:
    if project_id:
        return database.rows(
            "SELECT d.*, COUNT(t.id) AS case_count FROM datasets d LEFT JOIN test_cases t ON t.dataset_id=d.id WHERE d.project_id=? GROUP BY d.id,d.project_id,d.name,d.version,d.created_at ORDER BY d.created_at DESC",
            (project_id,),
        )
    return database.rows(
        "SELECT d.*, COUNT(t.id) AS case_count FROM datasets d LEFT JOIN test_cases t ON t.dataset_id=d.id GROUP BY d.id,d.project_id,d.name,d.version,d.created_at ORDER BY d.created_at DESC"
    )


@app.post("/api/datasets", status_code=201)
def create_dataset(request: DatasetCreate) -> dict:
    cases = [TestCase.from_dict(value) for value in request.cases]
    if any(not case.id or not case.user_input for case in cases):
        raise HTTPException(422, "each case requires id and user_input")
    database.save_dataset(cases, request.id, request.name, request.project_id)
    return {"id": request.id, "case_count": len(cases)}


@app.get("/api/datasets/{dataset_id}/cases")
def cases(dataset_id: str, limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)) -> dict:
    all_cases = database.get_cases(dataset_id)
    return {"total": len(all_cases), "items": [case.to_dict() for case in all_cases[offset:offset + limit]]}


@app.post("/api/runs", status_code=201)
def create_run(request: RunCreate) -> dict:
    evaluation_cases = database.get_cases(request.dataset_id)
    if not evaluation_cases:
        raise HTTPException(404, "dataset not found or empty")
    if request.limit:
        evaluation_cases = evaluation_cases[:request.limit]
    target = HttpTarget(request.http_url) if request.http_url else DemoAgentTarget(request.mode)
    report = EvaluationEngine().run(evaluation_cases, target, dataset_id=request.dataset_id)
    database.save_run(report)
    return report.to_dict()


@app.get("/api/runs")
def runs() -> list[dict]:
    values = database.list_runs()
    for value in values:
        value["aggregate"] = json.loads(value["aggregate"])
    return values


@app.get("/api/runs/{run_id}")
def run_detail(run_id: str) -> dict:
    report = database.get_run(run_id)
    if not report:
        raise HTTPException(404, "run not found")
    return report.to_dict()


@app.post("/api/runs/{run_id}/baseline")
def mark_baseline(run_id: str) -> dict:
    report = database.get_run(run_id)
    if not report:
        raise HTTPException(404, "run not found")
    database.mark_baseline(report.project_id, run_id)
    return {"project_id": report.project_id, "baseline_run_id": run_id}


@app.get("/api/compare")
def compare(candidate_id: str, baseline_id: str | None = None) -> dict:
    candidate = database.get_run(candidate_id)
    if not candidate:
        raise HTTPException(404, "candidate not found")
    baseline = database.get_run(baseline_id) if baseline_id else database.get_baseline(candidate.project_id)
    if not baseline:
        raise HTTPException(404, "baseline not found")
    return compare_runs(candidate, baseline)


@app.post("/api/gates")
def gate(request: GateRequest) -> dict:
    candidate = database.get_run(request.candidate_id)
    if not candidate:
        raise HTTPException(404, "candidate not found")
    baseline = database.get_run(request.baseline_id) if request.baseline_id else database.get_baseline(candidate.project_id)
    config = GateConfig.from_dict(request.config)
    result = apply_gate(candidate, config, baseline)
    database.execute(
        "INSERT INTO gate_results (id,run_id,passed,payload,created_at) VALUES (?,?,?,?,?)",
        (str(uuid4()), candidate.id, int(result["passed"]), json.dumps(result), datetime.now(UTC).isoformat()),
    )
    return result


@app.get("/api/dashboard")
def dashboard() -> dict:
    projects_count = database.rows("SELECT COUNT(*) AS count FROM projects")[0]["count"]
    datasets_count = database.rows("SELECT COUNT(*) AS count FROM datasets")[0]["count"]
    cases_count = database.rows("SELECT COUNT(*) AS count FROM test_cases")[0]["count"]
    run_values = runs()
    return {
        "counts": {"projects": projects_count, "datasets": datasets_count, "test_cases": cases_count, "runs": len(run_values)},
        "latest_runs": run_values[:10],
        "metric_trends": [
            {"run_id": item["id"], "created_at": item["created_at"], **item["aggregate"]}
            for item in reversed(run_values[:20])
        ],
    }

