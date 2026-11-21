"""Staff console: approvals, workflow timeline, audit search, review tasks.

Demo-grade auth only (seeded users, cookie session). Roles: front_desk, nurse, inventory. Each role sees and can
decide only the approvals meant for it (enforced in app/approval/service.decide, not just in the template).
All patient-written text is rendered through Jinja2 autoescaping.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from starlette.middleware.sessions import SessionMiddleware

from app import clock
from app.approval import service as approvals
from app.audit import log as audit
from app.config import get_settings
from app.data.db import init_db, session
from app.data.models import AgentRun, Approval, Observation, StaffUser, Workflow
from app.data.seed import hash_password

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).with_name("templates")))


def create_app(inline_processor=None) -> FastAPI:
    """inline_processor: optional callable run after each decision (tests/demo). In compose a worker does this."""
    app = FastAPI(title="EIR staff console")
    app.add_middleware(SessionMiddleware, secret_key=get_settings().session_secret, same_site="strict")

    def current(request: Request) -> StaffUser | None:
        name = request.session.get("user")
        if not name:
            return None
        with session() as s:
            return s.get(StaffUser, name)

    def need_user(request: Request) -> StaffUser:
        u = current(request)
        if u is None:
            raise HTTPException(status_code=401, detail="login required")
        return u

    def render(request: Request, name: str, **ctx):
        return TEMPLATES.TemplateResponse(request, name, {"user": current(request), "now": clock.now(), **ctx})

    @app.exception_handler(401)
    async def _unauth(request: Request, exc):
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": "login required"}, status_code=401)
        return RedirectResponse("/login", status_code=303)

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/login", response_class=HTMLResponse)
    def login_form(request: Request):
        return render(request, "login.html", error=None)

    @app.post("/login")
    def login(request: Request, username: str = Form(...), password: str = Form(...)):
        with session() as s:
            u = s.get(StaffUser, username)
        if u is None or u.password_hash != hash_password(password):
            return render(request, "login.html", error="Invalid credentials")
        request.session["user"] = u.username
        return RedirectResponse("/approvals", status_code=303)

    @app.get("/logout")
    def logout(request: Request):
        request.session.clear()
        return RedirectResponse("/login", status_code=303)

    @app.get("/")
    def index():
        return RedirectResponse("/approvals", status_code=303)

    # ------------------------------------------------------------- approvals
    def _pending(user: StaffUser) -> list[Approval]:
        return approvals.pending_for_role(user.role)  # oldest first

    @app.get("/approvals", response_class=HTMLResponse)
    def approvals_page(request: Request, msg: str | None = None):
        u = need_user(request)
        approvals.expire_overdue()
        return render(request, "approvals.html", items=_pending(u), msg=msg)

    @app.get("/api/approvals")
    def approvals_api(request: Request):
        u = need_user(request)
        return [{"id": a.id, "kind": a.kind, "required_role": a.required_role, "created_at": a.created_at.isoformat(),
                 "summary": a.summary} for a in _pending(u)]

    @app.post("/approvals/{approval_id}/decide")
    def decide(request: Request, approval_id: str, decision: str = Form(...), reason: str = Form("")):
        u = need_user(request)
        try:
            approvals.decide(approval_id, u.username, decision == "approve", reason)
        except approvals.ApprovalError as exc:
            code = 403 if "may not decide" in str(exc) else 400
            if request.headers.get("accept", "").startswith("application/json"):
                return JSONResponse({"error": str(exc)}, status_code=code)
            raise HTTPException(status_code=code, detail=str(exc)) from exc
        if inline_processor:
            inline_processor()
        return RedirectResponse(f"/approvals?msg=Decision+recorded:+{decision}", status_code=303)

    # ------------------------------------------------------------- workflows
    @app.get("/workflows", response_class=HTMLResponse)
    def workflows(request: Request, status: str | None = None):
        need_user(request)
        q = select(Workflow).order_by(Workflow.updated_at.desc()).limit(200)
        if status:
            q = q.where(Workflow.status == status)
        with session() as s:
            rows = list(s.scalars(q))
        return render(request, "workflows.html", workflows=rows, status=status)

    @app.get("/workflows/{wf_id}", response_class=HTMLResponse)
    def workflow(request: Request, wf_id: str):
        need_user(request)
        with session() as s:
            wf = s.get(Workflow, wf_id)
            if wf is None:
                raise HTTPException(status_code=404, detail="no such workflow")
            aps = list(s.scalars(select(Approval).where(Approval.workflow_id == wf_id).order_by(Approval.created_at)))
            runs = list(s.scalars(select(AgentRun).where(AgentRun.workflow_id == wf_id).order_by(AgentRun.id)))
        calls = list(reversed(audit.search(workflow_id=wf_id, limit=500)))
        return render(request, "workflow.html", wf=wf, approvals=aps, runs=runs, calls=calls)

    # ------------------------------------------------------------- audit & reviews
    @app.get("/audit", response_class=HTMLResponse)
    def audit_page(request: Request, actor: str = "", tool: str = "", patient_id: str = "", date_from: str = "",
                   date_to: str = ""):
        need_user(request)

        def parse(v: str):
            return datetime.fromisoformat(v) if v else None

        try:
            rows = audit.search(actor=actor or None, tool=tool or None, patient_id=patient_id or None,
                                date_from=parse(date_from), date_to=parse(date_to))
        except ValueError:
            raise HTTPException(status_code=400, detail="dates must look like 2026-03-02 or 2026-03-02T09:00") from None
        return render(request, "audit.html", rows=rows, f=dict(actor=actor, tool=tool, patient_id=patient_id,
                                                              date_from=date_from, date_to=date_to))

    @app.get("/reviews", response_class=HTMLResponse)
    def reviews(request: Request):
        u = need_user(request)
        if u.role != "nurse":
            raise HTTPException(status_code=403, detail="review tasks are for nurses")
        with session() as s:
            obs = list(s.scalars(select(Observation).where(Observation.flagged.is_(True))
                                 .order_by(Observation.effective.desc()).limit(100)))
            ap_by_ref = {a.ref_id: a for a in s.scalars(select(Approval).where(Approval.kind == "checkin_review"))}
        return render(request, "reviews.html", obs=obs, aps=ap_by_ref)

    return app


def _default_app() -> FastAPI:
    init_db()
    return create_app()


def __getattr__(name: str):  # lazily build `app` for `uvicorn app.console.app:app`
    if name == "app":
        return _default_app()
    raise AttributeError(name)
