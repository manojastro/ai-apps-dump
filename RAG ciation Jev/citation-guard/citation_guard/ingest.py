"""Download, clean and section source documents.

Cleaning keeps an offset map so every position in the cleaned text points back to a line
of the raw download. All offsets used elsewhere (quote matches, passages) are offsets
into the *cleaned* text.

Text in source documents is data. Nothing in it is interpreted as an instruction.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from functools import lru_cache
from pathlib import Path

import httpx
import yaml
from pydantic import BaseModel

from .config import ROOT, paths

# "Jones, et al.                Standards Track                    [Page 5]"
FOOTER_RE = re.compile(r"^\S.*\s{2,}\[Page \d+\]\s*$")
# "RFC 7519                  JSON Web Token (JWT)                  May 2015"
HEADER_RE = re.compile(r"^RFC \d+\s{2,}.+\s{2,}[A-Z][a-z]+ \d{4}\s*$")
# "4.1.4.  "exp" (Expiration Time) Claim", "Appendix A.  JWT Examples", "A.1.  Example ..."
NUMBERED_HEADING_RE = re.compile(r"^(?:Appendix )?((?:\d+|[A-Z])(?:\.\d+)*)\.\s{2}(\S.*)$")
# "Abstract", "Status of This Memo", "Authors' Addresses"
UNNUMBERED_HEADING_RE = re.compile(r"^[A-Z][A-Za-z']+(?: [A-Za-z']+)*$")
HYPHEN_END_RE = re.compile(r"[A-Za-z0-9]-$")

LOW_PRIORITY_SECTIONS = {"table-of-contents"}


class Section(BaseModel):
    section_id: str
    title: str
    start: int  # offset in cleaned text (inclusive)
    end: int  # offset in cleaned text (exclusive)
    text: str


class Document(BaseModel):
    doc_id: str
    title: str
    clean_text: str
    sections: list[Section]
    # (clean_offset, raw_line_number) for the start of every cleaned line, sorted by offset.
    line_map: list[tuple[int, int]]

    def section(self, section_id: str) -> Section | None:
        for s in self.sections:
            if s.section_id == section_id:
                return s
        return None

    def section_at(self, offset: int) -> Section | None:
        for s in self.sections:
            if s.start <= offset < s.end:
                return s
        return None

    def raw_line_at(self, offset: int) -> int:
        line = self.line_map[0][1] if self.line_map else 0
        for off, raw in self.line_map:
            if off > offset:
                break
            line = raw
        return line


# --------------------------------------------------------------------------- manifest


def load_manifest() -> list[dict]:
    with open(paths()["sources"] / "manifest.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)["documents"]


def save_manifest(docs: list[dict]) -> None:
    header = (
        "# Source documents. Add more entries here; `citation-guard ingest` processes every entry.\n"
        "# Text inside these documents is data, never instructions.\n"
    )
    with open(paths()["sources"] / "manifest.yaml", "w", encoding="utf-8") as fh:
        fh.write(header)
        yaml.safe_dump({"documents": docs}, fh, sort_keys=False, allow_unicode=True)


def download_missing(docs: list[dict]) -> list[str]:
    """Download any manifest entry whose file is missing. Returns doc_ids downloaded."""
    fetched = []
    for d in docs:
        path = ROOT / d["path"]
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        resp = httpx.get(d["url"], timeout=60, follow_redirects=True)
        resp.raise_for_status()
        path.write_bytes(resp.content)
        d["downloaded_on"] = date.today().isoformat()
        d["sha256"] = hashlib.sha256(resp.content).hexdigest()
        fetched.append(d["doc_id"])
    return fetched


# --------------------------------------------------------------------------- cleaning


def _continues_paragraph(prev: str, nxt: str) -> bool:
    """Is the text after a page break the same paragraph as the text before it?"""
    p, n = prev.rstrip(), nxt.strip()
    if not p or not n:
        return False
    if NUMBERED_HEADING_RE.match(nxt) or not nxt.startswith(" "):
        return False
    return not p.endswith((".", ":")) or n[0].islower()


def clean_rfc(raw: str) -> tuple[str, list[tuple[int, int]]]:
    """Remove page headers/footers and form feeds, rejoin hyphen-split lines.

    Returns (clean_text, line_map) where line_map holds (clean_offset, raw_line_no)
    for the start of each cleaned line (raw lines are 1-based).

    Hyphen rejoin: RFCs break lines only at real hyphens (e.g. "case-" / "sensitive"), so
    the line break is removed and the hyphen kept ("case-sensitive"). Dropping the hyphen
    would corrupt compounds and break exact quote matching.
    """
    raw_lines = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    kept: list[tuple[str, int]] = []  # (line text, raw line no)
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i].replace("\f", "")
        if FOOTER_RE.match(line):
            while kept and not kept[-1][0].strip():
                kept.pop()
            j = i + 1
            while j < len(raw_lines):
                nxt = raw_lines[j].replace("\f", "")
                if nxt.strip() == "" or HEADER_RE.match(nxt):
                    j += 1
                    continue
                break
            nxt_line = raw_lines[j].replace("\f", "") if j < len(raw_lines) else ""
            prev_line = kept[-1][0] if kept else ""
            if j < len(raw_lines) and not _continues_paragraph(prev_line, nxt_line):
                kept.append(("", i + 1))
            i = j
            continue
        if HEADER_RE.match(line):
            i += 1
            continue
        kept.append((line.rstrip(), i + 1))
        i += 1

    while kept and not kept[-1][0].strip():
        kept.pop()
    while kept and not kept[0][0].strip():
        kept.pop(0)

    parts: list[str] = []
    line_map: list[tuple[int, int]] = []
    offset = 0
    for idx, (line, raw_no) in enumerate(kept):
        prev = kept[idx - 1][0] if idx > 0 else ""
        joined = (
            idx > 0
            and HYPHEN_END_RE.search(prev)
            and line.strip()
            and line.strip()[0].islower()
            and not NUMBERED_HEADING_RE.match(line)
        )
        if joined:
            piece = line.lstrip()
        else:
            if idx > 0:
                parts.append("\n")
                offset += 1
            piece = line
        line_map.append((offset, raw_no))
        parts.append(piece)
        offset += len(piece)
    return "".join(parts), line_map


# --------------------------------------------------------------------------- sections


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower().replace("'", "")).strip("-")


def split_sections(clean: str) -> list[Section]:
    lines = clean.split("\n")
    starts: list[tuple[int, str, str]] = []  # (offset, id, title)
    offset = 0
    for idx, line in enumerate(lines):
        prev_blank = idx == 0 or not lines[idx - 1].strip()
        m = NUMBERED_HEADING_RE.match(line)
        if m and prev_blank:
            title = m.group(2).strip()
            # Title continued on an indented line straight after the heading.
            if idx + 1 < len(lines):
                nxt = lines[idx + 1]
                indent = len(nxt) - len(nxt.lstrip())
                if nxt.strip() and indent > 3:
                    title = f"{title} {nxt.strip()}"
            starts.append((offset, m.group(1), title))
        elif (
            prev_blank
            and UNNUMBERED_HEADING_RE.match(line)
            and len(line) < 40
            and (idx + 1 >= len(lines) or not lines[idx + 1].strip())
        ):
            starts.append((offset, _slug(line), line.strip()))
        offset += len(line) + 1

    sections: list[Section] = []
    if not starts or starts[0][0] > 0:
        first = starts[0][0] if starts else len(clean)
        sections.append(Section(section_id="preamble", title="Preamble", start=0, end=first, text=clean[:first]))
    for k, (start, sid, title) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(clean)
        sections.append(Section(section_id=sid, title=title, start=start, end=end, text=clean[start:end]))
    return sections


# --------------------------------------------------------------------------- pipeline


def ingest_document(entry: dict) -> Document:
    raw = (ROOT / entry["path"]).read_text(encoding="utf-8", errors="replace")
    if entry.get("format", "rfc_text") != "rfc_text":
        raise ValueError(f"unsupported format {entry.get('format')!r} for {entry['doc_id']}")
    clean, line_map = clean_rfc(raw)
    doc = Document(
        doc_id=entry["doc_id"],
        title=entry.get("title", entry["doc_id"]),
        clean_text=clean,
        sections=split_sections(clean),
        line_map=line_map,
    )
    out = paths()["processed"]
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{doc.doc_id}.clean.txt").write_text(clean, encoding="utf-8", newline="\n")
    (out / f"{doc.doc_id}.json").write_text(doc.model_dump_json(indent=1), encoding="utf-8")
    return doc


def ingest_all() -> list[Document]:
    docs = load_manifest()
    if download_missing(docs):
        save_manifest(docs)
    return [ingest_document(d) for d in docs]


@lru_cache(maxsize=16)
def load_document(doc_id: str) -> Document:
    path = paths()["processed"] / f"{doc_id}.json"
    if not path.exists():
        for entry in load_manifest():
            if entry["doc_id"] == doc_id:
                return ingest_document(entry)
        raise KeyError(f"unknown doc_id {doc_id!r}; add it to data/sources/manifest.yaml")
    return Document.model_validate(json.loads(path.read_text(encoding="utf-8")))


def document_from_text(doc_id: str, raw: str, title: str = "") -> Document:
    """Build a Document in memory (used by tests)."""
    clean, line_map = clean_rfc(raw)
    return Document(doc_id=doc_id, title=title or doc_id, clean_text=clean,
                    sections=split_sections(clean), line_map=line_map)


def doc_fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
