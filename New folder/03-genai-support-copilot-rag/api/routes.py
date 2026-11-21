# File: api/routes.py
"""HTTP routes: chat, ingestion trigger/status, and health."""
from __future__ import annotations

import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from starlette.concurrency import run_in_threadpool

from api.schemas import (
    APP_VERSION,
    Citation,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    JobStatusResponse,
)
from core.logging_utils import get_logger
from ingestion.pipeline import IngestionConfig, IngestionPipeline
from rag.chain import SupportCopilotChain

load_dotenv()
logger = get_logger(__name__)
router = APIRouter()

_MAX_JOB_RECORDS = 200


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class _JobRecord:
    job_id: str
    status: str = "queued"
    submitted_at: str = field(default_factory=_utc_now_iso)
    finished_at: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


_JOBS: "OrderedDict[str, _JobRecord]" = OrderedDict()
_JOBS_LOCK = threading.Lock()


def _register_job(job_id: str) -> _JobRecord:
    with _JOBS_LOCK:
        record = _JobRecord(job_id=job_id)
        _JOBS[job_id] = record
        while len(_JOBS) > _MAX_JOB_RECORDS:
            _JOBS.popitem(last=False)
        return record


def _finish_job(
    job_id: str,
    job_status: str,
    stats: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> None:
    with _JOBS_LOCK:
        record = _JOBS.get(job_id)
        if record is not None:
            record.status = job_status
            record.stats = stats
            record.error = error
            record.finished_at = _utc_now_iso()


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    """Answer a support question grounded on the ingested knowledge base."""
    copilot: Optional[SupportCopilotChain] = getattr(request.app.state, "copilot", None)
    if copilot is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is initialising; try again shortly.",
        )
    started = time.perf_counter()
    result = await run_in_threadpool(copilot.answer, payload.message, payload.session_id)
    logger.info(
        "route_chat session=%s duration_ms=%d",
        payload.session_id,
        int((time.perf_counter() - started) * 1000),
    )
    return ChatResponse(
        answer=result.answer,
        sources=[Citation(source=source) for source in result.sources],
        session_id=result.session_id,
    )


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_ingestion(payload: IngestRequest, background_tasks: BackgroundTasks) -> IngestResponse:
    """Queue a knowledge-base ingestion run executed after the response returns."""
    job_id = uuid.uuid4().hex
    _register_job(job_id)
    background_tasks.add_task(_run_ingestion_job, job_id, payload)
    logger.info("ingest_queued job_id=%s path=%s dry_run=%s", job_id, payload.path, payload.dry_run)
    return IngestResponse(job_id=job_id)


def _run_ingestion_job(job_id: str, payload: IngestRequest) -> None:
    try:
        from ingestion.pipeline import build_embeddings

        config = IngestionConfig(
            data_dir=Path(payload.path) if payload.path else Path("data"),
            namespace=payload.namespace,
            dry_run=payload.dry_run,
        )
        report = IngestionPipeline(config, embeddings=build_embeddings()).run()
        _finish_job(job_id, "completed", stats=asdict(report))
    except Exception as exc:  # noqa: BLE001 - job failures are recorded, never raised
        logger.exception("ingest_failed job_id=%s error=%s", job_id, exc)
        _finish_job(job_id, "failed", error=str(exc))


@router.get("/ingest/status/{job_id}", response_model=JobStatusResponse)
async def ingestion_status(job_id: str) -> JobStatusResponse:
    """Poll the state of an ingestion job."""
    with _JOBS_LOCK:
        record = _JOBS.get(job_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown job id: {job_id}")
    return JobStatusResponse(**asdict(record))


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    """Liveness probe; reports degraded mode instead of failing hard."""
    app_state = request.app.state
    ready = bool(getattr(app_state, "copilot", None))
    return HealthResponse(
        status="ok" if ready else "degraded",
        llm_provider=str(getattr(app_state, "llm_provider", "unknown")),
        vectorstore_ready=bool(getattr(app_state, "vectorstore_ready", False)),
        version=APP_VERSION,
    )
