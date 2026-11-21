from typing import Any, Protocol

from app.models.domain import Candidate, Evidence, Incident, KnowledgeDocument, ReplayResult
from simulator.pipeline import Fixture


class PipelineAdapter(Protocol):
    async def fixture(self, incident: Incident) -> Fixture: ...
    async def investigate(self, incident: Incident, branch: str) -> Evidence: ...
    async def replay(self, fixture: Fixture, candidate: Candidate) -> ReplayResult: ...


class DatabaseAdapter(Protocol):
    async def read_snapshot(self, incident: Incident) -> dict[str, Any]: ...


class ObservabilityAdapter(Protocol):
    async def read_health(self, incident: Incident) -> dict[str, Any]: ...


class SourceControlAdapter(Protocol):
    async def read_changes(self, incident: Incident) -> dict[str, Any]: ...
    def artifact(self, incident: Incident, candidate: Candidate) -> dict[str, Any]: ...


class SandboxAdapter(Protocol):
    async def apply(self, fixture: Fixture, candidate: Candidate) -> Candidate: ...


class KnowledgeAdapter(Protocol):
    async def retrieve(
        self, query: str, pipeline_id: str, environment: str
    ) -> list[KnowledgeDocument]: ...
