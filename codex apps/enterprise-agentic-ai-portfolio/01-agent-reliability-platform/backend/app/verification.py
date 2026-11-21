from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Protocol

from .schemas import AgentTrace, ExpectedOutcome, VerifiedOutcome


BACKUP_ARTIFACT_ID = "backup-2026-08-24.tar"
BACKUP_REQUIRED_STATE: dict[str, Any] = {
    "artifact_exists": True,
    "complete": True,
    "checksum_verified": True,
    "artifact_id": BACKUP_ARTIFACT_ID,
    "checksum": "sha256:synthetic",
    "size_bytes": 4096,
}


class ArtifactStateProvider(Protocol):
    """Read-only outcome boundary, separate from the observed agent trace."""

    def read(self, run_id: str, artifact_id: str) -> dict[str, Any] | None: ...


class SyntheticArtifactStateStore:
    def __init__(self) -> None:
        self._states: dict[tuple[str, str], dict[str, Any]] = {}

    def register(self, run_id: str, artifact_id: str, state: dict[str, Any]) -> None:
        self._states[(run_id, artifact_id)] = deepcopy(state)

    def snapshot(self, run_id: str, artifact_id: str) -> dict[str, Any] | None:
        state = self._states.get((run_id, artifact_id))
        return deepcopy(state) if state is not None else None


class SyntheticArtifactStateProvider:
    """Read-only view used by verification; the simulator owns the writable store."""

    def __init__(self, store: SyntheticArtifactStateStore):
        self.__store = store

    def read(self, run_id: str, artifact_id: str) -> dict[str, Any] | None:
        return self.__store.snapshot(run_id, artifact_id)


def server_expected_contract(observed_started_at: str, verification_deadline: str) -> ExpectedOutcome:
    return ExpectedOutcome(
        artifact_type="backup_archive",
        required=deepcopy(BACKUP_REQUIRED_STATE),
        deadline=verification_deadline,
    )


class OutcomeVerifier:
    """Verifies a server-owned contract against a separate read-only provider."""

    def __init__(self, provider: ArtifactStateProvider):
        self.provider = provider

    def verify(
        self, trace: AgentTrace, observed_started_at: str, verification_deadline: str
    ) -> VerifiedOutcome:
        expected = server_expected_contract(observed_started_at, verification_deadline)
        artifact_id = str(expected.required["artifact_id"])
        observed = self.provider.read(trace.run_id, artifact_id) or {}
        checks = {
            key: key in observed and observed[key] == required
            for key, required in expected.required.items()
        }
        checks["artifact_identity"] = observed.get("artifact_id") == artifact_id
        checks["checksum_identity"] = observed.get("checksum") == expected.required["checksum"]
        checks["size_valid"] = isinstance(observed.get("size_bytes"), int) and observed.get("size_bytes", 0) > 0
        checks["created_in_run_window"] = self._in_window(
            observed.get("created_at"), observed_started_at, expected.deadline
        )
        reasons = [name.replace("_", " ") for name, passed in checks.items() if not passed]
        return VerifiedOutcome(
            success=all(checks.values()), checks=checks, observed=observed, mismatch_reasons=reasons
        )

    @staticmethod
    def _in_window(created_at: str | None, started_at: str, deadline: str) -> bool:
        if not created_at:
            return False
        try:
            created = datetime.fromisoformat(created_at)
            return datetime.fromisoformat(started_at) <= created <= datetime.fromisoformat(deadline)
        except (TypeError, ValueError):
            return False
