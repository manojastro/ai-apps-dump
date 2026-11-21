"""FastAPI app: JSON API + a small server-rendered review UI.

    uvicorn app.api.main:app --reload        # then open http://localhost:8000
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.applier.applier import Applier
from app.applier.sandbox import reset_sandbox, sandbox_ready
from app.approval.store import InvalidTransition, NotFound, Store
from app.config import Settings, get_settings
from app.core import pipeline
from app.core.models import ConflictType, ProposalStatus
from app.llm.client import LLMClient
from app.tracing import setup_tracing

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


class ApproveBody(BaseModel):
    reviewer: str = Field(min_length=1)
    note: str | None = None


class RejectBody(BaseModel):
    reviewer: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class ApplyBody(BaseModel):
    actor: str = Field(min_length=1)


class RunBody(BaseModel):
    prompt_version: str | None = None
    limit: int | None = None


@dataclass
class Services:
    settings: Settings
    store: Store
    llm: LLMClient
    applier: Applier


def create_app(settings: Settings | None = None, llm: LLMClient | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_tracing(settings.otel_endpoint)
    store = Store(settings.state_db, regressions_dir=settings.regressions_dir)
    svc = Services(settings, store, llm or LLMClient(settings),
                   Applier(store, settings.sandbox_dir, settings.generated_dir))
    app = FastAPI(title="TruthKeeper", version="0.1.0",
                  description="Rules detect, the LLM explains, humans approve. Sandbox data only.")
    app.state.svc = svc

    def _err(e: Exception):
        if isinstance(e, NotFound):
            raise HTTPException(404, str(e)) from e
        if isinstance(e, InvalidTransition):
            raise HTTPException(409, str(e)) from e
        raise e

    # ---------------------------------------------------------------- JSON API
    @app.get("/health")
    def health():
        return {"ok": True, "llm_mode": svc.llm.mode, "model": svc.llm.model_name,
                "sandbox_ready": sandbox_ready(settings.sandbox_dir)}

    @app.get("/stats")
    def stats():
        return svc.store.stats()

    @app.post("/sandbox/reset")
    def sandbox_reset():
        files = reset_sandbox(settings.generated_dir, settings.sandbox_dir)
        return {"reset": [f.name for f in files]}

    @app.post("/pipeline/run")
    def pipeline_run(body: RunBody | None = None):
        body = body or RunBody()
        if not sandbox_ready(settings.sandbox_dir):
            reset_sandbox(settings.generated_dir, settings.sandbox_dir)
        s = pipeline.run(svc.store, svc.llm, settings.sandbox_dir, body.prompt_version or settings.prompt_version,
                         limit=body.limit)
        return s.to_dict()

    @app.get("/conflicts")
    def list_conflicts(type: ConflictType | None = None, status: str | None = Query(None),
                       min_impact: float | None = None, proposal_status: ProposalStatus | None = None):
        return svc.store.list_queue(type=type.value if type else None, status=status, min_impact=min_impact,
                                    proposal_status=proposal_status.value if proposal_status else None)

    @app.get("/proposals/{proposal_id}")
    def get_proposal(proposal_id: int):
        try:
            return svc.store.get_proposal(proposal_id)
        except Exception as e:
            _err(e)

    @app.post("/proposals/{proposal_id}/approve")
    def approve(proposal_id: int, body: ApproveBody):
        try:
            return svc.store.approve(proposal_id, body.reviewer, body.note)
        except Exception as e:
            _err(e)

    @app.post("/proposals/{proposal_id}/reject")
    def reject(proposal_id: int, body: RejectBody):
        try:
            return svc.store.reject(proposal_id, body.reviewer, body.reason)
        except Exception as e:
            _err(e)

    @app.post("/proposals/{proposal_id}/apply")
    def apply(proposal_id: int, body: ApplyBody):
        try:
            return svc.applier.apply(proposal_id, body.actor).to_dict()
        except Exception as e:
            _err(e)

    @app.get("/audit")
    def audit_log(entity_id: str | None = None, limit: int = 200):
        return svc.store.audit_entries(entity_id=entity_id, limit=limit)

    # ---------------------------------------------------------------- HTML UI
    @app.get("/", response_class=HTMLResponse)
    def ui_queue(request: Request, type: str | None = None, show: str = "open"):
        rows = svc.store.list_queue(type=type or None, status="OPEN" if show == "open" else None)
        return TEMPLATES.TemplateResponse(request, "queue.html", {
            "rows": rows, "stats": svc.store.stats(), "types": [t.value for t in ConflictType],
            "selected_type": type or "", "show": show, "llm_mode": svc.llm.mode, "model": svc.llm.model_name,
            "sandbox_ready": sandbox_ready(settings.sandbox_dir)})

    @app.get("/ui/proposals/{proposal_id}", response_class=HTMLResponse)
    def ui_proposal(request: Request, proposal_id: int, msg: str | None = None):
        try:
            p = svc.store.get_proposal(proposal_id)
        except Exception as e:
            _err(e)
        return TEMPLATES.TemplateResponse(request, "proposal.html", {"p": p, "msg": msg})

    def _back(pid: int, msg: str) -> RedirectResponse:
        from urllib.parse import quote

        return RedirectResponse(f"/ui/proposals/{pid}?msg={quote(msg)}", status_code=303)

    @app.post("/ui/proposals/{proposal_id}/approve")
    def ui_approve(proposal_id: int, reviewer: str = Form(...), note: str = Form("")):
        try:
            svc.store.approve(proposal_id, reviewer, note or None)
            return _back(proposal_id, "Approved. Click Apply to write the fix to the sandbox.")
        except (NotFound, InvalidTransition) as e:
            return _back(proposal_id, f"Not approved: {e}")

    @app.post("/ui/proposals/{proposal_id}/reject")
    def ui_reject(proposal_id: int, reviewer: str = Form(...), reason: str = Form(...)):
        try:
            svc.store.reject(proposal_id, reviewer, reason)
            return _back(proposal_id, "Rejected. Saved as a regression case.")
        except (NotFound, InvalidTransition) as e:
            return _back(proposal_id, f"Not rejected: {e}")

    @app.post("/ui/proposals/{proposal_id}/apply")
    def ui_apply(proposal_id: int, actor: str = Form(...)):
        try:
            r = svc.applier.apply(proposal_id, actor)
            return _back(proposal_id, f"{r.outcome}: {r.message}")
        except NotFound as e:
            return _back(proposal_id, f"Error: {e}")

    @app.post("/ui/run")
    def ui_run():
        pipeline_run(RunBody())
        return RedirectResponse("/", status_code=303)

    @app.post("/ui/reset")
    def ui_reset():
        sandbox_reset()
        return RedirectResponse("/", status_code=303)

    return app


_APP: FastAPI | None = None


def __getattr__(name):  # pragma: no cover - lets `uvicorn app.api.main:app` work without import side effects
    global _APP
    if name == "app":
        if _APP is None:
            _APP = create_app()
        return _APP
    raise AttributeError(name)
