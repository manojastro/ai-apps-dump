"""Pydantic v2 request/response shapes (OpenAI-compatible subset)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = "user"
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "general-default"
    messages: list[ChatMessage] = Field(min_length=1)
    temperature: float = 0.0
    max_tokens: int | None = None
    stream: bool = False
    response_format: dict[str, Any] | None = None


class TenantCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    monthly_budget_usd: float = Field(default=10.0, gt=0)
    rpm: int = Field(default=60, gt=0)
    tpm: int = Field(default=20000, gt=0)
    allowed_models: list[str] = Field(default_factory=list)
    guardrail_profile: Literal["standard", "strict"] = "standard"
