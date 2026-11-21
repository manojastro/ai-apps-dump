"""Copilot chat, the daily brief and citation lookups."""
from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, Db, UserScope, not_found
from app.api.schemas import BriefOut, ChatRequest, ChatResponse, SourceRecord
from app.copilot.agent import Copilot, LLMUnavailable
from app.core.config import get_settings
from app.core.ratelimit import RateLimiter
from app.services import briefing, sources

router = APIRouter(tags=["copilot"])


@lru_cache
def limiter() -> RateLimiter:
    return RateLimiter(get_settings().copilot_rate_limit_per_minute)


@router.post("/copilot/chat", response_model=ChatResponse)
def chat(body: ChatRequest, db: Db, user: CurrentUser, scope: UserScope) -> ChatResponse:
    if not limiter().allow(str(user.id)):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many copilot requests")
    try:
        copilot = Copilot(db, scope, user.team.name if user.team else None)
    except LLMUnavailable as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Copilot is not configured: set ANTHROPIC_API_KEY on the server.",
        ) from error
    result = copilot.ask(body.question, [t.model_dump() for t in body.history])
    return ChatResponse(
        answer=result.answer, tools_called=result.tools_called, citations=result.citations,
        invalid_citations=result.invalid_citations,
        ungrounded_numbers=result.ungrounded_numbers, audit_id=result.audit_id,
        latency_ms=result.latency_ms,
    )


@router.get("/copilot/status")
def copilot_status(_: CurrentUser) -> dict[str, bool | str]:
    settings = get_settings()
    return {"configured": bool(settings.anthropic_api_key), "model": settings.llm_model}


@router.get("/sources/{table}/{source_id}", response_model=SourceRecord)
def source(table: str, source_id: int, db: Db, scope: UserScope) -> dict:
    record = sources.get_source(db, scope, table, source_id)
    if record is None:
        raise not_found()
    return record


@router.get("/brief", response_model=BriefOut | None)
def brief(db: Db, user: CurrentUser) -> BriefOut | None:
    latest = briefing.latest_for(db, user.id)
    if latest is None:
        return None
    return BriefOut(brief_date=latest.brief_date, content=latest.content_json)
