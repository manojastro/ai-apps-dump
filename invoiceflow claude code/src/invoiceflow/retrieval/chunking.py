"""Split policy, GST and contract Markdown into one chunk per numbered section (§x.y).

A chunk runs from a paragraph that starts with "§x.y" to the next such paragraph or
heading, so tables that belong to a section stay with it. The contract header table
becomes a "parties" chunk.
"""

import re
from datetime import date
from pathlib import Path

from invoiceflow.retrieval.models import ALL_ROLES, CONTRACT_ROLES, GLOBAL_VENDOR, Chunk, DocType

_SECTION = re.compile(r"^§(\d+\.\d+)\s")
_HEADING = re.compile(r"^##\s+(?:§\d+\s+)?(.*)$")
_TERM = re.compile(r"\|\s*Term\s*\|\s*(\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})")
_VENDOR = re.compile(r"\((V\d{3})\)")

DOC_IDS: dict[str, tuple[str, DocType]] = {
    "ap_policy_manual.md": ("AP-POL", "policy"),
    "gst_guide.md": ("GST-GUIDE", "gst_guide"),
}


def chunk_document(text: str, doc_id: str, doc_type: DocType) -> list[Chunk]:
    vendor_id, start, end = GLOBAL_VENDOR, None, None
    if doc_type == "contract":
        vendor = _VENDOR.search(text)
        term = _TERM.search(text)
        vendor_id = vendor.group(1) if vendor else GLOBAL_VENDOR
        if term:
            start, end = date.fromisoformat(term.group(1)), date.fromisoformat(term.group(2))
    roles = CONTRACT_ROLES if doc_type == "contract" else ALL_ROLES

    chunks: list[Chunk] = []
    title = ""
    section: str | None = None
    buffer: list[str] = []
    header: list[str] = []

    def flush() -> None:
        if section and buffer:
            body = "\n".join(buffer).strip()
            chunks.append(
                Chunk(
                    chunk_id=f"{doc_id}:§{section}",
                    doc_id=doc_id,
                    doc_type=doc_type,
                    section=f"§{section}",
                    title=title,
                    text=f"{title}. {body}" if title else body,
                    vendor_id=vendor_id,
                    effective_from=start,
                    effective_to=end,
                    allowed_roles=roles,
                )
            )

    for line in text.splitlines():
        heading = _HEADING.match(line)
        if heading:
            flush()
            section, buffer = None, []
            title = heading.group(1).strip()
            continue
        match = _SECTION.match(line)
        if match:
            flush()
            section, buffer = match.group(1), [line]
        elif section:
            buffer.append(line)
        elif doc_type == "contract" and line.startswith("|"):
            header.append(line)
    flush()

    if header:
        chunks.insert(
            0,
            Chunk(
                chunk_id=f"{doc_id}:parties",
                doc_id=doc_id,
                doc_type=doc_type,
                section="parties",
                title="Parties and term",
                text="Parties and term.\n" + "\n".join(header),
                vendor_id=vendor_id,
                effective_from=start,
                effective_to=end,
                allowed_roles=roles,
            ),
        )
    return chunks


def load_chunks(docs_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for name, (doc_id, doc_type) in DOC_IDS.items():
        text = (docs_dir / name).read_text(encoding="utf-8")
        chunks += chunk_document(text, doc_id, doc_type)
    for path in sorted((docs_dir / "contracts").glob("CT-*.md")):
        chunks += chunk_document(path.read_text(encoding="utf-8"), path.stem, "contract")
    return chunks
