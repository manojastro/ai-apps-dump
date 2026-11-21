"""OpenAI-compatible chat completions: Databricks model serving endpoints and Azure OpenAI.

Databricks serving endpoints accept the OpenAI chat format; the client comes from
`WorkspaceClient().serving_endpoints.get_open_ai_client()`. Tool calls use function
calling; the final proposal uses `response_format` with a JSON schema. Whether a given
endpoint honours both must be checked per model (ADR 0001 open item).
"""

import json
from collections.abc import Sequence
from typing import Any

from invoiceflow.ports.llm import LLMError, LLMResponse, Message, ToolCall, ToolSpec, Usage


def _to_openai(message: Message) -> dict[str, Any]:
    out: dict[str, Any] = {"role": message.role, "content": message.content}
    if message.tool_calls:
        out["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.name, "arguments": json.dumps(call.arguments)},
            }
            for call in message.tool_calls
        ]
    if message.tool_call_id:
        out["tool_call_id"] = message.tool_call_id
    return out


class OpenAICompatibleChatModel:
    def __init__(self, client: Any, model: str, provider: str, temperature: float = 0.0) -> None:
        self._client = client
        self._model = model
        self._provider = provider
        self._temperature = temperature

    @property
    def name(self) -> str:
        return f"{self._provider}:{self._model}"

    def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec] = (),
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": [_to_openai(m) for m in messages],
            "temperature": self._temperature,
        }
        if tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]
        if json_schema is not None:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "resolution_proposal", "schema": json_schema},
            }
        try:
            response = self._client.chat.completions.create(**kwargs)
        except Exception as exc:  # network, auth, rate limit, bad request
            raise LLMError(f"{self.name}: {type(exc).__name__}: {exc}") from exc
        if not response.choices:
            raise LLMError(f"{self.name}: empty response")
        message = response.choices[0].message
        calls = []
        for call in message.tool_calls or []:
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError as exc:
                raise LLMError(f"{self.name}: tool arguments are not JSON") from exc
            calls.append(ToolCall(id=call.id, name=call.function.name, arguments=arguments))
        usage = response.usage
        return LLMResponse(
            content=message.content or "",
            tool_calls=tuple(calls),
            usage=Usage(
                input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                output_tokens=getattr(usage, "completion_tokens", 0) or 0,
            ),
            model=self.name,
        )
