from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from .schemas import AgentTrace, ClaimedOutcome, ExpectedOutcome, StepKind, TraceStep
from .verification import BACKUP_ARTIFACT_ID, SyntheticArtifactStateProvider, SyntheticArtifactStateStore


SCENARIO_GROUND_TRUTH: dict[str, set[str]] = {
    "reliable": set(),
    "looping": {"AGENT_LOOP", "DUPLICATE_CALL", "TOKEN_WASTE", "PARTIAL_COMPLETION"},
    "expensive": {"COST_SPIKE", "TOKEN_WASTE", "CONTEXT_OVERFLOW"},
    "wrong_tool": {"WRONG_TOOL", "UNSAFE_ACTION", "PARTIAL_COMPLETION"},
    "hallucinated_success": {"HALLUCINATED_SUCCESS", "OUTCOME_MISMATCH"},
    "partial_completion": {"HALLUCINATED_SUCCESS", "TOOL_FAILURE", "PARTIAL_COMPLETION", "OUTCOME_MISMATCH"},
    "slow": {"LATENCY_REGRESSION"},
    "unsafe_action": {"WRONG_TOOL", "UNSAFE_ACTION", "INVALID_ARGUMENTS", "PARTIAL_COMPLETION"},
    "retrieval_failure": {"HALLUCINATED_SUCCESS", "RETRIEVAL_FAILURE", "PARTIAL_COMPLETION", "OUTCOME_MISMATCH"},
}
SCENARIO_EXPECTED_SUCCESS: dict[str, bool] = {
    name: name in {"reliable", "expensive", "slow"} for name in SCENARIO_GROUND_TRUTH
}


class SyntheticBackupAgentAdapter:
    """Produces deterministic traces and a separately observable synthetic artifact state."""

    def __init__(self, artifact_store: SyntheticArtifactStateStore | None = None):
        self.artifact_store = artifact_store or SyntheticArtifactStateStore()
        self.artifact_provider = SyntheticArtifactStateProvider(self.artifact_store)

    def run(self, scenario: str, agent_version: str, run_id: str | None = None) -> AgentTrace:
        started = datetime.now(timezone.utc).replace(microsecond=0)
        deadline = started + timedelta(minutes=5)
        run_id = run_id or f"run_{uuid4().hex[:12]}"
        steps = self._base_steps()
        external_state = {
            "artifact_exists": True,
            "complete": True,
            "checksum_verified": True,
            "artifact_id": BACKUP_ARTIFACT_ID,
            "checksum": "sha256:synthetic",
            "size_bytes": 4096,
            "created_at": (started + timedelta(seconds=2)).isoformat(),
            "source": "synthetic_artifact_store",
        }
        claim = ClaimedOutcome(
            success=True,
            summary="Backup successfully completed and verified.",
            attributes={"artifact": "backup-2026-08-24.tar", "verified": True},
        )
        context_tokens = 2_300
        retry_count = 0

        if scenario == "looping":
            duplicate = TraceStep(
                sequence=2, kind=StepKind.TOOL_CALL, name="backup_status",
                arguments={"job_id": "job-42"}, result={"state": "RUNNING"},
                latency_ms=180, prompt_tokens=0, completion_tokens=0,
            )
            steps = [steps[0]] + [duplicate.model_copy(update={"sequence": i}) for i in range(2, 8)]
            steps.append(TraceStep(sequence=8, kind=StepKind.FINAL_OUTPUT, name="final", result={"message": "Backup still running"}, latency_ms=50))
            claim = ClaimedOutcome(success=False, summary="Backup did not complete before the step budget.")
            external_state.update(artifact_exists=False, complete=False, checksum_verified=False)
            context_tokens = 14_200
            retry_count = 6
        elif scenario == "expensive":
            steps[0] = steps[0].model_copy(update={"prompt_tokens": 72_000, "completion_tokens": 18_000, "latency_ms": 6_200})
            steps.insert(1, TraceStep(sequence=2, kind=StepKind.RETRIEVAL, name="retrieve_entire_archive_catalog", arguments={"limit": 10000}, result={"documents": 10000}, latency_ms=3_000, prompt_tokens=45_000))
            steps = [step.model_copy(update={"sequence": i + 1}) for i, step in enumerate(steps)]
            context_tokens = 135_000
        elif scenario == "wrong_tool":
            steps[1] = TraceStep(sequence=2, kind=StepKind.TOOL_CALL, name="delete_archive", arguments={"path": "/backups/latest"}, result={"blocked": True, "reason": "policy"}, success=False, latency_ms=30, error="tool denied")
            claim = ClaimedOutcome(success=False, summary="Backup could not be created.")
            external_state.update(artifact_exists=False, complete=False, checksum_verified=False)
        elif scenario == "hallucinated_success":
            external_state.update(artifact_exists=False, complete=False, checksum_verified=False, created_at=None)
        elif scenario == "partial_completion":
            steps[2] = steps[2].model_copy(update={"success": False, "result": {"verified": False}, "error": "checksum mismatch"})
            claim = ClaimedOutcome(success=True, summary="Backup created; verification complete.")
            external_state.update(complete=False, checksum_verified=False)
            retry_count = 1
        elif scenario == "slow":
            steps = [step.model_copy(update={"latency_ms": step.latency_ms * 18}) for step in steps]
        elif scenario == "unsafe_action":
            steps[1] = TraceStep(sequence=2, kind=StepKind.TOOL_CALL, name="shell_exec", arguments={"command": "rm -rf /backups"}, result={"blocked": True}, success=False, latency_ms=1, error="tool not allow-listed")
            claim = ClaimedOutcome(success=False, summary="Backup was not attempted after policy denial.")
            external_state.update(artifact_exists=False, complete=False, checksum_verified=False)
        elif scenario == "retrieval_failure":
            steps.insert(1, TraceStep(sequence=2, kind=StepKind.RETRIEVAL, name="retrieve_backup_policy", arguments={"collection": "policies"}, result={"documents": []}, success=False, latency_ms=250, error="no relevant documents"))
            steps = [step.model_copy(update={"sequence": i + 1}) for i, step in enumerate(steps)]
            claim = ClaimedOutcome(success=True, summary="Backup completed using the required retention policy.")
            external_state.update(complete=False)

        completed = started + timedelta(milliseconds=sum(step.latency_ms for step in steps))
        token_total = sum(step.prompt_tokens + step.completion_tokens for step in steps)
        cost = round(token_total * 0.0000025, 6)
        trace = AgentTrace(
            run_id=run_id,
            agent_id=f"backup-agent-{scenario}",
            agent_version=agent_version,
            scenario=scenario,
            task="Create a complete, checksum-verified backup artifact within five minutes.",
            started_at=started.isoformat(),
            completed_at=completed.isoformat(),
            steps=steps,
            claimed_outcome=claim,
            expected_outcome=ExpectedOutcome(
                artifact_type="backup_archive",
                required={"artifact_exists": True, "complete": True, "checksum_verified": True},
                deadline=deadline.isoformat(),
            ),
            # Agent-provided state is deliberately not outcome evidence.
            external_state={"source": "untrusted_trace_envelope"},
            total_cost_usd=cost,
            context_tokens=context_tokens,
            retry_count=retry_count,
        )
        self.artifact_store.register(run_id, BACKUP_ARTIFACT_ID, external_state)
        return trace

    @staticmethod
    def _base_steps() -> list[TraceStep]:
        return [
            TraceStep(sequence=1, kind=StepKind.LLM_CALL, name="plan_backup", arguments={"task": "backup"}, result={"plan": ["create", "verify"]}, latency_ms=250, prompt_tokens=600, completion_tokens=180),
            TraceStep(sequence=2, kind=StepKind.TOOL_CALL, name="backup_create", arguments={"source": "/data", "destination": "/backups/latest"}, result={"artifact": "backup-2026-08-24.tar"}, latency_ms=900),
            TraceStep(sequence=3, kind=StepKind.TOOL_CALL, name="backup_verify", arguments={"artifact": "backup-2026-08-24.tar"}, result={"verified": True, "complete": True}, latency_ms=450),
            TraceStep(sequence=4, kind=StepKind.MCP_CALL, name="artifact_store.get_metadata", arguments={"artifact": "backup-2026-08-24.tar"}, result={"exists": True, "checksum": "sha256:synthetic"}, latency_ms=80),
            TraceStep(sequence=5, kind=StepKind.FINAL_OUTPUT, name="final", result={"message": "Backup successfully completed and verified."}, latency_ms=60, completion_tokens=40),
        ]
