"""Chat model interface. Model names come from configuration, never from code."""

from collections.abc import Sequence
from typing import Any, Literal, Protocol

from pydantic import Field

from invoiceflow.data.models import Frozen


class ToolCall(Frozen):
    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class Message(Frozen):
    role: Literal["system", "user", "assistant", "tool"]
    content: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    tool_call_id: str | None = None


class ToolSpec(Frozen):
    name: str
    description: str
    parameters: dict[str, Any]


class Usage(Frozen):
    input_tokens: int = 0
    output_tokens: int = 0


class LLMResponse(Frozen):
    content: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    usage: Usage = Usage()
    model: str = ""


class LLMError(RuntimeError):
    """Any model failure (timeout, refusal, malformed output). Routed to fail_safe."""


class ChatModel(Protocol):
    @property
    def name(self) -> str: ...

    def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec] = (),
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResponse: ...
