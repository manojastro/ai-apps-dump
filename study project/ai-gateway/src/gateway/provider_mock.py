"""Mock provider layer. NO network calls — synthetic responses only."""

from __future__ import annotations


class MockProviderError(RuntimeError):
    pass


def mock_chat(model: str, messages: list[dict[str, str]]) -> tuple[str, int, int]:
    """Return (text, tokens_in_mock, tokens_out_mock).

    Fails when the model name starts with 'fail-' or any message contains
    a [FAIL:<model>] marker for the attempted model (used to demo fallback
    without network: only the named primary fails, the fallback succeeds).
    """
    joined = "\n".join(m.get("content", "") for m in messages)
    if model.startswith("fail-") or f"[FAIL:{model}]" in joined:
        raise MockProviderError(f"mock provider failure for model={model}")
    last_user = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"),
        "hello",
    )
    text = f"[mock:{model}] synthetic reply to: {last_user[:200]}"
    tokens_in = max(1, len(joined.split()))
    tokens_out = max(1, len(text.split()))
    return text, tokens_in, tokens_out
