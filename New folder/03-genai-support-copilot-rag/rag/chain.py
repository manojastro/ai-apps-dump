# File: rag/chain.py
"""The support copilot chain.

Flow per turn:

1. History-aware rephrasing -> "standalone question" (skipped on first turn).
2. MMR retrieval over the vector store.
3. Hard refusal short-circuit when nothing is retrieved (LLM never called).
4. Strict stuff-documents prompt -> ChatOpenAI(gpt-4o-mini, temperature=0)
   -> StrOutputParser.
5. Persist user + assistant turns to windowed session memory.

``SupportCopilotChain.answer`` returns the answer plus cited sources;
``stream_events`` streams answer tokens; ``as_runnable`` exposes the same
components as a canonical LCEL ``RunnableWithMessageHistory`` graph.

When ``OPENAI_API_KEY`` is missing, :func:`build_llm` falls back to a scripted
fake chat model so the app boots and tests run fully offline.
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Iterator, List, Optional

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import MessagesPlaceholder  # noqa: F401 - re-exported for convenience
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import (
    Runnable,
    RunnableBranch,
    RunnableLambda,
    RunnablePassthrough,
    RunnableWithMessageHistory,
)

from rag.memory import DEFAULT_MEMORY_WINDOW_TURNS, BaseHistoryStore, InMemoryHistoryStore
from rag.prompts import CONDENSE_QUESTION_PROMPT, QA_PROMPT, REFUSAL_MESSAGE
from rag.retriever import extract_sources, format_context

load_dotenv()
logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o-mini"

FAKE_LLM_RESPONSE = (
    "A full refund can be requested within 30 days of purchase and is issued to "
    "the original payment method within 5-10 business days after approval. "
    "[source: sample_refund_policy.md]"
)


@dataclass
class CopilotAnswer:
    """Non-streaming chain output."""

    answer: str
    sources: List[str] = field(default_factory=list)
    session_id: str = ""


@dataclass
class StreamEvent:
    """Streaming chunk: token events followed by one terminal ``done`` event."""

    type: str  # "token" | "done"
    content: str = ""
    sources: List[str] = field(default_factory=list)
    session_id: str = ""


def build_llm(model: Optional[str] = None, temperature: float = 0.0) -> BaseLanguageModel:
    """Return ``ChatOpenAI`` when configured, else an offline fake chat model."""
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY missing - using offline mock LLM")
        return FakeListChatModel(responses=[FAKE_LLM_RESPONSE])
    from langchain_openai import ChatOpenAI

    resolved_model = model or os.getenv("OPENAI_MODEL") or DEFAULT_MODEL
    return ChatOpenAI(model=resolved_model, temperature=temperature, max_retries=2)


class SupportCopilotChain:
    """Composable RAG chain with memory, citations, refusal guard and streaming."""

    def __init__(
        self,
        llm: BaseLanguageModel,
        retriever: BaseRetriever,
        history_store: Optional[BaseHistoryStore] = None,
        memory_window_turns: int = DEFAULT_MEMORY_WINDOW_TURNS,
    ) -> None:
        self.llm = llm
        self.retriever = retriever
        self.history_store = history_store or InMemoryHistoryStore(max_turns=memory_window_turns)
        self._condense_chain = CONDENSE_QUESTION_PROMPT | llm | StrOutputParser()
        self._generate_chain = QA_PROMPT | llm | StrOutputParser()

    # ------------------------------------------------------------------ steps

    def _standalone_question(self, question: str, chat_history: list) -> str:
        question = question.strip()
        if not chat_history:
            return question
        try:
            rewritten = self._condense_chain.invoke(
                {"question": question, "chat_history": chat_history}
            ).strip()
            return rewritten or question
        except Exception as exc:  # noqa: BLE001 - rewriting must never break answering
            logger.warning("condense_failed falling back to raw question error=%s", exc)
            return question

    def _safe_retrieve(self, query: str) -> List[Document]:
        try:
            return list(self.retriever.invoke(query))
        except Exception as exc:  # noqa: BLE001 - degraded answers beat crashed requests
            logger.error("retrieval_failed returning zero documents error=%s", exc)
            return []

    def _generate(self, question: str, context: str, chat_history: list) -> str:
        response = self._generate_chain.invoke(
            {"question": question.strip(), "context": context, "chat_history": chat_history}
        )
        return response.strip()

    # --------------------------------------------------------------- public

    def answer(self, message: str, session_id: str) -> CopilotAnswer:
        """Full non-streaming turn: retrieve -> generate/refuse -> persist memory."""
        started = time.perf_counter()
        history = self.history_store.get_history(session_id)
        prior_turns = history.as_list()

        standalone = self._standalone_question(message, prior_turns)
        documents = self._safe_retrieve(standalone)

        if documents:
            answer_text = self._generate(message, format_context(documents), prior_turns)
        else:
            answer_text = REFUSAL_MESSAGE

        history.add_message(HumanMessage(content=message))
        history.add_message(AIMessage(content=answer_text))

        result = CopilotAnswer(
            answer=answer_text,
            sources=extract_sources(documents),
            session_id=session_id,
        )
        logger.info(
            "chat_answered session=%s docs=%d duration_ms=%d",
            session_id,
            len(documents),
            int((time.perf_counter() - started) * 1000),
        )
        return result

    def stream_events(self, message: str, session_id: str) -> Iterator[StreamEvent]:
        """Stream answer tokens; terminal event carries sources + full answer."""
        started = time.perf_counter()
        history = self.history_store.get_history(session_id)
        prior_turns = history.as_list()

        standalone = self._standalone_question(message, prior_turns)
        documents = self._safe_retrieve(standalone)
        sources = extract_sources(documents)

        parts: List[str] = []
        if documents:
            token_stream = self._generate_chain.stream(
                {"question": message.strip(), "context": format_context(documents), "chat_history": prior_turns}
            )
        else:
            token_stream = iter([REFUSAL_MESSAGE])

        for token in token_stream:
            text = str(token)
            parts.append(text)
            yield StreamEvent(type="token", content=text, session_id=session_id)

        full_answer = "".join(parts).strip()
        history.add_message(HumanMessage(content=message))
        history.add_message(AIMessage(content=full_answer))

        logger.info(
            "chat_streamed session=%s docs=%d duration_ms=%d",
            session_id,
            len(documents),
            int((time.perf_counter() - started) * 1000),
        )
        yield StreamEvent(type="done", content=full_answer, sources=sources, session_id=session_id)

    # ------------------------------------------------------------ LCEL view

    def as_runnable(self) -> Runnable:
        """Canonical LCEL composition wrapped by ``RunnableWithMessageHistory``.

        Invoke with::

            chain.as_runnable().invoke(
                {"question": "..."},
                config={"configurable": {"session_id": "sess-1"}},
            )

        Returns ``{answer, sources, standalone_question, ...}``. Memory is read
        and written automatically via the configurable session id. Streaming of
        the final string degrades to a single chunk because of the output dict;
        use :meth:`stream_events` for true token streaming.
        """
        rewrite_or_pass = RunnableBranch(
            (lambda x: bool(x.get("chat_history")), self._condense_chain),
            lambda x: x["question"],
        )
        generate_or_refuse = RunnableBranch(
            (lambda x: bool(x.get("docs")), self._generate_chain),
            lambda x: REFUSAL_MESSAGE,
        )
        graph = (
            RunnablePassthrough.assign(standalone_question=rewrite_or_pass)
            .assign(docs=lambda x: self._safe_retrieve(x["standalone_question"]))
            .assign(context=lambda x: format_context(list(x["docs"])))
            .assign(answer=generate_or_refuse)
            .assign(sources=lambda x: extract_sources(list(x["docs"])))
            | RunnableLambda(lambda x: {"answer": x["answer"], "sources": x["sources"]})
        )
        return RunnableWithMessageHistory(
            graph,
            lambda session_id: self.history_store.get_history(session_id),
            input_messages_key="question",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )
