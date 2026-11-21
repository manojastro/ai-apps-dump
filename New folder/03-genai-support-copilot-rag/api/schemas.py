# File: api/schemas.py
"""Pydantic v2 request/response contracts for the copilot API."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

APP_VERSION = "1.0.0"

_SESSION_ID_PATTERN = r"^[A-Za-z0-9_.:\-]{1,128}$"


class ChatRequest(BaseModel):
    """A single user turn within a session."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"session_id": "sess-42", "message": "Can I get a refund after 30 days?"}
            ]
        }
    )

    session_id: str = Field(
        ...,
        pattern=_SESSION_ID_PATTERN,
        description="Stable conversation identifier.",
        examples=["sess-42"],
    )
    message: str = Field(
        ..., min_length=1, max_length=4000, examples=["Can I get a refund after 30 days?"]
    )


class Citation(BaseModel):
    """One knowledge-base source backing the answer."""

    source: str = Field(..., examples=["sample_refund_policy.md"])
    section: Optional[str] = Field(None, examples=["Refund window"])


class ChatResponse(BaseModel):
    """Grounded answer plus cited sources."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "answer": "Refunds are available within 30 days of purchase. [source: sample_refund_policy.md]",
                    "sources": [{"source": "sample_refund_policy.md", "section": None}],
                    "session_id": "sess-42",
                }
            ]
        }
    )

    answer: str
    sources: List[Citation] = Field(default_factory=list)
    session_id: str


class IngestRequest(BaseModel):
    """Trigger a knowledge-base ingestion run (trusted-operator endpoint)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"path": None, "namespace": "support-docs", "dry_run": False}]
        }
    )

    path: Optional[str] = Field(
        None, description="Directory to ingest; defaults to ./data.", examples=["data"]
    )
    namespace: Optional[str] = Field(None, examples=["support-docs"])
    dry_run: bool = Field(False, description="Parse and chunk without writing to Pinecone.")


class IngestResponse(BaseModel):
    """Acknowledgement of an asynchronously running ingestion job."""

    job_id: str = Field(..., examples=["3f2a9c1e8b7d4f6a9c0e1d2b3a4f5c6d"])
    status: Literal["queued"] = "queued"


class JobStatusResponse(BaseModel):
    """Current state of one ingestion job."""

    job_id: str
    status: str = Field(..., examples=["completed"])
    submitted_at: str
    finished_at: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Liveness plus degraded-mode indicators."""

    status: Literal["ok", "degraded"]
    llm_provider: str = Field(..., examples=["openai"])
    vectorstore_ready: bool
    version: str


class ErrorResponse(BaseModel):
    """Uniform error envelope returned by every failure path."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "error": "rate_limit_exceeded",
                    "detail": "Too many requests. Please retry shortly.",
                    "request_id": "b0ca4f21",
                }
            ]
        }
    )

    error: str
    detail: Optional[str] = None
    request_id: Optional[str] = None
