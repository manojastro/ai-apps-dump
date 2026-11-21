# File: tests/test_chain.py
"""Offline tests for the RAG chain: FakeListLLM + InMemoryVectorStore.

No network, no API keys, no model downloads — verifies grounded answers,
deterministic refusal on empty context, memory windowing and streaming.
"""
from __future__ import annotations

import pytest
from langchain_core.language_models.fake import FakeListLLM
from langchain_core.vectorstores import InMemoryVectorStore

from conftest import GROUNDED_ANSWER
from rag.chain import SupportCopilotChain
from rag.memory import InMemoryHistoryStore
from rag.prompts import REFUSAL_MESSAGE
from rag.retriever import NullRetriever, RetrieverConfig, build_retriever


def test_grounded_answer_cites_sources(chain: SupportCopilotChain) -> None:
    result = chain.answer("What is your refund policy?", session_id="t-grounded")

    assert "[source: sample_refund_policy.md]" in result.answer
    assert result.sources == ["sample_refund_policy.md"]
    assert result.session_id == "t-grounded"
    history = chain.history_store.get_history("t-grounded")
    assert len(history.messages) == 2


def test_refusal_on_empty_context(llm: FakeListLLM) -> None:
    copilot = SupportCopilotChain(
        llm=llm,
        retriever=NullRetriever(),
        history_store=InMemoryHistoryStore(max_turns=5),
    )

    result = copilot.answer("Who won the 1998 football world cup?", session_id="t-refusal")

    assert result.answer == REFUSAL_MESSAGE
    assert result.sources == []
    assert llm.i == 0, "refusal must short-circuit without calling the LLM"


def test_memory_window_trims_old_turns(llm: FakeListLLM, vectorstore: InMemoryVectorStore) -> None:
    retriever = build_retriever(vectorstore, RetrieverConfig(k=2, fetch_k=4))
    copilot = SupportCopilotChain(
        llm=llm,
        retriever=retriever,
        history_store=InMemoryHistoryStore(max_turns=2),
    )

    for turn in range(3):
        copilot.answer(f"question number {turn}", session_id="t-window")

    messages = copilot.history_store.get_history("t-window").messages
    assert len(messages) == 4  # last 2 turns only (k * 2)
    assert "question number 0" not in messages[0].content


def test_stream_emits_tokens_then_done_event(chain: SupportCopilotChain) -> None:
    events = list(chain.stream_events("How long do refunds take?", session_id="t-stream"))

    assert events[0].type == "token"
    assert events[-1].type == "done"
    assert events[-1].sources == ["sample_refund_policy.md"]
    streamed_text = "".join(event.content for event in events if event.type == "token")
    assert streamed_text.strip() == GROUNDED_ANSWER


@pytest.mark.parametrize(
    "session_a,session_b",
    [("t-iso-a", "t-iso-b")],
)
def test_sessions_are_isolated(llm: FakeListLLM, vectorstore: InMemoryVectorStore, session_a: str, session_b: str) -> None:
    retriever = build_retriever(vectorstore, RetrieverConfig(k=2, fetch_k=4))
    copilot = SupportCopilotChain(llm=llm, retriever=retriever, history_store=InMemoryHistoryStore())

    copilot.answer("first question", session_id=session_a)

    assert len(copilot.history_store.get_history(session_a).messages) == 2
    assert len(copilot.history_store.get_history(session_b).messages) == 0
