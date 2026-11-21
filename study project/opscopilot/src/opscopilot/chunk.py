"""Heading-aware markdown splitter. Each chunk keeps `title > section` context."""

import re

from opscopilot.models import Chunk, Document

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)\s*$")


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


def _split_long_section(
    lines: list[str], max_chars: int, prefix: str
) -> list[str]:
    """Split long section text at paragraph boundaries under max_chars."""
    paras: list[str] = []
    current = ""
    for raw in lines:
        block = raw.strip()
        if not block:
            if current:
                paras.append(current)
                current = ""
            continue
        candidate = f"{current}\n\n{block}" if current else block
        if len(prefix) + len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                paras.append(current)
            # hard-split an oversized single paragraph by sentences/words
            while len(prefix) + len(block) > max_chars:
                cut = block.rfind(". ", 0, max_chars - len(prefix))
                if cut < 0:
                    cut = max_chars - len(prefix)
                paras.append(block[:cut].strip())
                block = block[cut:].strip()
            current = block
    if current:
        paras.append(current)
    return paras if paras else [""]


def chunk_document(doc: Document, max_chars: int = 1500) -> list[Chunk]:
    """Split one Document into heading-aware chunks.

    - A level-1 heading sets the title context; deeper headings start sections.
    - Each chunk body is prefixed with `title > section` so retrieval sees context.
    - Long sections split at paragraph boundaries under max_chars.
    """
    title = doc.title
    current_section = "Overview"
    section_lines: list[str] = []
    sections: list[tuple[str, list[str]]] = []

    for line in doc.content.splitlines():
        m = _HEADING_RE.match(line.strip())
        if m:
            level = len(m.group(1))
            heading = m.group(2).strip()
            if sections or section_lines:
                # flush previous section (even if empty heading seen first)
                pass
            if level == 1:
                # flush previous before retitling
                if section_lines or sections or current_section:
                    sections.append((current_section, section_lines))
                    section_lines = []
                title = heading or doc.title
                current_section = "Overview"
            else:
                if section_lines or len(sections) > 0 or current_section != "Overview":
                    sections.append((current_section, section_lines))
                    section_lines = []
                elif section_lines:
                    sections.append((current_section, section_lines))
                    section_lines = []
                current_section = heading or "Overview"
        else:
            section_lines.append(line)
    sections.append((current_section, section_lines))

    # Drop the initial empty Overview if the doc started with a heading and no text.
    cleaned: list[tuple[str, list[str]]] = []
    for sec, lines in sections:
        text = "\n".join(lines).strip()
        if not text and sec == "Overview":
            continue
        cleaned.append((sec, lines))
    if not cleaned:
        cleaned = [("Overview", [])]

    chunks: list[Chunk] = []
    idx = 0
    for sec, lines in cleaned:
        prefix = f"{title} > {sec}\n"
        bodies = _split_long_section(lines, max_chars, prefix)
        for body in bodies:
            text = body.strip()
            if not text:
                continue
            content = prefix + text
            chunk_id = f"{doc.doc_id}#{_slug(sec)}:{idx}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    doc_id=doc.doc_id,
                    doc_type=doc.doc_type,
                    title=title,
                    section=sec,
                    service=doc.service,
                    status=doc.status,
                    updated_at=doc.updated_at,
                    content=content,
                )
            )
            idx += 1
    # Fallback: doc with no body text still yields one chunk with title context.
    if not chunks:
        chunks.append(
            Chunk(
                chunk_id=f"{doc.doc_id}#overview:0",
                doc_id=doc.doc_id,
                doc_type=doc.doc_type,
                title=title,
                section="Overview",
                service=doc.service,
                status=doc.status,
                updated_at=doc.updated_at,
                content=f"{title} > Overview\n{doc.title}",
            )
        )
    return chunks


def chunk_corpus(docs: list[Document], max_chars: int = 1500) -> list[Chunk]:
    """Chunk a whole corpus deterministically (input order preserved)."""
    out: list[Chunk] = []
    for doc in docs:
        out.extend(chunk_document(doc, max_chars=max_chars))
    return out
