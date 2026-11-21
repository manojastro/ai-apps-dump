from __future__ import annotations

import hashlib
import json
from pydantic import BaseModel, Field

from .fixtures import SCENARIOS, scenario_observations
from .models import Evidence, EvidenceSource, Incident
from .security import sanitize_untrusted


class TelemetryQuery(BaseModel):
    incident_id: str = Field(min_length=4, max_length=80)
    scenario: str = Field(min_length=3, max_length=80)
    service: str | None = Field(default=None, max_length=80)
    lookback_minutes: int = Field(default=60, ge=1, le=1440)
    variant: int = Field(default=0, ge=0, le=10_000)


def evidence_id(payload: dict[str, object]) -> str:
    canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return f"EV-{hashlib.sha256(canonical.encode()).hexdigest()[:12].upper()}"


class ReadOnlyTelemetryTool:
    """A typed allow-listed, read-only adapter. It exposes no query language or shell surface."""

    def __init__(self, source: EvidenceSource) -> None:
        self.source = source
        self.name = f"read_{source.value}"
        self.read_only = True

    async def query(self, request: TelemetryQuery) -> list[Evidence]:
        if request.scenario not in SCENARIOS:
            return []
        observations = scenario_observations(request.scenario, request.variant)[self.source.value]
        result: list[Evidence] = []
        for raw in observations:
            clean, redacted = sanitize_untrusted(raw["summary"])
            identity = {
                "incident_id": request.incident_id,
                "source": self.source.value,
                "source_ref": raw["source_ref"],
                "observed_at": raw["observed_at"].isoformat(),
                "service": raw["service"],
                "summary": clean,
            }
            result.append(
                Evidence(
                    id=evidence_id(identity),
                    incident_id=request.incident_id,
                    source=self.source,
                    source_ref=raw["source_ref"],
                    observed_at=raw["observed_at"],
                    service=raw["service"],
                    summary=clean,
                    attributes={
                        "relevant": raw["relevant"],
                        "signal": raw["signal"],
                        "root_category": raw["root_category"],
                        "root_component": raw["root_component"],
                        "lookback_minutes": request.lookback_minutes,
                    },
                    redacted=redacted,
                )
            )
        return result


TOOLS = {
    EvidenceSource.metrics: ReadOnlyTelemetryTool(EvidenceSource.metrics),
    EvidenceSource.logs: ReadOnlyTelemetryTool(EvidenceSource.logs),
    EvidenceSource.changes: ReadOnlyTelemetryTool(EvidenceSource.changes),
    EvidenceSource.tickets: ReadOnlyTelemetryTool(EvidenceSource.tickets),
}


def tool_for(source: EvidenceSource) -> ReadOnlyTelemetryTool:
    return TOOLS[source]


def query_for(incident: Incident, variant: int = 0) -> TelemetryQuery:
    return TelemetryQuery(
        incident_id=incident.id,
        scenario=incident.scenario,
        service=incident.service,
        variant=variant,
    )
