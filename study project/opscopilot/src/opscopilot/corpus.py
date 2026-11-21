"""Load synthetic markdown corpus (front-matter + body). Pure python, offline."""

from pathlib import Path

import yaml

from opscopilot.models import Document


def parse_markdown_file(path: Path) -> Document:
    """Parse one markdown file with YAML front-matter into a Document."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"Missing front-matter in {path}")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Bad front-matter in {path}")
    meta_raw = parts[1]
    body = parts[2].lstrip("\n")
    meta: dict[str, object] = yaml.safe_load(meta_raw) or {}
    doc_id = str(meta.get("doc_id", path.stem))
    title = str(meta.get("title", doc_id))
    doc_type_raw = str(meta.get("doc_type", "kedb"))
    doc_type = doc_type_raw if doc_type_raw in ("kedb", "sop") else "kedb"
    service = str(meta.get("service", "general"))
    status_raw = str(meta.get("status", "active"))
    status = status_raw if status_raw in ("active", "retired") else "active"
    updated_at = str(meta.get("updated_at", ""))
    # mypy narrowing for Literal fields via explicit branch
    if doc_type == "sop":
        dtype: str = "sop"
    else:
        dtype = "kedb"
    st: str = "retired" if status == "retired" else "active"
    kwargs: dict[str, str] = {
        "doc_id": doc_id,
        "title": title,
        "service": service,
        "updated_at": updated_at,
        "content": body,
        "path": str(path),
    }
    if dtype == "sop":
        if st == "retired":
            return Document(doc_type="sop", status="retired", **kwargs)
        return Document(doc_type="sop", status="active", **kwargs)
    if st == "retired":
        return Document(doc_type="kedb", status="retired", **kwargs)
    return Document(doc_type="kedb", status="active", **kwargs)


def load_corpus(corpus_dir: Path | str) -> list[Document]:
    """Load every *.md file under corpus_dir (sorted for determinism)."""
    root = Path(corpus_dir)
    if not root.exists():
        return []
    docs: list[Document] = []
    for path in sorted(root.rglob("*.md")):
        docs.append(parse_markdown_file(path))
    return docs
