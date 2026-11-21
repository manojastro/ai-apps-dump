"""Versioned agent boundaries. Telemetry content never grants permissions."""

import hashlib
import json
import time
import uuid
from typing import Literal

from pydantic import BaseModel, Field


def action_hash(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class Budget(BaseModel):
    tool_limit: int = Field(default=12, ge=0, le=50)
    tool_calls: int = 0
    model_limit: int = 8
    model_calls: int = 0
    token_limit: int = 24000
    tokens: int = 0
    runtime_limit: int = 120
    started: float = Field(default_factory=time.time)

    def reserve_tool(self):
        if self.tool_calls >= self.tool_limit or time.time() - self.started > self.runtime_limit:
            raise ValueError("Investigation budget exceeded")
        self.tool_calls += 1

    def reserve_model(self):
        if self.model_calls >= self.model_limit or self.tokens >= self.token_limit:
            raise ValueError("Model budget exceeded")
        if time.time() - self.started > self.runtime_limit:
            raise ValueError("Runtime budget exceeded")
        self.model_calls += 1


class Evidence(BaseModel):
    id: str
    run_id: str
    source_type: str
    source_record_id: str
    observed_at: float
    collected_at: float
    service: str = "checkout"
    environment: str = "demo"
    query: dict = Field(default_factory=dict)
    payload: dict
    summary: str
    content_hash: str
    stale: bool = False
    truncated: bool = False

    @classmethod
    def make(cls, run_id: str, source: str, payload: dict, summary: str, **kwargs):
        now = time.time()
        return cls(
            id=str(uuid.uuid4()),
            run_id=run_id,
            source_type=source,
            source_record_id=kwargs.pop("source_record_id", f"fixture-v1/{source}"),
            observed_at=kwargs.pop("observed_at", now),
            collected_at=now,
            payload=payload,
            summary=summary,
            content_hash=action_hash(payload),
            **kwargs,
        )


class Diagnosis(BaseModel):
    category: Literal[
        "payment_delay", "config_regression", "pool_exhaustion", "cpu_saturation", "healthy", "inconclusive"
    ]
    confidence: Literal["supported", "tentative", "inconclusive"]
    explanation: str = Field(max_length=4000)
    evidence_ids: list[str]
    missing: list[str]
    alternatives: list[str] = Field(default_factory=list)

    def validate_evidence(self, evidence: list[Evidence], run_id: str):
        available = {
            e.id for e in evidence if e.run_id == run_id and action_hash(e.payload) == e.content_hash
        }
        if not set(self.evidence_ids).issubset(available):
            raise ValueError("Evidence scope or integrity violation")
        usable = [e for e in evidence if e.id in self.evidence_ids and not e.stale and not e.truncated]
        if self.confidence == "supported" and len({e.source_type for e in usable}) < 2:
            raise ValueError("Supported findings require independent current evidence")


def verify_recovery(before: dict, after: dict) -> dict:
    verified = (
        after.get("samples", 0) >= 30
        and after.get("error_rate", 1) <= min(0.02, before.get("error_rate", 0) / 2)
        and after.get("p95_ms", 99999) < before.get("p95_ms", 0) * 0.7
    )
    return {
        "verified": verified,
        "before": before,
        "after": after,
        "reason": "Latency and errors improved with sufficient samples"
        if verified
        else "Recovery not verified: insufficient samples or improvement",
    }
