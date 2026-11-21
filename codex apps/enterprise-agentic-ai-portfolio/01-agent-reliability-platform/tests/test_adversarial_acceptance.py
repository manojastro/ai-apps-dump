from __future__ import annotations

import json
import copy
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from backend.app.database import Database, canonical_payload
from backend.app.detectors import TraceDetector
from backend.app.evaluation import (
    DATASET_VERSION,
    TASK_FAILURE_CODES,
    VERSION_ARTIFACT_DIGESTS,
    Evaluator,
    SyntheticVersionBenchmarkRunner,
    case_evidence_digest,
    run_evidence_digest,
)
from backend.app.policy import SyntheticPolicyRegistry
from backend.app.schemas import ProposedAction, RiskLevel, utc_now
from backend.app.simulator import SyntheticBackupAgentAdapter
from backend.app.verification import BACKUP_ARTIFACT_ID, OutcomeVerifier
from backend.app.workflow import ReliabilityWorkflow


def make_database(tmp_path, name="acceptance.db") -> Database:
    database = Database(tmp_path / name)
    database.migrate()
    return database


def test_forged_trace_state_cannot_override_artifact_provider():
    adapter = SyntheticBackupAgentAdapter()
    assert not hasattr(adapter.artifact_provider, "register")
    trace = adapter.run("hallucinated_success", "review")
    forged = trace.model_copy(update={
        "external_state": {
            "artifact_exists": True, "complete": True, "checksum_verified": True,
            "artifact_id": BACKUP_ARTIFACT_ID, "checksum": "sha256:synthetic",
            "size_bytes": 4096, "created_at": trace.started_at,
        }
    })
    result = OutcomeVerifier(adapter.artifact_provider).verify(
        forged, trace.started_at, trace.expected_outcome.deadline
    )
    assert result.success is False
    assert result.observed["artifact_exists"] is False


def test_stale_provider_artifact_fails_freshness_window():
    adapter = SyntheticBackupAgentAdapter()
    trace = adapter.run("reliable", "review")
    state = adapter.artifact_provider.read(trace.run_id, BACKUP_ARTIFACT_ID)
    adapter.artifact_store.register(
        trace.run_id, BACKUP_ARTIFACT_ID, {**state, "created_at": "2000-01-01T00:00:00+00:00"}
    )
    result = OutcomeVerifier(adapter.artifact_provider).verify(
        trace, trace.started_at, trace.expected_outcome.deadline
    )
    assert result.success is False
    assert result.checks["created_in_run_window"] is False


def test_forged_trace_start_cannot_expand_server_owned_freshness_window():
    adapter = SyntheticBackupAgentAdapter()
    trace = adapter.run("reliable", "review")
    state = adapter.artifact_provider.read(trace.run_id, BACKUP_ARTIFACT_ID)
    old_start = datetime(2000, 1, 1, tzinfo=timezone.utc)
    adapter.artifact_store.register(
        trace.run_id, BACKUP_ARTIFACT_ID,
        {**state, "created_at": (old_start + timedelta(seconds=2)).isoformat()},
    )
    forged = trace.model_copy(update={"started_at": old_start.isoformat()})
    result = OutcomeVerifier(adapter.artifact_provider).verify(
        forged, trace.started_at, trace.expected_outcome.deadline
    )
    assert result.success is False
    assert result.checks["created_in_run_window"] is False


def test_missing_any_server_required_field_fails_closed():
    adapter = SyntheticBackupAgentAdapter()
    trace = adapter.run("reliable", "review")
    state = adapter.artifact_provider.read(trace.run_id, BACKUP_ARTIFACT_ID)
    state.pop("size_bytes")
    adapter.artifact_store.register(trace.run_id, BACKUP_ARTIFACT_ID, state)
    result = OutcomeVerifier(adapter.artifact_provider).verify(
        trace, trace.started_at, trace.expected_outcome.deadline
    )
    assert result.success is False
    assert result.checks["size_bytes"] is False
    assert result.checks["size_valid"] is False


def test_trace_supplied_expected_contract_cannot_weaken_server_contract():
    adapter = SyntheticBackupAgentAdapter()
    trace = adapter.run("hallucinated_success", "review")
    weakened = trace.expected_outcome.model_copy(update={
        "required": {"artifact_exists": False, "complete": False, "checksum_verified": False}
    })
    result = OutcomeVerifier(adapter.artifact_provider).verify(
        trace.model_copy(update={"expected_outcome": weakened}),
        trace.started_at, trace.expected_outcome.deadline,
    )
    assert result.success is False
    assert "artifact_identity" in result.checks


def test_approved_payload_is_database_immutable(tmp_path):
    database = make_database(tmp_path)
    workflow = ReliabilityWorkflow(database)
    action = workflow.run("hallucinated_success", "1.0.0").proposed_action
    workflow.approve(action.action_id, "reviewer", "APPROVED", "Original payload reviewed")
    payload = database.query_one("SELECT payload_json FROM actions WHERE action_id=?", (action.action_id,))
    changed = json.loads(payload["payload_json"])
    changed["action_type"] = "enforce_step_budget"
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        database.execute(
            "UPDATE actions SET payload_json=? WHERE action_id=?", (json.dumps(changed), action.action_id)
        )


def test_approved_attestation_row_is_append_only(tmp_path):
    database = make_database(tmp_path)
    workflow = ReliabilityWorkflow(database)
    action = workflow.run("hallucinated_success", "1.0.0").proposed_action
    approval = workflow.approve(action.action_id, "reviewer", "APPROVED", "Reviewed")
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        database.execute(
            "UPDATE approvals SET reason='rewritten' WHERE approval_id=?",
            (approval["approval_id"],),
        )
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        database.execute(
            "DELETE FROM approvals WHERE approval_id=?", (approval["approval_id"],)
        )


def test_wrong_allowed_payload_is_rejected_even_if_row_and_hash_are_tampered(tmp_path):
    database = make_database(tmp_path)
    workflow = ReliabilityWorkflow(database)
    action = workflow.run("hallucinated_success", "1.0.0").proposed_action
    row = database.query_one("SELECT payload_json FROM actions WHERE action_id=?", (action.action_id,))
    payload = json.loads(row["payload_json"])
    payload.update({
        "action_type": "enforce_step_budget", "allowed_tool": "runtime_policy",
        "risk": "LOW", "required_approval": False,
    })
    encoded, digest = canonical_payload(payload)
    database.execute(
        """UPDATE actions SET payload_json=?,payload_hash=?,action_type=?,risk=?,required_approval=?
           WHERE action_id=?""",
        (encoded, digest, "enforce_step_budget", "LOW", 0, action.action_id),
    )
    with pytest.raises(ValueError, match="incident action catalog"):
        workflow.approve(action.action_id, "reviewer", "APPROVED", "Tampered payload")


def test_policy_state_is_persisted_and_independently_observed(tmp_path):
    database = make_database(tmp_path)
    workflow = ReliabilityWorkflow(database)
    action = workflow.run("looping", "1.0.0").proposed_action
    result = workflow.execute(action.action_id)
    assert result["status"] == "EXECUTED"
    assert result["before"]["version"] == 0
    assert result["after"]["version"] == 1
    assert result["validation"]["passed"] is True
    state = database.query_one("SELECT * FROM policy_state WHERE policy_key='runtime.step_budget'")
    assert json.loads(state["value_json"]) == {"max_steps": 8}


def test_wrong_post_action_state_fails_validation_and_rolls_back(tmp_path):
    database = make_database(tmp_path)
    registry = SyntheticPolicyRegistry(database, fault_mode="wrong_state")
    workflow = ReliabilityWorkflow(database, policy_registry=registry)
    action = workflow.run("looping", "1.0.0").proposed_action
    result = workflow.execute(action.action_id)
    assert result["status"] == "ROLLED_BACK"
    assert result["validation"]["passed"] is False
    assert result["validation"]["checks"]["expected_policy_value"] is False
    assert registry.observe("runtime.step_budget")["version"] == 0
    execution = database.query_one("SELECT status FROM policy_executions WHERE action_id=?", (action.action_id,))
    assert execution["status"] == "ROLLED_BACK"


def test_apply_failure_after_write_is_observed_and_rolled_back(tmp_path):
    database = make_database(tmp_path)
    registry = SyntheticPolicyRegistry(database, fault_mode="raise_after_write")
    workflow = ReliabilityWorkflow(database, policy_registry=registry)
    action = workflow.run("looping", "1.0.0").proposed_action
    result = workflow.execute(action.action_id)
    assert result["status"] == "ROLLED_BACK"
    assert result["validation"]["passed"] is False
    assert result["validation"]["checks"]["apply_completed"] is False
    assert result["validation"]["checks"]["rollback_restored"] is True
    assert registry.observe("runtime.step_budget") == {
        "policy_key": "runtime.step_budget", "version": 0, "value": {}
    }


def test_lying_noop_rollback_fails_authoritative_readback(tmp_path):
    database = make_database(tmp_path)

    class LyingRollbackRegistry(SyntheticPolicyRegistry):
        def rollback(self, before):
            return dict(before)

    registry = LyingRollbackRegistry(database, fault_mode="wrong_state")
    workflow = ReliabilityWorkflow(database, policy_registry=registry)
    action = workflow.run("looping", "1.0.0").proposed_action
    result = workflow.execute(action.action_id)
    assert result["status"] == "ROLLBACK_FAILED"
    assert result["validation"]["checks"]["rollback_restored"] is False
    assert result["rollback"]["authoritative_observation"]["value"] == {"unexpected": True}
    assert database.query_one("SELECT status FROM actions WHERE action_id=?", (action.action_id,))["status"] == "ROLLBACK_FAILED"


def test_detector_benchmark_blocks_missing_loop_detector(tmp_path):
    database = make_database(tmp_path)
    base = TraceDetector()

    class NoLoopDetector:
        def detect(self, trace, verified):
            return [item for item in base.detect(trace, verified) if item.code != "AGENT_LOOP"]

    evaluator = Evaluator(database)
    evaluator.detector = NoLoopDetector()
    result = evaluator.run_detector_benchmark()
    assert result["passed"] is False
    assert result["metrics"]["loop_detection_accuracy"] == 0.0
    assert result["metrics"]["per_class_recall"]["AGENT_LOOP"] == 0.0
    assert result["metrics"]["critical_class_gate"] is False


def test_task_and_outcome_metrics_are_independently_derived():
    base = TraceDetector()

    class NoTaskFailureDetector:
        def detect(self, trace, verified):
            return [item for item in base.detect(trace, verified) if item.code not in TASK_FAILURE_CODES]

    metrics = SyntheticVersionBenchmarkRunner(NoTaskFailureDetector()).run("1.0.0")["metrics"]
    assert metrics["outcome_verification_accuracy"] == 1.0
    assert metrics["task_success_detection_accuracy"] < 1.0


class FailingRunner:
    def run(self, version, execution_spec):
        raise RuntimeError("candidate unavailable")


class IncompleteRunner:
    def run(self, version, execution_spec):
        return {"complete": False, "dataset_version": "synthetic-backup-v2", "metrics": {}}


@pytest.mark.parametrize("runner", [FailingRunner(), IncompleteRunner()])
def test_regression_gate_blocks_failed_or_incomplete_runner(tmp_path, runner):
    database = make_database(tmp_path)
    result = Evaluator(database, version_runner=runner).compare_versions("1.0.0", "1.1.0-safe")
    assert result["decision"] == "BLOCK"
    assert result["error"] == "UntrustedBenchmarkRunner"
    assert result["checks"]["trusted_runner"] is False
    assert result["checks"]["runner_complete"] is False


def test_regression_gate_never_calls_injected_runner(tmp_path):
    database = make_database(tmp_path)
    delegate = SyntheticVersionBenchmarkRunner()

    class CountingRunner:
        def __init__(self):
            self.versions = []

        def run(self, version, execution_spec):
            self.versions.append(version)
            return delegate.run(version, execution_spec)

    runner = CountingRunner()
    result = Evaluator(database, version_runner=runner).compare_versions("1.0.0", "1.1.0-safe")
    assert runner.versions == []
    assert result["decision"] == "BLOCK"
    assert result["error"] == "UntrustedBenchmarkRunner"
    assert result["dataset_version"] == "synthetic-backup-v2"


def test_externally_created_builtin_executor_is_not_server_registered(tmp_path):
    database = make_database(tmp_path)
    result = Evaluator(
        database, version_runner=SyntheticVersionBenchmarkRunner()
    ).compare_versions("1.0.0", "1.1.0-safe")
    assert result["decision"] == "BLOCK"
    assert result["checks"]["trusted_runner"] is False
    assert result["error"] == "UntrustedBenchmarkRunner"


def test_regression_gate_rejects_missing_named_scenario_even_with_perfect_metrics(tmp_path):
    database = make_database(tmp_path)
    delegate = SyntheticVersionBenchmarkRunner()

    class MissingScenarioRunner:
        def run(self, version, execution_spec):
            result = delegate.run(version, execution_spec)
            result["raw_cases"] = result["raw_cases"][:-1]
            result["metrics"] = {key: 1.0 for key in (
                "success_rate", "quality", "cost_per_task", "p95_latency_ms", "tool_accuracy", "safety"
            )}
            result["metrics"]["scenario_count"] = 9
            return result

    result = Evaluator(database, version_runner=MissingScenarioRunner()).compare_versions(
        "1.0.0", "1.1.0-safe"
    )
    assert result["decision"] == "BLOCK"
    assert result["error"] == "UntrustedBenchmarkRunner"
    assert result["checks"]["runner_complete"] is False


def test_regression_gate_derives_metrics_instead_of_trusting_summary(tmp_path):
    database = make_database(tmp_path)
    delegate = SyntheticVersionBenchmarkRunner()

    class ForgedSummaryRunner:
        def run(self, version, execution_spec):
            result = delegate.run(version, execution_spec)
            result["metrics"].update({
                "success_rate": 1.0, "quality": 1.0, "cost_per_task": 0.0,
                "p95_latency_ms": 0, "tool_accuracy": 1.0, "safety": 1.0,
            })
            return result

    blocked = Evaluator(database, version_runner=ForgedSummaryRunner()).compare_versions(
        "1.0.0", "1.1.0-regressed"
    )
    assert blocked["decision"] == "BLOCK"
    assert blocked["candidate_metrics"] == {}
    assert blocked["error"] == "UntrustedBenchmarkRunner"


def test_regression_gate_blocks_deep_relabelled_rehashed_baseline_replay(tmp_path):
    database = make_database(tmp_path)
    delegate = SyntheticVersionBenchmarkRunner()

    class DeepRelabelReplayRunner:
        def __init__(self):
            self.cached = None
            self.calls = []

        def run(self, version, execution_spec):
            self.calls.append(version)
            if self.cached is None:
                self.cached = delegate.run(version, execution_spec)
                return self.cached
            replay = copy.deepcopy(self.cached)
            replay["version"] = version
            replay["dataset_version"] = DATASET_VERSION
            replay["version_artifact_digest"] = VERSION_ARTIFACT_DIGESTS[version]
            replay["execution_nonce"] = execution_spec["execution_nonce"]
            requested = {item["case_id"]: item for item in execution_spec["cases"]}
            for item in replay["raw_cases"]:
                case = requested[item["case_id"]]
                item["run_id"] = case["run_id"]
                item["version_artifact_digest"] = VERSION_ARTIFACT_DIGESTS[version]
                item["observed_started_at"] = case["observed_started_at"]
                item["verification_deadline"] = case["verification_deadline"]
                item["trace"]["run_id"] = case["run_id"]
                item["trace"]["agent_version"] = version
                item["trace"]["started_at"] = case["observed_started_at"]
                item["trace"]["completed_at"] = (
                    datetime.fromisoformat(case["observed_started_at"]) + timedelta(seconds=2)
                ).isoformat()
                item["trace"]["expected_outcome"]["deadline"] = case["verification_deadline"]
                if item["artifact_state"].get("artifact_exists"):
                    item["artifact_state"]["created_at"] = (
                        datetime.fromisoformat(case["observed_started_at"]) + timedelta(seconds=1)
                    ).isoformat()
                unsigned = {key: value for key, value in item.items() if key != "evidence_digest"}
                item["evidence_digest"] = case_evidence_digest(
                    version, DATASET_VERSION, execution_spec["execution_nonce"], unsigned
                )
            replay["evidence_digest"] = run_evidence_digest(
                version, DATASET_VERSION, VERSION_ARTIFACT_DIGESTS[version],
                execution_spec["execution_nonce"], replay["raw_cases"],
            )
            return replay

    runner = DeepRelabelReplayRunner()
    result = Evaluator(database, version_runner=runner).compare_versions(
        "1.0.0", "1.1.0-regressed"
    )
    assert result["decision"] == "BLOCK"
    assert result["error"] == "UntrustedBenchmarkRunner"
    assert result["checks"]["trusted_runner"] is False
    assert result["checks"]["runner_complete"] is False
    assert runner.calls == []


def test_v1_approval_migrates_to_reapproval_and_can_be_freshly_bound(tmp_path):
    path = tmp_path / "legacy.db"
    connection = sqlite3.connect(path)
    migration = Path(__file__).parents[1] / "backend" / "app" / "migrations" / "001_initial.sql"
    try:
        connection.executescript(migration.read_text(encoding="utf-8"))
        connection.execute("INSERT INTO schema_migrations(version,applied_at) VALUES(1,?)", (utc_now(),))
        connection.execute(
            "INSERT INTO agent_runs(run_id,agent_id,agent_version,scenario,status,started_at,completed_at,total_cost_usd,latency_ms,trace_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            ("run_old", "backup-agent", "1.0.0", "hallucinated_success", "FAILED", utc_now(), utc_now(), 0.01, 1, "{}", utc_now()),
        )
        connection.execute(
            "INSERT INTO incidents(incident_id,run_id,severity,status,title,root_cause,confidence,detections_json,rca_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            ("inc_old", "run_old", "CRITICAL", "OPEN", "old", "old", 1.0, json.dumps([{"code": "HALLUCINATED_SUCCESS"}]), "{}", utc_now()),
        )
        action = ProposedAction(
            action_id="act_old", incident_id="inc_old", action_type="require_outcome_attestation",
            description="legacy action", risk=RiskLevel.MEDIUM, blast_radius="one agent",
            reversibility="reversible", expected_benefit="attestation", confidence=1.0,
            required_approval=True, rollback_plan="restore", allowed_tool="evaluation_policy",
        )
        payload, _ = canonical_payload(action)
        connection.execute(
            "INSERT INTO actions(action_id,incident_id,action_type,risk,required_approval,status,payload_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (action.action_id, action.incident_id, action.action_type, action.risk.value, 1, "APPROVED", payload, utc_now(), utc_now()),
        )
        connection.execute(
            "INSERT INTO approvals(approval_id,action_id,approver,decision,reason,created_at) VALUES(?,?,?,?,?,?)",
            ("apr_old", action.action_id, "legacy-reviewer", "APPROVED", "legacy", utc_now()),
        )
        connection.commit()
    finally:
        connection.close()

    database = Database(path)
    database.migrate()
    migrated_action = database.query_one("SELECT status,payload_hash FROM actions WHERE action_id='act_old'")
    legacy_approval = database.query_one("SELECT decision,payload_hash FROM approvals WHERE approval_id='apr_old'")
    assert migrated_action["status"] == "REAPPROVAL_REQUIRED"
    assert migrated_action["payload_hash"]
    assert legacy_approval == {"decision": "REAPPROVAL_REQUIRED", "payload_hash": ""}

    # The invalidated legacy attestation cannot be repaired in place to bypass
    # the fresh approval workflow, even when all binding columns are supplied.
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        database.execute(
            "UPDATE approvals SET decision='APPROVED',payload_version=1,payload_hash=? "
            "WHERE approval_id='apr_old'",
            (migrated_action["payload_hash"],),
        )
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        database.execute("DELETE FROM approvals WHERE approval_id='apr_old'")

    workflow = ReliabilityWorkflow(database)
    fresh = workflow.approve("act_old", "new-reviewer", "APPROVED", "Re-reviewed exact migrated payload")
    assert fresh["payload_hash"] == migrated_action["payload_hash"]
    approvals = database.query_all(
        "SELECT approval_id,decision,payload_hash FROM approvals WHERE action_id='act_old' ORDER BY rowid"
    )
    assert len(approvals) == 2
    assert approvals[0] == {
        "approval_id": "apr_old", "decision": "REAPPROVAL_REQUIRED", "payload_hash": "",
    }
    assert approvals[1]["decision"] == "APPROVED"
    assert approvals[1]["payload_hash"] == migrated_action["payload_hash"]
    assert workflow.execute("act_old")["status"] == "EXECUTED"
