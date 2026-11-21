# File: ingestion/loaders.py
"""Multi-format document loader factory with per-file error isolation.

Supported formats: PDF (``pypdf``), Markdown and plain text. Each format has a
primary loader plus ordered fallbacks; a failure in one file never aborts the
whole ingestion run.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Sequence, Tuple

from langchain_community.document_loaders import BaseLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = frozenset({".pdf", ".md", ".txt"})


class DocumentLoadError(RuntimeError):
    """Raised when every candidate loader fails for a given file."""


@dataclass
class LoadResult:
    """Outcome of a directory load attempt."""

    documents: List[Document] = field(default_factory=list)
    loaded_files: List[Path] = field(default_factory=list)
    failures: List[Tuple[Path, str]] = field(default_factory=list)


def _text_loader(path: Path) -> BaseLoader:
    return TextLoader(str(path), encoding="utf-8")


def _pdf_loader(path: Path) -> BaseLoader:
    return PyPDFLoader(str(path))


def _markdown_loader(path: Path) -> BaseLoader:
    # Prefer structure-aware parsing when `unstructured` is installed;
    # the factory falls back to TextLoader otherwise.
    from langchain_community.document_loaders import UnstructuredMarkdownLoader

    return UnstructuredMarkdownLoader(str(path))


_LOADER_CANDIDATES: dict[str, Sequence[Callable[[Path], BaseLoader]]] = {
    ".pdf": (_pdf_loader,),
    ".md": (_markdown_loader, _text_loader),
    ".txt": (_text_loader,),
}


def iter_supported_files(directory: Path) -> List[Path]:
    """Recursively list supported files under ``directory``, skipping hidden ones."""
    if not directory.exists():
        raise FileNotFoundError(f"Data directory does not exist: {directory}")
    return sorted(
        path
        for path in directory.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
        and not path.name.startswith(".")
        and "__pycache__" not in path.parts
    )


def _load_with_fallbacks(path: Path) -> List[Document]:
    suffix = path.suffix.lower()
    candidates = _LOADER_CANDIDATES.get(suffix)
    if not candidates:
        raise DocumentLoadError(f"Unsupported file type '{suffix}': {path.name}")
    attempts: List[str] = []
    for factory in candidates:
        try:
            documents = factory(path).load()
        except Exception as exc:  # noqa: BLE001 - isolate ANY loader failure
            attempts.append(f"{factory.__name__}: {type(exc).__name__}: {exc}")
            continue
        if not documents or all(not doc.page_content.strip() for doc in documents):
            attempts.append(f"{factory.__name__}: no extractable text")
            continue
        for doc in documents:
            doc.metadata.setdefault("source", str(path))
            doc.metadata["source_type"] = suffix.lstrip(".")
        logger.info("loaded file=%s docs=%d via %s", path.name, len(documents), factory.__name__)
        return documents
    raise DocumentLoadError(f"All loaders failed for '{path.name}' -> " + " | ".join(attempts))


def load_file(path: Path) -> List[Document]:
    """Load one file; any failure is raised as :class:`DocumentLoadError`."""
    try:
        return _load_with_fallbacks(path)
    except DocumentLoadError:
        raise
    except Exception as exc:  # noqa: BLE001 - normalize unexpected errors
        raise DocumentLoadError(f"Unexpected error loading '{path.name}': {exc}") from exc


def load_documents(directory: Path) -> LoadResult:
    """Load every supported file in ``directory``, isolating errors per file.

    A broken/empty file is logged and skipped; it never blocks the rest of the run.
    """
    result = LoadResult()
    files = iter_supported_files(directory)
    logger.info("discovered files=%d in %s", len(files), directory)
    for path in files:
        try:
            result.documents.extend(load_file(path))
            result.loaded_files.append(path)
        except DocumentLoadError as exc:
            result.failures.append((path, str(exc)))
            logger.error("loader failure isolated file=%s error=%s", path.name, exc)
    return result
