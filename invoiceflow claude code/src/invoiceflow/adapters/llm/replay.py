"""Record live model responses once, replay them in CI. A request whose hash was never
recorded raises LLMError, which the agent routes to fail_safe: replay never guesses."""

import gzip
import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from invoiceflow.ports.llm import ChatModel, LLMError, LLMResponse, Message, ToolSpec


def request_key(
    messages: Sequence[Message], tools: Sequence[ToolSpec], json_schema: dict[str, Any] | None
) -> str:
    payload = {
        "messages": [m.model_dump(mode="json") for m in messages],
        "tools": [t.model_dump(mode="json") for t in tools],
        "schema": json_schema,
    }
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class RecordingChatModel:
    def __init__(self, inner: ChatModel, path: Path) -> None:
        self._inner = inner
        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return self._inner.name

    def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec] = (),
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        response = self._inner.complete(messages, tools, json_schema)
        record = {
            "request_sha256": request_key(messages, tools, json_schema),
            "response": response.model_dump(mode="json"),
        }
        with self._path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return response


class ReplayChatModel:
    def __init__(self, path: Path, name: str = "replay") -> None:
        self._name = name
        self._responses: dict[str, LLMResponse] = {}
        if path.exists():
            raw = path.read_bytes()
            if path.suffix == ".gz":  # large recordings are stored gzip-compressed
                raw = gzip.decompress(raw)
            for line in raw.decode("utf-8").splitlines():
                record = json.loads(line)
                self._responses[record["request_sha256"]] = LLMResponse.model_validate(
                    record["response"]
                )

    @property
    def name(self) -> str:
        return self._name

    def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec] = (),
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        key = request_key(messages, tools, json_schema)
        if key not in self._responses:
            raise LLMError(f"no recorded response for request {key[:12]}")
        return self._responses[key]
