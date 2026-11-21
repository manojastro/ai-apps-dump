from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.constants import DISCLAIMER

Confidence = Literal["high", "medium", "low"]
Verification = Literal["verified", "stale", "conflicting", "unverified"]
SourceTier = Literal[1, 2]


class SourcedValue(BaseModel):
    value: Any = None
    unit: str = ""
    source_url: str = ""
    source_tier: int = 1
    published_at: datetime | None = None
    fetched_at: datetime | None = None
    as_of: str = ""
    confidence: Confidence = "low"
    verification: Verification = "unverified"
    mock: bool = False
    notes: str = ""


class SourceRecord(BaseModel):
    source_id: str
    title: str
    url: str
    authority: str
    tier: int = 1
    published_at: datetime | None = None
    fetched_at: datetime | None = None
    as_of: str = ""
    verification: Verification = "unverified"
    confidence: Confidence = "medium"
    affected_facts: list[str] = Field(default_factory=list)
    mock: bool = False
    prohibited: bool = False
    injection_attempt: bool = False


class ApiMeta(BaseModel):
    disclaimer: str = DISCLAIMER
    educational_only: bool = True
    sebi_registered_adviser: bool = False
    executes_transactions: bool = False
    data_mode: str = "mock"
    degraded: bool = False
    rules_version: str = ""
    snapshot_id: str | None = None
