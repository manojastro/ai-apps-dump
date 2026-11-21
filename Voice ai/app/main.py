"""Event-ingestion + read API. `uvicorn app.main:app`. The staff console is a separate app (app/console/app.py)."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.data.db import init_db, session
from app.data.models import Workflow
from app.obs.tracing import setup_tracing
from app.queue import outbox


@asynccontextmanager
async def lifespan(_app: FastAPI):
    load_dotenv()
    init_db()
    setup_tracing()
    yield


app = FastAPI(title="EIR Agent Fleet API", lifespan=lifespan)


def require_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.environ.get("EIR_API_KEY")  # optional shared secret for the demo API
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="bad or missing X-API-Key")


class EventIn(BaseModel):
    type: str
    payload: dict = {}


@app.get("/health")
def health():
    return {"ok": True, "queue": outbox.counts()}


@app.post("/events", dependencies=[Depends(require_key)])
def post_event(ev: EventIn):
    try:
        return {"event_id": outbox.enqueue(ev.type, ev.payload)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/workflows", dependencies=[Depends(require_key)])
def list_workflows(status: str | None = None, limit: int = 100):
    q = select(Workflow).order_by(Workflow.updated_at.desc()).limit(min(limit, 500))
    if status:
        q = q.where(Workflow.status == status)
    with session() as s:
        return [{"id": w.id, "type": w.type, "status": w.status, "step": w.step,
                 "outcome": w.data.get("outcome")} for w in s.scalars(q)]


@app.get("/api/workflows/{wf_id}", dependencies=[Depends(require_key)])
def get_workflow(wf_id: str):
    with session() as s:
        w = s.get(Workflow, wf_id)
        if w is None:
            raise HTTPException(status_code=404, detail="no such workflow")
        return {"id": w.id, "type": w.type, "status": w.status, "step": w.step, "data": w.data, "history": w.history}
