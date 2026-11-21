# File: rag/retriever.py
"""Configurable retriever wrapper with MMR search and optional score filtering."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import VectorStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetrieverConfig:
    """Tuning knobs for retrieval."""

    k: int = 5
    fetch_k: int = 20
    score_threshold: Optional[float] = None


class NullRetriever(BaseRetriever):
    """Always returns zero documents — used in degraded mode (no vector store)."""

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        return []


def build_retriever(
    vectorstore: Optional[VectorStore],
    config: Optional[RetrieverConfig] = None,
    embeddings: Optional[Embeddings] = None,
) -> BaseRetriever:
    """Build an MMR retriever over ``vectorstore``; wrap with a similarity filter.

    When ``score_threshold`` is set, retrieved documents below the embedding
    similarity threshold are dropped via ``ContextualCompressionRetriever`` +
    ``EmbeddingsFilter`` before they ever reach the prompt.
    """
    cfg = config or RetrieverConfig()
    if vectorstore is None:
        logger.warning("no_vectorstore - using NullRetriever (degraded mode)")
        return NullRetriever()

    base = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": cfg.k, "fetch_k": cfg.fetch_k},
    )
    if cfg.score_threshold is None:
        return base
    threshold_embeddings = embeddings or getattr(vectorstore, "embeddings", None)
    if threshold_embeddings is None:
        logger.warning("score_threshold=%s requested but no embeddings available; skipping filter", cfg.score_threshold)
        return base
    compressor = EmbeddingsFilter(
        embeddings=threshold_embeddings,
        similarity_threshold=cfg.score_threshold,
    )
    return ContextualCompressionRetriever(base_compressor=compressor, base_retriever=base)


def format_context(documents: List[Document]) -> str:
    """Render documents as a single context string with per-chunk source tags."""
    blocks = []
    for doc in documents:
        source = doc.metadata.get("source", "unknown")
        blocks.append(f"[source: {source}]\n{doc.page_content.strip()}")
    return "\n\n".join(blocks)


def extract_sources(documents: List[Document]) -> List[str]:
    """Deduplicated, order-preserving list of source filenames."""
    seen: dict[str, None] = {}
    for doc in documents:
        raw = str(doc.metadata.get("source", "unknown"))
        seen.setdefault(Path(raw).name, None)
    return list(seen.keys())
