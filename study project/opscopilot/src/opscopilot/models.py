"""Pydantic v2 data shapes for the stable /v1 contract (P2/P3/P4 will reuse these)."""

from typing import Literal

from pydantic import BaseModel, Field

Confidence = Literal["HIGH", "MEDIUM", "LOW"]
DocStatus = Literal["active", "retired"]
DocType = Literal["kedb", "sop"]


class Document(BaseModel):
    doc_id: str
    doc_type: DocType
    title: str
    service: str
    status: DocStatus = "active"
    updated_at: str = ""
    content: str = ""  # full markdown body (without front-matter)
    path: str = ""


class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    doc_type: DocType
    title: str
    section: str
    service: str
    status: DocStatus = "active"
    updated_at: str = ""
    content: str


class ScoredChunk(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    section: str
    service: str
    status: DocStatus = "active"
    score: float
    rank: int
    snippet: str = ""


class CitationCheck(BaseModel):
    cited_ids: list[str] = Field(default_factory=list)
    valid: list[str] = Field(default_factory=list)
    invalid: list[str] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.invalid) == 0


class RetrievalDebug(BaseModel):
    keyword_ranking: list[str] = Field(default_factory=list)
    vector_ranking: list[str] = Field(default_factory=list)
    fused_ranking: list[str] = Field(default_factory=list)


# --- API contract models ---


class SearchRequest(BaseModel):
    question: str = Field(min_length=1)
    service: str | None = None
    top_k: int | None = Field(default=None, ge=1, le=20)


class SearchHit(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    section: str
    service: str
    status: DocStatus
    score: float
    rank: int
    snippet: str


class SearchResponse(BaseModel):
    hits: list[SearchHit]
    retrieval_debug: RetrievalDebug


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    service: str | None = None
    top_k: int | None = Field(default=None, ge=1, le=20)


class Citation(BaseModel):
    doc_id: str
    section: str


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: Confidence
    refused: bool
    retrieval_debug: RetrievalDebug | None = None


class SourceResponse(BaseModel):
    doc_id: str
    doc_type: DocType
    title: str
    service: str
    status: DocStatus
    updated_at: str
    content: str


class HealthResponse(BaseModel):
    status: str
    docs: int
    chunks: int
    corpus_loaded: bool
