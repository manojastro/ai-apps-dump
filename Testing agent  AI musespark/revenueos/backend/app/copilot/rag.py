"""Retrieval over ticket text and activity summaries with pgvector.

Embedder choice: Anthropic does not offer an embeddings endpoint, and the project rules
avoid paid calls beyond the LLM key. So this uses a local, stateless hashing vectoriser.
It matches on words, not meaning, which is a real limitation. `Embedder` is the seam for
swapping in a semantic model later: only `encode` changes, plus a re-index.
"""
from __future__ import annotations

from typing import Protocol

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sqlalchemy import insert, select, text
from sqlalchemy.orm import Session

from app.copilot.guardrails import neutralise
from app.db.models import EMBEDDING_DIM, Account, Activity, Deal, Embedding, Ticket
from app.services.scope import Scope


class Embedder(Protocol):
    def encode(self, texts: list[str]) -> np.ndarray: ...


class HashingEmbedder:
    def __init__(self) -> None:
        self._vectorizer = HashingVectorizer(
            n_features=EMBEDDING_DIM, ngram_range=(1, 2), norm="l2", alternate_sign=True,
            stop_words="english",
        )

    def encode(self, texts: list[str]) -> np.ndarray:
        return self._vectorizer.transform(texts).toarray().astype(np.float32)


def get_embedder() -> Embedder:
    return HashingEmbedder()


def build_index(session: Session, embedder: Embedder | None = None) -> int:
    """Rebuild the index from source tables. Safe to re-run."""
    embedder = embedder or get_embedder()
    tickets = session.execute(select(Ticket.id, Ticket.account_id, Ticket.subject,
                                     Ticket.body_text)).all()
    activities = session.execute(
        select(Activity.id, Deal.account_id, Activity.summary_text)
        .join(Deal, Activity.deal_id == Deal.id).where(Activity.summary_text.is_not(None))
    ).all()
    records = [("tickets", i, a, f"{s}. {b or ''}") for i, a, s, b in tickets]
    records += [("activities", i, a, t) for i, a, t in activities]
    session.execute(text("TRUNCATE embeddings RESTART IDENTITY"))
    for start in range(0, len(records), 1000):
        chunk = records[start:start + 1000]
        vectors = embedder.encode([r[3] for r in chunk])
        session.execute(insert(Embedding), [
            {"source_table": table, "source_id": sid, "account_id": account, "text": body,
             "vector": vector.tolist()}
            for (table, sid, account, body), vector in zip(chunk, vectors, strict=True)
        ])
    session.commit()
    return len(records)


def search(
    session: Session,
    scope: Scope,
    query: str,
    account_id: int | None = None,
    limit: int = 8,
    embedder: Embedder | None = None,
) -> list[dict]:
    embedder = embedder or get_embedder()
    vector = embedder.encode([query])[0]
    if not np.any(vector):
        return []
    distance = Embedding.vector.cosine_distance(vector.tolist())
    filters = [scope.accounts()]
    if account_id is not None:
        filters.append(Embedding.account_id == account_id)
    rows = session.execute(
        select(Embedding, Account.name, distance.label("distance"))
        .join(Account, Embedding.account_id == Account.id)
        .where(*filters).order_by(distance).limit(limit)
    ).all()
    return [{
        "source": embedding.source_table,
        "source_id": embedding.source_id,
        "account_id": embedding.account_id,
        "account_name": account_name,
        "similarity": round(1 - float(dist), 3),
        "text": neutralise(embedding.text),
        "cite": f"{embedding.source_table}#{embedding.source_id}",
    } for embedding, account_name, dist in rows]
