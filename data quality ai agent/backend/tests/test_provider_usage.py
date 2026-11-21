from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.config import Settings
from app.llm.online import StructuredProvider
from app.models.domain import Candidate


def response(parsed, input_tokens, output_tokens):
    return SimpleNamespace(
        usage=SimpleNamespace(prompt_tokens=input_tokens, completion_tokens=output_tokens),
        choices=[SimpleNamespace(message=SimpleNamespace(refusal=None, parsed=parsed))],
    )


async def test_correction_retry_counts_usage_from_both_responses():
    parse = AsyncMock(
        side_effect=[
            response(None, 100, 10),
            response(Candidate(summary="Corrected proposal"), 200, 20),
        ]
    )
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(parse=parse)))
    provider = StructuredProvider(
        Settings(
            llm_input_cost_per_million=1,
            llm_output_cost_per_million=2,
        ),
        client=client,
    )
    result = await provider._request(Candidate, "Propose recovery", {})
    assert result.summary == "Corrected proposal"
    assert provider.last_usage["llm_calls"] == 2
    assert provider.last_usage["input_tokens"] == 300
    assert provider.last_usage["output_tokens"] == 30
    assert provider.last_usage["estimated_cost_usd"] == pytest.approx(0.00036)
