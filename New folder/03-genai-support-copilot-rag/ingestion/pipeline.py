# File: ingestion/pipeline.py
"""Ingestion core: load -> chunk -> enrich -> embed -> upsert to Pinecone.

Idempotency: every chunk receives a deterministic vector ID
(``md5(source :: chunk_index)``), so re-running the pipeline over unchanged
files overwrites the same IDs instead of creating duplicates.

Usage::

    python -m ingestion.pipeline --dry-run
    python -m ingestion.pipeline --namespace support-docs
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.logging_utils import configure_logging, get_logger
from ingestion.loaders import LoadResult, load_documents

load_dotenv()
logger = get_logger(__name__)

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
DEFAULT_DATA_DIR = Path("data")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class IngestionConfig:
    """Typed knobs for one ingestion run."""

    data_dir: Path = DEFAULT_DATA_DIR
    chunk_size: int = 1000
    chunk_overlap: int = 150
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    batch_size: int = 100
    namespace: Optional[str] = None
    dry_run: bool = False


@dataclass
class IngestionReport:
    """Structured outcome of an ingestion run."""

    files_seen: int = 0
    files_loaded: int = 0
    files_failed: int = 0
    documents_loaded: int = 0
    chunks_created: int = 0
    vectors_upserted: int = 0
    dry_run: bool = False
    duration_ms: int = 0
    errors: List[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            "IngestionReport("
            f"dry_run={self.dry_run}, files={self.files_loaded}/{self.files_seen}, "
            f"chunks={self.chunks_created}, upserted={self.vectors_upserted}, "
            f"duration_ms={self.duration_ms}, errors={len(self.errors)})"
        )


def chunk_id(source: str, chunk_index: int) -> str:
    """Deterministic, collision-safe-per-source vector ID (stable across runs)."""
    return hashlib.md5(f"{source}::{chunk_index}".encode("utf-8")).hexdigest()


def extract_section_title(content: str, fallback: str = "unknown") -> str:
    """Best-effort section heading for a chunk (markdown heading, else first line)."""
    match = _HEADING_RE.search(content)
    if match:
        return match.group(1)[:80]
    for line in content.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:80]
    return fallback


def _relative_source(raw_source: str, data_dir: Path) -> str:
    """Normalize a document's source path relative to the data dir (posix style)."""
    try:
        path = Path(raw_source)
        if path.is_absolute():
            return path.resolve().relative_to(data_dir.resolve()).as_posix()
        return path.as_posix()
    except ValueError:
        return Path(raw_source).name


def enrich_chunk(
    chunk: Document,
    source: str,
    chunk_index: int,
    ingested_at: str,
) -> Document:
    """Attach provenance metadata used by retrieval citations and debugging."""
    chunk.metadata.update(
        {
            "source": source,
            "section": extract_section_title(chunk.page_content),
            "chunk_index": chunk_index,
            "ingested_at": ingested_at,
        }
    )
    return chunk


def split_and_enrich(documents: List[Document], config: IngestionConfig, ingested_at: str) -> List[Document]:
    """Chunk documents and enrich each chunk with per-source metadata + IDs."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        length_function=len,
        add_start_index=False,
    )
    chunks: List[Document] = []
    counters: dict[str, int] = {}
    for doc in documents:
        source = _relative_source(str(doc.metadata.get("source", "unknown")), config.data_dir)
        for piece in splitter.split_documents([doc]):
            index = counters.get(source, 0)
            counters[source] = index + 1
            chunks.append(enrich_chunk(piece, source, index, ingested_at))
    return chunks


@lru_cache(maxsize=4)
def _cached_embeddings(model_name: str) -> Embeddings:
    from langchain_huggingface import HuggingFaceEmbeddings

    logger.info("loading embeddings model=%s", model_name)
    return HuggingFaceEmbeddings(
        model_name=model_name,
        encode_kwargs={"normalize_embeddings": True},
        show_progress=False,
    )


def build_embeddings(model_name: Optional[str] = None) -> Embeddings:
    """Factory for local HuggingFace embeddings (cached per model name)."""
    resolved = model_name or os.getenv("EMBEDDING_MODEL") or DEFAULT_EMBEDDING_MODEL
    return _cached_embeddings(resolved)


def ensure_pinecone_index(pc: object, index_name: str) -> None:
    """Create a serverless index if missing (dimension matched to MiniLM-L6-v2)."""
    from pinecone import ServerlessSpec

    existing = {entry["name"] for entry in pc.list_indexes()}  # type: ignore[attr-defined]
    if index_name in existing:
        return
    cloud = os.getenv("PINECONE_CLOUD", "aws")
    region = os.getenv("PINECONE_REGION", "us-east-1")
    logger.info("creating serverless index name=%s dim=%d region=%s", index_name, EMBEDDING_DIMENSION, region)
    pc.create_index(  # type: ignore[attr-defined]
        name=index_name,
        dimension=EMBEDDING_DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud=cloud, region=region),
    )


def connect_pinecone_store(
    embeddings: Embeddings,
    index_name: Optional[str] = None,
    namespace: Optional[str] = None,
):
    """Return a ``PineconeVectorStore`` or ``None`` when credentials are absent.

    Returning ``None`` (instead of raising) lets the API boot in degraded mode.
    """
    api_key = os.getenv("PINECONE_API_KEY")
    resolved_index = index_name or os.getenv("PINECONE_INDEX")
    if not api_key or not resolved_index:
        logger.warning("pinecone_not_configured - vector store unavailable; degraded mode active")
        return None
    from langchain_pinecone import PineconeVectorStore
    from pinecone import Pinecone

    pc = Pinecone(api_key=api_key)
    ensure_pinecone_index(pc, resolved_index)
    index = pc.Index(resolved_index)
    namespace = namespace or os.getenv("PINECONE_NAMESPACE") or None
    logger.info("connected to pinecone index=%s namespace=%s", resolved_index, namespace or "<default>")
    return PineconeVectorStore(index=index, embedding=embeddings, text_key="text", namespace=namespace)


class IngestionPipeline:
    """Orchestrates load -> chunk -> enrich -> embed -> idempotent batched upsert."""

    def __init__(self, config: IngestionConfig, embeddings: Optional[Embeddings] = None) -> None:
        self.config = config
        self._embeddings = embeddings

    def run(self) -> IngestionReport:
        started = time.perf_counter()
        report = IngestionReport(dry_run=self.config.dry_run)

        loaded: LoadResult = load_documents(self.config.data_dir)
        report.files_seen = len(loaded.loaded_files) + len(loaded.failures)
        report.files_loaded = len(loaded.loaded_files)
        report.files_failed = len(loaded.failures)
        report.errors.extend(f"{path.name}: {message}" for path, message in loaded.failures)

        ingested_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        chunks = split_and_enrich(loaded.documents, self.config, ingested_at)
        report.chunks_created = len(chunks)
        report.duration_ms = int((time.perf_counter() - started) * 1000)

        if not chunks:
            logger.error("ingestion_aborted reason=no_chunks data_dir=%s", self.config.data_dir)
            return report

        ids = [chunk_id(chunk.metadata["source"], chunk.metadata["chunk_index"]) for chunk in chunks]

        if self.config.dry_run:
            sample = list(zip([c.metadata["source"] for c in chunks[:3]], ids[:3]))
            logger.info(
                "dry_run_complete chunks=%d planned_batches=%d sample_ids=%s",
                len(chunks),
                (len(chunks) + self.config.batch_size - 1) // self.config.batch_size,
                sample,
            )
            return report

        embeddings = self._embeddings or build_embeddings(self.config.embedding_model)
        store = connect_pinecone_store(embeddings=embeddings, namespace=self.config.namespace)
        if store is None:
            raise RuntimeError(
                "Cannot ingest: PINECONE_API_KEY / PINECONE_INDEX are not configured. "
                "Use --dry-run to inspect without writing."
            )

        upserted = 0
        for start in range(0, len(chunks), self.config.batch_size):
            batch_docs = chunks[start : start + self.config.batch_size]
            batch_ids = ids[start : start + self.config.batch_size]
            store.add_documents(documents=batch_docs, ids=batch_ids)
            upserted += len(batch_docs)
            logger.info(
                "batch_upserted count=%d total=%d/%d",
                len(batch_docs),
                upserted,
                len(chunks),
            )
        report.vectors_upserted = upserted
        report.duration_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "ingestion_complete %s",
            report.summary(),
            extra={"report": asdict(report)},
        )
        return report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest support KB files into Pinecone.")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR), help="Directory containing PDF/MD/TXT files.")
    parser.add_argument("--index", default=None, help="Pinecone index name (defaults to $PINECONE_INDEX).")
    parser.add_argument("--namespace", default=None, help="Optional Pinecone namespace.")
    parser.add_argument("--dry-run", action="store_true", help="Load/chunk only; no network writes.")
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--chunk-overlap", type=int, default=150)
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))
    args = parser.parse_args(argv)

    configure_logging(args.log_level)
    config = IngestionConfig(
        data_dir=Path(args.data_dir),
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        namespace=args.namespace,
        dry_run=args.dry_run,
    )
    report = IngestionPipeline(config).run()
    print(report.summary())
    return 0 if not report.files_failed or report.files_loaded else 1


if __name__ == "__main__":
    raise SystemExit(main())
