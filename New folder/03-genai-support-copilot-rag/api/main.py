# File: api/main.py
"""FastAPI entrypoint: wires the RAG chain, token-bucket rate limiting, CORS
and structured error handling. Boots in degraded mode when API keys are absent."""
from __future__ import annotations

import os
import time
import uuid
from contextlib import asynccontextmanager
from threading import Lock
from typing import AsyncIterator, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from api.routes import router
from api.schemas import APP_VERSION, ErrorResponse
from core.logging_utils import configure_logging, get_logger
from ingestion.pipeline import build_embeddings, connect_pinecone_store
from rag.chain import SupportCopilotChain, build_llm
from rag.memory import DEFAULT_MEMORY_WINDOW_TURNS
from rag.retriever import RetrieverConfig, build_retriever

load_dotenv()
logger = get_logger(__name__)


class TokenBucket:
    """Classic token-bucket limiter: burst up to ``capacity``, steady refill."""

    __slots__ = ("capacity", "refill_per_sec", "tokens", "updated_at")

    def __init__(self, capacity: int, refill_per_sec: float) -> None:
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.tokens = float(capacity)
        self.updated_at = time.monotonic()

    def try_acquire(self) -> bool:
        now = time.monotonic()
        elapsed = now - self.updated_at
        self.updated_at = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-client-IP token bucket; ``/health`` is exempt; stub for Redis-backed limits."""

    def __init__(self, app, capacity: int = 30, refill_per_sec: float = 1.0) -> None:
        super().__init__(app)
        self._capacity = capacity
        self._refill_per_sec = refill_per_sec
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = Lock()

    @staticmethod
    def _client_ip(request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for", "")
        first_hop = forwarded.split(",")[0].strip()
        if first_hop:
            return first_hop
        return request.client.host if request.client else "anonymous"

    def _bucket_for(self, client_ip: str) -> TokenBucket:
        with self._lock:
            bucket = self._buckets.get(client_ip)
            if bucket is None:
                bucket = TokenBucket(self._capacity, self._refill_per_sec)
                self._buckets[client_ip] = bucket
            return bucket

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        if request.url.path == "/health":
            return await call_next(request)
        client_ip = self._client_ip(request)
        if not self._bucket_for(client_ip).try_acquire():
            logger.warning("rate_limited client_ip=%s path=%s", client_ip, request.url.path)
            body = ErrorResponse(
                error="rate_limit_exceeded",
                detail="Too many requests. Please retry shortly.",
                request_id=request.headers.get("x-request-id"),
            )
            return JSONResponse(status_code=429, content=body.model_dump(), headers={"Retry-After": "1"})
        return await call_next(request)


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Build embeddings, vector store and the copilot chain exactly once."""
    configure_logging(os.getenv("LOG_LEVEL", "INFO"))
    llm = build_llm()
    embeddings = build_embeddings()
    store = connect_pinecone_store(embeddings=embeddings)
    threshold = _env_float("RETRIEVER_SCORE_THRESHOLD", 0.0)
    retriever = build_retriever(
        store,
        RetrieverConfig(score_threshold=threshold if threshold > 0 else None),
        embeddings=embeddings,
    )
    app.state.copilot = SupportCopilotChain(
        llm=llm,
        retriever=retriever,
        memory_window_turns=int(_env_float("MEMORY_WINDOW_TURNS", DEFAULT_MEMORY_WINDOW_TURNS)),
    )
    app.state.llm_provider = "mock" if isinstance(llm, FakeListChatModel) else "openai"
    app.state.vectorstore_ready = store is not None
    logger.info(
        "startup_complete llm_provider=%s vectorstore_ready=%s",
        app.state.llm_provider,
        app.state.vectorstore_ready,
    )
    yield
    logger.info("shutdown_complete")


app = FastAPI(
    title="GenAI Support Copilot (RAG)",
    version=APP_VERSION,
    description="Customer-support copilot grounded on a Pinecone knowledge base.",
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware, capacity=int(_env_float("RATE_LIMIT_CAPACITY", 30)), refill_per_sec=_env_float("RATE_LIMIT_REFILL_PER_SEC", 1.0))
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", include_in_schema=False)
async def root() -> JSONResponse:
    return JSONResponse({"service": "genai-support-copilot", "version": APP_VERSION, "docs": "/docs", "health": "/health"})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    body = ErrorResponse(
        error="validation_error",
        detail=str(exc.errors()[:3]),
        request_id=request.headers.get("x-request-id"),
    )
    return JSONResponse(status_code=422, content=body.model_dump())


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    body = ErrorResponse(
        error="http_error",
        detail=str(exc.detail),
        request_id=request.headers.get("x-request-id"),
    )
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = uuid.uuid4().hex[:12]
    logger.exception("unhandled_error request_id=%s error=%s", request_id, exc)
    body = ErrorResponse(
        error="internal_error",
        detail=f"Unexpected server error. Reference: {request_id}",
        request_id=request_id,
    )
    return JSONResponse(status_code=500, content=body.model_dump())
