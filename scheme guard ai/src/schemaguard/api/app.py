"""FastAPI app.  Run: `uv run schemaguard api` (or uvicorn schemaguard.api.app:app)."""

from __future__ import annotations

import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field, model_validator

from schemaguard import __version__
from schemaguard.config import get_settings
from schemaguard.schemas.avro import load_pipeline_schemas
from schemaguard.schemas.mutate import apply_mutations
from schemaguard.schemas.registry import make_registry, topic_for_subject
from schemaguard.service import SchemaGuardService


class ChangeRequest(BaseModel):
    """Submit either (topic + new_schema), (topic + mutations), or (subject + version from the registry)."""

    topic: str | None = None
    new_schema: dict[str, Any] | None = None
    old_schema: dict[str, Any] | None = None
    mutations: list[dict[str, Any]] | None = Field(
        default=None, description="declarative ops applied to the current schema"
    )
    subject: str | None = None
    version: int | None = None

    @model_validator(mode="after")
    def _one_form(self) -> ChangeRequest:
        if self.subject and self.version:
            return self
        if self.topic and (self.new_schema or self.mutations):
            return self
        raise ValueError("provide topic+new_schema, topic+mutations, or subject+version")


class Decision(BaseModel):
    reviewer: str = Field(min_length=1, max_length=100)
    comment: str = Field(default="", max_length=2000)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.svc = SchemaGuardService(background=True)
    yield
    app.state.svc.close()


app = FastAPI(title="SchemaGuard", version=__version__, lifespan=lifespan)


def svc(request: Request) -> SchemaGuardService:
    return request.app.state.svc  # type: ignore[no-any-return]


def require_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = get_settings().api_key
    if expected and not (x_api_key and secrets.compare_digest(x_api_key, expected)):
        raise HTTPException(401, "missing or invalid X-API-Key")


@app.get("/health")
def health(s: SchemaGuardService = Depends(svc)) -> dict[str, Any]:
    return {
        "status": "ok",
        "version": __version__,
        "lineage_version": s.lineage_version,
        "llm_provider": s.settings.llm_provider,
        "database": s.db.kind,
        "runs": len(s.list_runs(limit=1000)),
    }


@app.post("/changes", status_code=202, dependencies=[Depends(require_key)])
def submit_change(req: ChangeRequest, s: SchemaGuardService = Depends(svc)) -> dict[str, Any]:
    old_version = new_version = None
    if req.subject and req.version:
        reg = make_registry(s.settings.registry_url, s.settings.resolved_registry_dir)
        try:
            new = reg.get(req.subject, req.version)
            old = reg.get(req.subject, req.version - 1).schema if req.version > 1 else None
        except KeyError as exc:
            raise HTTPException(404, f"registry: {exc}") from exc
        topic, new_schema, old_schema = topic_for_subject(req.subject), new.schema, old
        old_version, new_version = (req.version - 1 if req.version > 1 else None), req.version
    else:
        assert req.topic
        topic, old_schema = req.topic, req.old_schema
        if req.mutations:
            current = load_pipeline_schemas(s.pipeline_dir / "avro")
            if topic not in current:
                raise HTTPException(404, f"unknown topic {topic}")
            try:
                new_schema = apply_mutations(current[topic].raw, req.mutations)
            except (KeyError, ValueError) as exc:
                raise HTTPException(422, f"bad mutation: {exc}") from exc
        else:
            new_schema = req.new_schema or {}
    try:
        run_id, created = s.submit_change(
            topic,
            new_schema,
            old_schema,
            source="api",
            subject=req.subject or "",
            old_version=old_version,
            new_version=new_version,
        )
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"run_id": run_id, "created": created, "status_url": f"/runs/{run_id}"}


def _view(run: dict[str, Any]) -> dict[str, Any]:
    st = run.pop("state")
    keep = [
        "status", "change_event", "schema_diff", "change_class", "explanation", "injection_findings", "lineage_version",
        "impacted_nodes", "assessments", "aggregate", "fix_plan", "patch", "test_results", "baseline_results", "attempts",
        "retry_count", "approval_status", "approval", "pr_url_or_patch_path", "report", "cost_tracking", "errors",
        "route_reason", "escalation_reason",
    ]  # fmt: skip
    run["state"] = {k: st.get(k) for k in keep if k in st}
    return run


@app.get("/runs", dependencies=[Depends(require_key)])
def list_runs(limit: int = Query(100, le=1000), s: SchemaGuardService = Depends(svc)) -> list[dict[str, Any]]:
    return s.list_runs(limit)


@app.get("/runs/{run_id}", dependencies=[Depends(require_key)])
def get_run(run_id: str, s: SchemaGuardService = Depends(svc)) -> dict[str, Any]:
    run = s.get_run(run_id)
    if run is None:
        raise HTTPException(404, "run not found")
    return _view(run)


@app.get("/runs/{run_id}/report", response_class=PlainTextResponse, dependencies=[Depends(require_key)])
def get_report(run_id: str, s: SchemaGuardService = Depends(svc)) -> str:
    run = s.get_run(run_id)
    if run is None or not run["state"].get("report"):
        raise HTTPException(404, "report not available yet")
    return str(run["state"]["report"])


@app.get("/runs/{run_id}/graph.dot", response_class=PlainTextResponse, dependencies=[Depends(require_key)])
def get_graph_dot(run_id: str, s: SchemaGuardService = Depends(svc)) -> str:
    run = s.get_run(run_id)
    if run is None:
        raise HTTPException(404, "run not found")
    st = run["state"]
    nodes = [n["id"] for n in st.get("impacted_nodes", []) if not n["context"]]
    topic = st.get("schema_diff", {}).get("topic")
    for c in st.get("schema_diff", {}).get("changes", []):
        fid = f"field:{topic}.{c['field']}"
        if s.lineage.has(fid):
            nodes.append(fid)
    verdicts = {a["asset"]: a["verdict"] for a in st.get("assessments", [])}
    verdicts.update({f"dashboard:{k}": v for k, v in st.get("aggregate", {}).get("dashboards", {}).items()})
    return s.lineage.to_dot(nodes, verdicts)


def _decide(run_id: str, d: Decision, s: SchemaGuardService, approve: bool) -> dict[str, Any]:
    try:
        (s.approve if approve else s.reject)(run_id, d.reviewer, d.comment)
    except KeyError as exc:
        raise HTTPException(404, "run not found") from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"run_id": run_id, "accepted": True}


@app.post("/runs/{run_id}/approve", status_code=202, dependencies=[Depends(require_key)])
def approve(run_id: str, d: Decision, s: SchemaGuardService = Depends(svc)) -> dict[str, Any]:
    return _decide(run_id, d, s, True)


@app.post("/runs/{run_id}/reject", status_code=202, dependencies=[Depends(require_key)])
def reject(run_id: str, d: Decision, s: SchemaGuardService = Depends(svc)) -> dict[str, Any]:
    return _decide(run_id, d, s, False)


def _lineage_node(s: SchemaGuardService, node: str) -> str:
    if not s.lineage.has(node):
        raise HTTPException(404, f"node {node!r} not in lineage graph v{s.lineage_version}")
    return node


@app.get("/lineage/downstream", dependencies=[Depends(require_key)])
def downstream(
    node: str, max_depth: int = Query(12, ge=1, le=50), s: SchemaGuardService = Depends(svc)
) -> dict[str, Any]:
    n = _lineage_node(s, node)
    return {
        "node": n,
        "lineage_version": s.lineage_version,
        "nodes": [x.to_dict() for x in s.lineage.downstream(n, max_depth)],
        "impact_paths": s.lineage.impact_paths(n),
        "blast_radius": s.lineage.blast_radius_summary(n),
    }


@app.get("/lineage/upstream", dependencies=[Depends(require_key)])
def upstream(
    node: str, max_depth: int = Query(12, ge=1, le=50), s: SchemaGuardService = Depends(svc)
) -> dict[str, Any]:
    n = _lineage_node(s, node)
    return {
        "node": n,
        "lineage_version": s.lineage_version,
        "nodes": [x.to_dict() for x in s.lineage.upstream(n, max_depth)],
    }
