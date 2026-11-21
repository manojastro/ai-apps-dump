"""Runtime settings, read from environment at call time (so tests can override)."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    db_url: str
    llm_mode: str
    model: str
    approval_ttl_hours: float
    queue_lease_seconds: float
    backoff_base_seconds: float
    max_attempts: int
    agent_max_steps: int
    session_secret: str


def get_settings() -> Settings:
    e = os.environ.get
    return Settings(
        db_url=e("EIR_DB_URL", "sqlite:///data/eir.db"),
        llm_mode=e("EIR_LLM_MODE", "MOCK").upper(),
        model=e("EIR_MODEL", "claude-sonnet-5-5"),
        approval_ttl_hours=float(e("EIR_APPROVAL_TTL_HOURS", "48")),
        queue_lease_seconds=float(e("EIR_QUEUE_LEASE_SECONDS", "60")),
        backoff_base_seconds=float(e("EIR_BACKOFF_BASE_SECONDS", "2")),
        max_attempts=int(e("EIR_MAX_ATTEMPTS", "5")),
        agent_max_steps=int(e("EIR_AGENT_MAX_STEPS", "8")),
        session_secret=e("EIR_SESSION_SECRET", "change-me-demo-only"),
    )
