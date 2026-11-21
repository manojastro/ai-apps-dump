"""Routes: health, triage, batch, streaming reply."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from ticketsort.api.deps import get_app_settings
from ticketsort.config import Settings
from ticketsort.domain.escalation import should_escalate_to_human
from ticketsort.domain.models import TicketIn, TriageResult
from ticketsort.domain.priority import compute_priority
from ticketsort.domain.routing import route
from ticketsort.domain.sla import sla_for
from ticketsort.llm.client import get_client

router = APIRouter()


@router.get("/health")
def health(settings: Settings = Depends(get_app_settings)) -> dict[str, str]:
    """Liveness + config check. Never returns secrets."""
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "prompt_version": settings.prompt_version,
    }


async def triage_one(ticket: TicketIn, settings: Settings) -> TriageResult:
    """Validate -> LLM extract (repair x2) -> code decides priority/routing."""
    client = get_client(settings)
    last_err: Exception | None = None
    extraction = None
    llm_meta = None
    for _attempt in range(3):  # first try + 2 repairs
        try:
            extraction, llm_meta = await client.extract(ticket)
            break
        except ValidationError as e:
            last_err = e
            continue
    if extraction is None or llm_meta is None:
        raise HTTPException(status_code=502, detail=f"LLM extraction failed: {last_err}")
    priority = compute_priority(extraction.impact, extraction.urgency)
    group = route(extraction.category, extraction.affected_service)
    needs = should_escalate_to_human(extraction, settings)
    return TriageResult(
        **extraction.model_dump(),
        priority=priority,
        assignment_group=group,
        needs_human=needs,
        llm_meta=llm_meta,
        prompt_version=settings.prompt_version,
    )


@router.post("/v1/triage", response_model=TriageResult)
async def triage(ticket: TicketIn, settings: Settings = Depends(get_app_settings)) -> TriageResult:
    return await triage_one(ticket, settings)


@router.post("/v1/triage/batch", response_model=list[TriageResult])
async def triage_batch(
    tickets: list[TicketIn], settings: Settings = Depends(get_app_settings)
) -> list[TriageResult]:
    if len(tickets) > 20:
        raise HTTPException(status_code=400, detail="batch max is 20 tickets")
    sem = asyncio.Semaphore(5)

    async def _one(t: TicketIn) -> TriageResult:
        async with sem:
            return await triage_one(t, settings)

    return list(await asyncio.gather(*(_one(t) for t in tickets)))


def build_reply_text(result: TriageResult) -> str:
    """Template reply: acknowledge, SLA promise, one clarifying Q if vague."""
    sla = sla_for(result.priority)
    hours = int(sla.total_seconds() // 3600)
    base = (
        f"Hi, thanks for reporting '{result.summary}'. "
        f"We logged it as {result.priority} and assigned {result.assignment_group}. "
        f"Target first response within {hours} hour(s). "
    )
    if result.confidence < 0.6 or result.affected_service.value == "unknown":
        base += "Could you share one photo or error code and when it started? "
    base += "We will update you here. — Acme IT (synthetic demo)"
    return base


async def _sse_chunks(text: str) -> AsyncIterator[str]:
    for word in text.split():
        yield f"data: {word}\n\n"
    yield "data: [DONE]\n\n"


@router.post("/v1/reply/stream")
async def reply_stream(
    ticket: TicketIn, settings: Settings = Depends(get_app_settings)
) -> StreamingResponse:
    result = await triage_one(ticket, settings)
    text = build_reply_text(result)
    return StreamingResponse(_sse_chunks(text), media_type="text/event-stream")
