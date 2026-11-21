# File: rag/memory.py
"""Session-scoped, windowed conversational memory.

Implements the ``ConversationBufferWindowMemory(k=5)`` behaviour on the modern
``RunnableWithMessageHistory`` pattern: an in-process store keyed by
``session_id``, each session holding only the last ``max_turns`` user/assistant
exchanges. The :class:`BaseHistoryStore` interface is a drop-in seam for a Redis
backend (e.g. wrap ``RedisChatMessageHistory``) without touching chain code.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from threading import Lock
from typing import Dict, List

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)

DEFAULT_MEMORY_WINDOW_TURNS = 5
_MESSAGES_PER_TURN = 2


class WindowedChatMessageHistory(BaseChatMessageHistory):
    """Chat history that keeps only the most recent ``max_turns`` exchanges."""

    def __init__(self, session_id: str, max_turns: int = DEFAULT_MEMORY_WINDOW_TURNS) -> None:
        self.session_id = session_id
        self.max_turns = max(1, int(max_turns))
        self.messages: List[BaseMessage] = []

    def add_message(self, message: BaseMessage) -> None:
        """Append a message and trim history to the last ``max_turns * 2`` messages."""
        super().add_message(message)
        limit = self.max_turns * _MESSAGES_PER_TURN
        if len(self.messages) > limit:
            dropped = len(self.messages) - limit
            self.messages = self.messages[-limit:]
            logger.debug("history_trimmed session=%s dropped=%d kept=%d", self.session_id, dropped, limit)

    def clear(self) -> None:
        self.messages = []

    def as_list(self) -> List[BaseMessage]:
        return list(self.messages)


class BaseHistoryStore(ABC):
    """Storage seam — swap with a Redis/DB implementation in production."""

    @abstractmethod
    def get_history(self, session_id: str) -> BaseChatMessageHistory:
        ...

    @abstractmethod
    def delete_session(self, session_id: str) -> None:
        ...


class InMemoryHistoryStore(BaseHistoryStore):
    """Thread-safe in-memory history store keyed by session id."""

    def __init__(self, max_turns: int = DEFAULT_MEMORY_WINDOW_TURNS) -> None:
        self._max_turns = max_turns
        self._sessions: Dict[str, WindowedChatMessageHistory] = {}
        self._lock = Lock()

    def get_history(self, session_id: str) -> BaseChatMessageHistory:
        with self._lock:
            history = self._sessions.get(session_id)
            if history is None:
                history = WindowedChatMessageHistory(session_id=session_id, max_turns=self._max_turns)
                self._sessions[session_id] = history
            return history

    def delete_session(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)


_default_store: BaseHistoryStore = InMemoryHistoryStore()


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Factory suitable for ``RunnableWithMessageHistory(history_factory=...)``."""
    return _default_store.get_history(session_id)


def set_default_store(store: BaseHistoryStore) -> None:
    """Install a custom backend (e.g. Redis-backed) process-wide."""
    global _default_store
    _default_store = store


def reset_default_store() -> None:
    """Reset to a fresh in-memory store (used by tests)."""
    global _default_store
    _default_store = InMemoryHistoryStore()
