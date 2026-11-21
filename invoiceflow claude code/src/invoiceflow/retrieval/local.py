"""Local hybrid retriever: BM25 + a hashing embedder, fused with reciprocal rank fusion.

`HashingEmbedder` is a deterministic stand-in for a real embedding model (feature hashing
of words and word pairs). It keeps CI offline and reproducible; it is not semantic. On
Databricks the AI Search index uses a real embedding endpoint instead.

Access filtering happens before scoring: a chunk the caller may not see is never ranked.
"""

import hashlib
import math
import re
from collections import Counter
from collections.abc import Sequence
from itertools import pairwise

from invoiceflow.retrieval.models import AccessScope, Chunk, DocType, Hit, RetrievalResult

_TOKEN = re.compile(r"[a-z0-9]+")
STOPWORDS = frozenset(
    [
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "can",
        "do",
        "does",
        "for",
        "from",
        "has",
        "have",
        "how",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "may",
        "must",
        "no",
        "not",
        "of",
        "on",
        "or",
        "our",
        "than",
        "that",
        "the",
        "their",
        "then",
        "there",
        "this",
        "to",
        "was",
        "we",
        "what",
        "when",
        "which",
        "who",
        "whose",
        "will",
        "with",
        "you",
    ]
)
RRF_K = 60


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in STOPWORDS]


class HashingEmbedder:
    def __init__(self, dim: int = 512) -> None:
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        tokens = tokenize(text)
        features = tokens + [f"{a}_{b}" for a, b in pairwise(tokens)]
        vector = [0.0] * self.dim
        for feature in features:
            digest = hashlib.sha1(feature.encode("utf-8"), usedforsecurity=False).digest()
            index = int.from_bytes(digest[:4], "little") % self.dim
            vector[index] += 1.0 if digest[4] % 2 == 0 else -1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


class _BM25:
    def __init__(self, docs: Sequence[list[str]], k1: float = 1.5, b: float = 0.75) -> None:
        self.k1, self.b = k1, b
        self.docs = [Counter(d) for d in docs]
        self.lengths = [len(d) for d in docs]
        self.avg = (sum(self.lengths) / len(docs)) if docs else 0.0
        df: Counter[str] = Counter()
        for d in docs:
            df.update(set(d))
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def score(self, query: list[str], i: int) -> float:
        doc, length = self.docs[i], self.lengths[i]
        total = 0.0
        for term in query:
            tf = doc.get(term, 0)
            if tf:
                denom = tf + self.k1 * (1 - self.b + self.b * length / (self.avg or 1))
                total += self.idf.get(term, 0.0) * tf * (self.k1 + 1) / denom
        return total


class LocalHybridRetriever:
    def __init__(
        self,
        chunks: Sequence[Chunk],
        embedder: HashingEmbedder | None = None,
        min_bm25: float = 2.0,
        min_coverage: float = 0.5,
    ) -> None:
        self.chunks = list(chunks)
        self.embedder = embedder or HashingEmbedder()
        self.min_bm25 = min_bm25
        self.min_coverage = min_coverage
        self._terms = [set(tokenize(c.text)) for c in self.chunks]
        self._bm25 = _BM25([tokenize(c.text) for c in self.chunks])
        self._vectors = [self.embedder.embed(c.text) for c in self.chunks]

    def search(
        self,
        query: str,
        scope: AccessScope,
        k: int = 5,
        doc_types: Sequence[DocType] | None = None,
    ) -> RetrievalResult:
        allowed = [
            i
            for i, c in enumerate(self.chunks)
            if scope.allows(c) and (doc_types is None or c.doc_type in doc_types)
        ]
        if not allowed:
            return RetrievalResult(
                query=query, hits=(), abstained=True, reason="no documents in your access scope"
            )
        terms = tokenize(query)
        qvec = self.embedder.embed(query)
        lexical = {i: self._bm25.score(terms, i) for i in allowed}
        dense = {
            i: sum(a * b for a, b in zip(qvec, self._vectors[i], strict=True)) for i in allowed
        }
        best = max(allowed, key=lambda i: lexical[i])
        query_terms = set(terms)
        coverage = len(query_terms & self._terms[best]) / len(query_terms) if query_terms else 0.0
        # Abstain unless the best section matches strongly AND contains at least half of the
        # question's content words: one shared common word ("approved") is not evidence.
        if lexical[best] < self.min_bm25 or coverage < self.min_coverage:
            return RetrievalResult(
                query=query,
                hits=(),
                abstained=True,
                reason="insufficient evidence: no section matches the question",
            )
        lex_rank = {i: r for r, i in enumerate(sorted(allowed, key=lambda i: -lexical[i]))}
        dense_rank = {i: r for r, i in enumerate(sorted(allowed, key=lambda i: -dense[i]))}
        fused = {
            i: 1 / (RRF_K + lex_rank[i] + 1) + 1 / (RRF_K + dense_rank[i] + 1)
            for i in allowed
            if lexical[i] > 0
        }
        ranked = sorted(fused, key=lambda i: (-fused[i], self.chunks[i].chunk_id))[:k]
        return RetrievalResult(
            query=query, hits=tuple(Hit(chunk=self.chunks[i], score=fused[i]) for i in ranked)
        )
