import asyncio
import json
from uuid import uuid4

from fastapi import APIRouter, Header, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse

from app.db.repository import RELATED
from app.models.domain import Approval, ApprovalInput, Incident, IncidentInput, Status

router = APIRouter(prefix="/api/v1")


@router.post("/incidents", status_code=201)
async def create_incident(body: IncidentInput, request: Request):
    incident = Incident(id=str(uuid4()), **body.model_dump())
    return await asyncio.to_thread(request.app.state.repository.create, incident)


@router.get("/incidents")
async def list_incidents(
    request: Request, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)
):
    return await asyncio.to_thread(request.app.state.repository.list_incidents, limit, offset)


@router.get("/incidents/{incident_id}")
async def get_incident(incident_id: str, request: Request):
    return await asyncio.to_thread(request.app.state.repository.get, incident_id)


@router.post("/incidents/{incident_id}/run")
async def run_incident(incident_id: str, request: Request, wait: bool = False):
    return await request.app.state.service.start(incident_id, wait=wait)


@router.get("/incidents/{incident_id}/state")
async def get_state(incident_id: str, request: Request):
    await get_incident(incident_id, request)
    snapshot = await request.app.state.service.snapshot(incident_id)
    return jsonable_encoder(
        {
            "values": snapshot.values,
            "next": snapshot.next,
            "interrupts": [i.value for task in snapshot.tasks for i in task.interrupts],
        }
    )


@router.post("/incidents/{incident_id}/approve")
async def approve(incident_id: str, body: ApprovalInput, request: Request, wait: bool = False):
    return await request.app.state.service.start(
        incident_id, decision=Approval(**body.model_dump(), approved=True), wait=wait
    )


@router.post("/incidents/{incident_id}/reject")
async def reject(incident_id: str, body: ApprovalInput, request: Request, wait: bool = False):
    return await request.app.state.service.start(
        incident_id, decision=Approval(**body.model_dump(), approved=False), wait=wait
    )


@router.get("/incidents/{incident_id}/events")
async def events(
    incident_id: str,
    request: Request,
    after: int = Query(0, ge=0),
    last_event_id: str | None = Header(None),
):
    await get_incident(incident_id, request)
    cursor = max(after, int(last_event_id)) if last_event_id and last_event_id.isdigit() else after

    async def stream():
        position = cursor
        while not await request.is_disconnected():
            batch = await asyncio.to_thread(
                request.app.state.repository.events, incident_id, position
            )
            for item in batch:
                position = item["id"]
                yield f"id: {position}\nevent: workflow\ndata: {json.dumps(item)}\n\n"
            row = await asyncio.to_thread(request.app.state.repository.get, incident_id)
            if not batch and row["status"] in (
                Status.COMPLETED,
                Status.FAILED,
                Status.REJECTED,
                Status.WAITING,
                Status.CREATED,
            ):
                yield f"event: settled\ndata: {json.dumps({'status': row['status']})}\n\n"
                break
            if not batch:
                yield ": heartbeat\n\n"
                await asyncio.sleep(0.25)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/incidents/{incident_id}/{collection}")
async def related(incident_id: str, collection: str, request: Request):
    await get_incident(incident_id, request)
    if collection not in RELATED:
        raise KeyError(collection)
    return await asyncio.to_thread(request.app.state.repository.related, incident_id, collection)


@router.get("/metrics/summary")
async def summary(request: Request):
    return await asyncio.to_thread(request.app.state.repository.summary)
