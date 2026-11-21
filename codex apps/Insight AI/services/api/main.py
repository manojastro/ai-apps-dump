import asyncio
import json
import os
import secrets
import time
import uuid
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, text

from packages.agent.contracts import action_hash
from packages.connectors.replay import snapshot
from services.api.auth import current_user, digest, passwords, require, throttle_login
from services.api.db import (
    Action,
    Audit,
    EvidenceRow,
    Incident,
    Job,
    LoginSession,
    Run,
    RunEvent,
    Session,
    Setting,
    User,
    add_event,
    serialize,
)
from services.api.evaluations import router as evaluation_router

app = FastAPI(title="ProductionLens", version="0.1.0")


@app.middleware("http")
async def boundary(request: Request, call_next):
    correlation = str(uuid.uuid4())
    try:
        size = int(request.headers.get("content-length", "0"))
    except ValueError:
        return JSONResponse({"detail": "INVALID_CONTENT_LENGTH"}, status_code=400)
    if size > 65536:
        return JSONResponse({"detail": "PAYLOAD_TOO_LARGE", "correlation_id": correlation}, status_code=413)
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        payload = bytearray()
        async for chunk in request.stream():
            payload.extend(chunk)
            if len(payload) > 65536:
                return JSONResponse(
                    {"detail": "PAYLOAD_TOO_LARGE", "correlation_id": correlation}, status_code=413
                )
        request._body = bytes(payload)
        origin = request.headers.get("origin")
        allowed = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
        if origin and origin not in allowed:
            return JSONResponse({"detail": "ORIGIN_DENIED", "correlation_id": correlation}, status_code=403)
    response = await call_next(request)
    response.headers["x-correlation-id"] = correlation
    response.headers["x-content-type-options"] = "nosniff"
    response.headers["cache-control"] = "no-store"
    return response


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.get("/health/ready")
def ready():
    with Session() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ready"}


class Login(BaseModel):
    username: str = Field(max_length=100)
    password: str = Field(max_length=300)


@app.post("/api/auth/login")
def login(body: Login, request: Request, response: Response):
    throttle_login(request.client.host if request.client else "unknown")
    with Session() as db:
        user = db.scalar(select(User).where(User.username == body.username))
        if not user or not passwords.verify(body.password, user.password_hash):
            raise HTTPException(401, "INVALID_CREDENTIALS")
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        db.add(
            LoginSession(user_id=user.id, token_hash=digest(token), csrf=csrf, expires_at=time.time() + 28800)
        )
        db.add(Audit(actor=user.id, operation="login", target=user.id))
        db.commit()
        response.set_cookie(
            "pl_session",
            token,
            httponly=True,
            samesite="strict",
            max_age=28800,
            secure=os.environ.get("SECURE_COOKIES") == "true",
        )
        return {"id": user.id, "username": user.username, "role": user.role, "csrf": csrf}


@app.get("/api/auth/me")
def me(request: Request, user=Depends(current_user)):
    return {"id": user.id, "username": user.username, "role": user.role, "csrf": request.state.csrf}


@app.post("/api/auth/logout")
def logout(request: Request, response: Response, user=Depends(current_user)):
    with Session() as db:
        row = db.scalar(
            select(LoginSession).where(
                LoginSession.token_hash == digest(request.cookies.get("pl_session", ""))
            )
        )
        if row:
            db.delete(row)
        db.commit()
    response.delete_cookie("pl_session")
    return {"status": "signed_out"}


class IncidentInput(BaseModel):
    title: str = Field(min_length=3, max_length=250)
    description: str = Field(default="", max_length=4000)
    service: Literal["checkout", "payment", "inventory"] = "checkout"
    severity: Literal["P1", "P2", "P3"] = "P2"
    mode: Literal["replay", "live"] = "replay"
    fixture: Literal[
        "payment_delay",
        "config_regression",
        "pool_exhaustion",
        "cpu_saturation",
        "healthy",
        "missing_evidence",
    ] = "payment_delay"


@app.get("/api/incidents")
def incidents(user=Depends(current_user)):
    with Session() as db:
        rows = db.scalars(select(Incident).order_by(Incident.created_at.desc()).limit(200)).all()
        return [{k: v for k, v in serialize(r).items() if k != "snapshot"} for r in rows]


@app.post("/api/incidents")
def create_incident(body: IncidentInput, user=Depends(require("investigator"))):
    if body.mode == "live" and not os.environ.get("MODEL_API_KEY"):
        raise HTTPException(503, "PROVIDER_NOT_CONFIGURED: set MODEL_API_KEY and MODEL_ID on the server")
    with Session() as db:
        row = Incident(
            title=body.title.strip(),
            description=body.description,
            service=body.service,
            severity=body.severity,
            mode=body.mode,
            created_by=user.id,
            snapshot=snapshot(body.fixture) if body.mode == "replay" else {},
        )
        db.add(row)
        db.flush()
        db.add(Audit(actor=user.id, operation="incident.create", target=row.id, data={"mode": row.mode}))
        db.commit()
        return {k: v for k, v in serialize(row).items() if k != "snapshot"}


@app.get("/api/investigations")
def runs(user=Depends(current_user)):
    with Session() as db:
        return [serialize(r) for r in db.scalars(select(Run).order_by(Run.created_at.desc()).limit(200))]


class RunInput(BaseModel):
    incident_id: str
    tool_limit: int = Field(default=12, ge=0, le=30)


@app.post("/api/investigations")
def create_run(body: RunInput, user=Depends(require("investigator"))):
    from packages.agent.version import version_metadata

    with Session() as db:
        incident = db.get(Incident, body.incident_id)
        if not incident:
            raise HTTPException(404, "INCIDENT_NOT_FOUND")
        row = Run(
            incident_id=incident.id,
            mode=incident.mode,
            version=version_metadata("script-v1" if incident.mode == "replay" else "iterative"),
            state={"tool_limit": body.tool_limit, "evidence": [], "tools": []},
        )
        db.add(row)
        db.flush()
        db.add(Job(kind="investigate", target_id=row.id))
        row.version = {**row.version, "runtime": {**row.version["runtime"], "tool_limit": body.tool_limit}}
        add_event(db, row.id, "queued", "Investigation persisted and queued for the worker")
        incident.status = "investigating"
        db.commit()
        return serialize(row)


@app.get("/api/investigations/{run_id}")
def get_run(run_id: str, user=Depends(current_user)):
    with Session() as db:
        row = db.get(Run, run_id)
        if not row:
            raise HTTPException(404, "RUN_NOT_FOUND")
        action = db.scalar(select(Action).where(Action.run_id == run_id))
        return {
            **serialize(row),
            "incident": {
                k: v for k, v in serialize(db.get(Incident, row.incident_id)).items() if k != "snapshot"
            },
            "events": [
                serialize(e)
                for e in db.scalars(
                    select(RunEvent).where(RunEvent.run_id == run_id).order_by(RunEvent.created_at)
                )
            ],
            "evidence": [e.data for e in db.scalars(select(EvidenceRow).where(EvidenceRow.run_id == run_id))],
            "action": serialize(action) if action else None,
        }


@app.get("/api/investigations/{run_id}/evidence/{evidence_id}")
def get_evidence(run_id: str, evidence_id: str, user=Depends(current_user)):
    with Session() as db:
        evidence = db.get(EvidenceRow, evidence_id)
        if not evidence or evidence.run_id != run_id:
            raise HTTPException(404, "EVIDENCE_NOT_FOUND")
        return evidence.data


@app.get("/api/investigations/{run_id}/events")
async def stream_events(run_id: str, request: Request, user=Depends(current_user)):
    with Session() as db:
        if not db.get(Run, run_id):
            raise HTTPException(404, "RUN_NOT_FOUND")

    async def generate():
        seen = set()
        # Each reconnect sends persisted events; clients deduplicate by immutable event ID.
        for _ in range(240):
            if await request.is_disconnected():
                break
            with Session() as db:
                events = db.scalars(
                    select(RunEvent).where(RunEvent.run_id == run_id).order_by(RunEvent.created_at)
                ).all()
                for item in events:
                    if item.id not in seen:
                        seen.add(item.id)
                        yield f"id: {item.id}\ndata: {json.dumps(serialize(item))}\n\n"
            yield ": heartbeat\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(generate(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"})


@app.post("/api/investigations/{run_id}/cancel")
def cancel_run(run_id: str, user=Depends(require("investigator"))):
    with Session() as db:
        run = db.get(Run, run_id)
        if not run:
            raise HTTPException(404, "RUN_NOT_FOUND")
        if run.status in {"completed", "inconclusive", "failed", "cancelled"}:
            raise HTTPException(409, "RUN_ALREADY_TERMINAL")
        action = db.scalar(select(Action).where(Action.run_id == run_id))
        if action and action.status in {"approved", "executed"}:
            raise HTTPException(409, "ACTION_ALREADY_AUTHORIZED")
        if action:
            action.status = "rejected"
        run.status = "cancelled"
        add_event(db, run.id, "cancelled", "Investigator cancelled the run")
        db.commit()
    return {"status": "cancelled"}


class Decision(BaseModel):
    action_hash: str = Field(min_length=64, max_length=64)


@app.post("/api/actions/{action_id}/{decision}")
def decide(
    action_id: str, decision: Literal["approve", "reject"], body: Decision, user=Depends(require("reviewer"))
):
    from sqlalchemy import update

    with Session() as db:
        action = db.get(Action, action_id)
        if not action:
            raise HTTPException(404, "ACTION_NOT_FOUND")
        if action.expires_at <= time.time():
            raise HTTPException(409, "APPROVAL_EXPIRED")
        if body.action_hash != action.digest or action_hash(action.proposal) != action.digest:
            raise HTTPException(409, "ACTION_HASH_MISMATCH")
        target_status = "approved" if decision == "approve" else "rejected"
        updated = db.execute(
            update(Action)
            .where(Action.id == action_id, Action.status == "pending")
            .values(status=target_status, reviewer=user.id, decision_at=time.time())
        )
        if not updated.rowcount:
            raise HTTPException(409, "ACTION_ALREADY_REVIEWED")
        if decision == "approve":
            db.add(Job(kind="execute", target_id=action_id))
        else:
            db.get(Run, action.run_id).status = "completed"
        add_event(db, action.run_id, target_status, f"Exact action {target_status} by {user.username}")
        db.add(
            Audit(
                actor=user.id, operation=f"action.{decision}", target=action.id, data={"hash": action.digest}
            )
        )
        db.commit()
    return {"status": target_status}


@app.get("/api/investigations/{run_id}/export")
def export_run(run_id: str, user=Depends(current_user)):
    return JSONResponse(
        get_run(run_id, user),
        headers={"Content-Disposition": f'attachment; filename="incident-{run_id}.json"'},
    )


@app.get("/api/integrations")
def integrations(user=Depends(current_user)):
    configured = bool(os.environ.get("MODEL_API_KEY") and os.environ.get("MODEL_ID"))
    with Session() as db:
        heartbeat = db.get(Setting, "worker")
        worker_ok = bool(heartbeat and time.time() - heartbeat.data.get("at", 0) < 20)
    return {
        "mode": "replay",
        "provider_configured": configured,
        "model": os.environ.get("MODEL_ID", "Not configured"),
        "worker": "connected" if worker_ok else "disconnected",
        "sources": [
            {
                "name": name,
                "status": "replay",
                "authentication": "Not required for fixtures",
                "freshness": "Versioned synthetic snapshot",
                "timeout_seconds": 8,
                "retries": 2,
                "max_bytes": 32768,
                "live_verified": False,
            }
            for name in ["Prometheus", "Jaeger", "Structured logs", "Deployment history"]
        ],
    }


@app.post("/api/integrations/provider/test")
def test_provider(user=Depends(require("administrator"))):
    from packages.connectors.provider import Provider

    try:
        return Provider().test()
    except Exception as exc:
        raise HTTPException(503, str(exc)[:200]) from None


@app.get("/api/demo")
def demo_state(user=Depends(current_user)):
    with Session() as db:
        row = db.get(Setting, "demo")
        return (
            row.data
            if row
            else {"mode": "replay", "fault": None, "traffic": False, "samples": 0, "revision": 0}
        )


class DemoInput(BaseModel):
    operation: Literal["traffic", "fault", "reset"]
    fault: Literal["payment_delay", "config_regression", "pool_exhaustion", "cpu_saturation"] = (
        "payment_delay"
    )


@app.post("/api/demo")
def demo_control(body: DemoInput, user=Depends(require("administrator"))):
    with Session() as db:
        setting = db.get(Setting, "demo")
        state = (
            dict(setting.data)
            if setting
            else {"mode": "replay", "revision": 0, "traffic": False, "samples": 0, "fault": None}
        )
        state["revision"] += 1
        if body.operation == "traffic":
            state.update(traffic=True, samples=240, observed_at=time.time())
        elif body.operation == "reset":
            state.update(fault=None, expires_at=None)
        else:
            state.update(fault=body.fault, expires_at=time.time() + 120)
        if setting:
            setting.data = state
        else:
            db.add(Setting(id="demo", data=state))
        db.add(Audit(actor=user.id, operation=f"demo.{body.operation}", target="replay-lab", data=state))
        db.commit()
        return state


@app.get("/api/audit")
def audit(user=Depends(require("administrator"))):
    with Session() as db:
        return [serialize(e) for e in db.scalars(select(Audit).order_by(Audit.created_at.desc()).limit(100))]


app.include_router(evaluation_router)
