"""Mock-first hybrid retrieval: TF-IDF-ish keyword + hash-embedding vector, fused with RRF.

No external DB, no network, no API keys. All deterministic so evals are reproducible.
"""

import hashlib
import math
import re

from opscopilot.models import Chunk, RetrievalDebug, ScoredChunk

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[._-][a-z0-9]+)*", re.IGNORECASE)

# Common English stopwords + corpus boilerplate ("Acme Retail Ltd" footer appears
# in every doc, so it carries no signal). Filtered from keyword scoring only;
# the mock hash-embedding still sees all tokens.
STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "when",
    "how", "what", "why", "which", "who", "whom", "is", "are", "was", "were",
    "be", "been", "being", "do", "does", "did", "doing", "have", "has", "had",
    "having", "i", "me", "my", "we", "our", "you", "your", "he", "she", "it",
    "they", "them", "this", "that", "these", "those", "am", "can", "could",
    "should", "would", "will", "just", "so", "than", "too", "very", "of",
    "at", "by", "for", "with", "about", "into", "through", "during", "before",
    "after", "above", "below", "to", "from", "up", "down", "in", "out", "on",
    "off", "over", "under", "again", "once", "here", "there", "all", "any",
    "both", "each", "few", "more", "most", "other", "some", "such", "only",
    "own", "same", "write", "get", "give", "go",
    # corpus boilerplate / company footer tokens
    "acme", "retail", "ltd", "synthetic", "fictional",
})


def tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric tokenizer that keeps codes like 0x80070005."""
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def content_terms(text: str) -> list[str]:
    """Query/chunk terms minus stopwords (used for keyword scoring)."""
    return [t for t in tokenize(text) if t not in STOPWORDS]


def keyword_ranking(query: str, chunks: list[Chunk]) -> tuple[list[str], dict[str, float]]:
    """TF-IDF-ish scoring: score = sum over query terms of tf * idf.

    idf(t) = log((N + 1) / (df + 1)) + 1. Returns (ranked chunk_ids, scores).
    Ties broken by chunk_id for determinism.
    """
    n = len(chunks)
    if n == 0 or not query.strip():
        return [], {}
    q_terms = content_terms(query)
    if not q_terms:
        return [], {}
    # document frequencies over chunks
    df: dict[str, int] = {}
    chunk_terms: list[dict[str, int]] = []
    for ch in chunks:
        counts: dict[str, int] = {}
        for t in set(content_terms(ch.content)):
            df[t] = df.get(t, 0) + 1
        for t in content_terms(ch.content):
            counts[t] = counts.get(t, 0) + 1
        chunk_terms.append(counts)
    scores: dict[str, float] = {}
    for ch, counts in zip(chunks, chunk_terms, strict=True):
        s = 0.0
        for t in q_terms:
            tf = float(counts.get(t, 0))
            if tf <= 0:
                continue
            idf = math.log((n + 1.0) / (df.get(t, 0) + 1.0)) + 1.0
            s += tf * idf
        if s > 0:
            scores[ch.chunk_id] = s
    ranked = sorted(scores, key=lambda cid: (-scores[cid], cid))
    return ranked, scores


def hash_embedding(text: str, dim: int = 128) -> list[float]:
    """Deterministic mock embedding: hash each token into dim buckets, L2-normalize."""
    vec = [0.0] * dim
    for tok in tokenize(text):
        h = hashlib.md5(tok.encode("utf-8")).hexdigest()
        idx = int(h, 16) % dim
        vec[idx] += 1.0
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity (inputs expected L2-normalized; safe for zero vectors)."""
    if len(a) != len(b) or not a:
        return 0.0
    denom_a = math.sqrt(sum(v * v for v in a))
    denom_b = math.sqrt(sum(v * v for v in b))
    if denom_a == 0 or denom_b == 0:
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=True)) / (denom_a * denom_b)


def vector_ranking(
    query: str, chunks: list[Chunk], dim: int = 128
) -> tuple[list[str], dict[str, float]]:
    """Rank chunks by cosine(query hash-embedding, chunk hash-embedding)."""
    if not chunks or not query.strip():
        return [], {}
    q = hash_embedding(query, dim)
    scores: dict[str, float] = {}
    for ch in chunks:
        c = hash_embedding(ch.content, dim)
        s = cosine(q, c)
        if s > 0:
            scores[ch.chunk_id] = s
    ranked = sorted(scores, key=lambda cid: (-scores[cid], cid))
    return ranked, scores


def rrf_fuse(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """Fuse ranked lists with Reciprocal Rank Fusion.

    RRF(d) = sum over lists of 1 / (k + rank(d)), ranks start at 1.
    Sorted by score desc, ties broken by doc id asc for determinism.
    Empty input (or all-empty lists) returns [].
    """
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))


def hybrid_search(
    query: str,
    chunks: list[Chunk],
    top_k: int = 5,
    rrf_k: int = 60,
    dim: int = 128,
    service: str | None = None,
) -> tuple[list[ScoredChunk], RetrievalDebug]:
    """Run keyword + vector rankings in-process, fuse with RRF, return top_k.

    A service filter (case-insensitive exact match) applies before ranking.
    """
    pool = chunks
    if service:
        pool = [c for c in chunks if c.service.lower() == service.lower()]
    kw_rank, _kw_scores = keyword_ranking(query, pool)
    vec_rank, _vec_scores = vector_ranking(query, pool, dim)
    fused = rrf_fuse([kw_rank, vec_rank], k=rrf_k)
    by_id = {c.chunk_id: c for c in pool}
    out: list[ScoredChunk] = []
    for rank, (cid, score) in enumerate(fused[:top_k], start=1):
        ch = by_id[cid]
        snippet = ch.content[:280].replace("\n", " ")
        out.append(
            ScoredChunk(
                chunk_id=cid,
                doc_id=ch.doc_id,
                title=ch.title,
                section=ch.section,
                service=ch.service,
                status=ch.status,
                score=score,
                rank=rank,
                snippet=snippet,
            )
        )
    # Also expose chunk ids that had zero score? No — debug shows ranked ids only.
    debug = RetrievalDebug(
        keyword_ranking=kw_rank[: max(top_k * 2, 10)],
        vector_ranking=vec_rank[: max(top_k * 2, 10)],
        fused_ranking=[cid for cid, _ in fused[:top_k]],
    )
    return out, debug
