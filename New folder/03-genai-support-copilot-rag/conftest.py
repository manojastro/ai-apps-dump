# File: conftest.py
"""Shared pytest fixtures. Puts the repo root on sys.path and provides a fully
offline RAG stack: deterministic hash embeddings + in-memory vectorstore + fake LLM."""
from __future__ import annotations

import hashlib
import math
import re
import sys
from pathlib import Path

import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.fake import FakeListLLM
from langchain_core.vectorstores import InMemoryVectorStore

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rag.chain import SupportCopilotChain  # noqa: E402
from rag.memory import InMemoryHistoryStore, reset_default_store  # noqa: E402
from rag.retriever import RetrieverConfig, build_retriever  # noqa: E402

DIM = 128

GROUNDED_ANSWER = (
    "A full refund can be requested within 30 days of purchase and is issued to "
    "the original payment method within 5-10 business days after approval. "
    "[source: sample_refund_policy.md]"
)

KB_DOCUMENTS = [
    Document(
        page_content=(
            "Refund window: customers can request a full refund within 30 days of purchase. "
            "Approved refunds are issued to the original payment method within 5-10 business days."
        ),
        metadata={"source": "sample_refund_policy.md", "section": "Refund window"},
    ),
    Document(
        page_content=(
            "Password reset: open the login page, click Forgot password, enter your account email "
            "and follow the emailed link. Reset links expire after 60 minutes."
        ),
        metadata={"source": "sample_kb_article.md", "section": "Resetting a forgotten password"},
    ),
]


class HashEmbeddings(Embeddings):
    """Deterministic offline embeddings: hashed bag-of-words, L2-normalised."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * DIM
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            digest = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            vector[digest % DIM] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


@pytest.fixture(autouse=True)
def _reset_default_memory():
    reset_default_store()
    yield
    reset_default_store()


@pytest.fixture(scope="session")
def vectorstore() -> InMemoryVectorStore:
    store = InMemoryVectorStore(embedding=HashEmbeddings())
    store.add_documents(KB_DOCUMENTS)
    return store


@pytest.fixture()
def llm() -> FakeListLLM:
    return FakeListLLM(responses=[GROUNDED_ANSWER])


@pytest.fixture()
def chain(vectorstore: InMemoryVectorStore, llm: FakeListLLM) -> SupportCopilotChain:
    retriever = build_retriever(vectorstore, RetrieverConfig(k=2, fetch_k=4))
    return SupportCopilotChain(llm=llm, retriever=retriever, history_store=InMemoryHistoryStore(max_turns=5))
