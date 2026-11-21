"""Knowledge coded tools (M7/M11): permission-aware keyword retrieval.

Order is load-bearing: role filter runs BEFORE any content is read for
scoring, so unauthorized documents never enter the LLM context — never
retrieve-all-then-filter. Docs without ACL metadata are invisible.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from common.redaction import redact_text
from neuro_san.interfaces.coded_tool import CodedTool

KNOWLEDGE_ROOT = Path("knowledge")

_STOPWORDS = frozenset({
    "the", "and", "for", "with", "how", "what", "when", "where", "who",
    "are", "was", "were", "been", "have", "has", "had", "will", "would",
    "should", "could", "does", "doing", "about", "into", "from", "that",
    "this", "your", "you", "our", "their", "they", "them", "then", "than",
    "also", "such", "only", "more", "most", "other", "some", "any", "all",
    "can", "may", "request",
})


def _acl_allows(doc_path: Path, user_role: str) -> bool:
    """Docs must declare allowed_roles in a leading HTML comment to be visible.

    Expected first-line form: <!-- allowed_roles: employee, manager -->
    Missing/unparseable ACL → invisible (safe default).
    """
    try:
        head = doc_path.read_text(encoding="utf-8", errors="replace")[:500]
    except OSError:
        return False
    if "allowed_roles:" not in head:
        return False
    line = next((ln for ln in head.splitlines() if "allowed_roles:" in ln), "")
    segment = line.split("allowed_roles:", 1)[1].split("-->")[0]
    roles = {r.strip().lower() for r in segment.split(",") if r.strip()}
    return user_role.strip().lower() in roles


def _terms(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower())
            if len(w) > 2 and w not in _STOPWORDS}


def _sections(doc_path: Path) -> list[tuple[str, str]]:
    """Split a doc into (section title, body) chunks on ## headers."""
    text = doc_path.read_text(encoding="utf-8", errors="replace")
    chunks: list[tuple[str, str]] = []
    title, body = doc_path.stem, []
    for line in text.splitlines():
        if line.startswith("## "):
            if body:
                chunks.append((title, "\n".join(body).strip()))
            title, body = line[3:].strip(), []
        elif line.startswith("# ") or line.startswith("<!--"):
            continue  # H1 title / ACL comment are metadata, not content
        else:
            body.append(line)
    if body:
        chunks.append((title, "\n".join(body).strip()))
    return [(t, b) for t, b in chunks if b]


def _score(query_terms: set[str], title: str, body: str) -> float:
    if not query_terms:
        return 0.0
    text_terms = _terms(title + " " + body)
    overlap = len(query_terms & text_terms)
    return round(100 * overlap / len(query_terms), 1)


class SearchEnterpriseKnowledge(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        query = str(args.get("query", ""))
        user_role = str(args.get("user_role", sly_data.get("user_role", "employee")))
        query_terms = _terms(query)
        hits = []
        if KNOWLEDGE_ROOT.is_dir():
            for doc in sorted(KNOWLEDGE_ROOT.rglob("*.md")):
                if not _acl_allows(doc, user_role):
                    continue  # filtered BEFORE llm context — never retrieved
                for section, body in _sections(doc):
                    confidence = _score(query_terms, section, body)
                    if confidence > 0:
                        hits.append({"doc_id": doc.stem, "path": str(doc),
                                     "section": section,
                                     "excerpt": redact_text(body[:300]),
                                     "confidence": confidence})
        hits.sort(key=lambda h: h["confidence"], reverse=True)
        top = hits[:5]
        return {"answer": top[0]["excerpt"] if top else "",
                "results": top,
                "source": {"doc_id": top[0]["doc_id"], "section": top[0]["section"]}
                if top else {}}



class GetDocumentAccessContext(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        doc_id = str(args.get("doc_id", ""))
        user_role = str(args.get("user_role", sly_data.get("user_role", "employee")))
        matches = list(KNOWLEDGE_ROOT.rglob(f"{doc_id}.md")) if KNOWLEDGE_ROOT.is_dir() else []
        if not matches:
            return {"doc_id": doc_id, "accessible": False, "reason": "not found"}
        accessible = _acl_allows(matches[0], user_role)
        return {"doc_id": doc_id, "accessible": accessible,
                "reason": "" if accessible else "ACCESS DENIED for role " + user_role}


class CiteKnowledgeSource(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        return {"doc_id": str(args.get("doc_id", "")),
                "section": str(args.get("section", "")),
                "confidence": float(args.get("confidence", 0.0) or 0.0)}
