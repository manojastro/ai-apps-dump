import json
import sqlite3
from dataclasses import replace

import pytest

from backend.app.database import Repository
from backend.app.models import ApprovalRequest
from backend.app.simulator import SCENARIOS
from backend.app.workflow import RemediationWorkflow, WorkflowConflict


@pytest.fixture()
def workflow(tmp_path):
    repository = Repository(tmp_path / "workflow.db")
    repository.initialize()
    return RemediationWorkflow(repository, tmp_path / "workspaces")


def test_full_approval_gated_remediation_and_validation(workflow):
    incident = workflow.investigate("sql_injection")
    assert incident["status"] == "AWAITING_APPROVAL"
    assert incident["investigation"]["release_risk_before"]["decision"] == "BLOCK"
    assert incident["investigation"]["finding"]["evidence"][0]["evidence_id"]

    with pytest.raises(WorkflowConflict, match="requires explicit approval"):
        workflow.remediate_and_validate(
            incident["incident_id"], executed_by="executor-test", executor_role="executor"
        )

    approved = workflow.approve(
        incident["incident_id"],
        ApprovalRequest(approved=True, reason="Reviewed exact transformation"),
        approved_by="approver-test", approver_role="approver",
    )
    assert approved["status"] == "APPROVED"

    result = workflow.remediate_and_validate(
        incident["incident_id"], executed_by="executor-test", executor_role="executor"
    )
    validation = result["validation"]["result"]
    assert result["status"] == "VALIDATED"
    assert validation["passed"] is True
    assert validation["findings_before"] == 1
    assert validation["findings_after"] == 0
    assert all(validation["checks"].values())
    assert validation["release_risk_after"]["score"] == 10
    assert validation["release_risk_after"]["decision"] == "ALLOW_WITH_REVIEW"


def test_workspace_tamper_blocks_exact_patch(workflow):
    incident = workflow.investigate("command_injection")
    workflow.approve(
        incident["incident_id"],
        ApprovalRequest(approved=True, reason="Reviewed patch and rollback"),
        approved_by="approver-test", approver_role="approver",
    )
    workspace_file = workflow.workspace_root / incident["incident_id"] / SCENARIOS["command_injection"].filename
    workspace_file.write_text(workspace_file.read_text(encoding="utf-8") + "\n# tampered", encoding="utf-8")

    with pytest.raises(WorkflowConflict, match="changed after review"):
        workflow.remediate_and_validate(
            incident["incident_id"], executed_by="executor-test", executor_role="executor"
        )


def test_rejection_prevents_remediation(workflow):
    incident = workflow.investigate("hardcoded_secret")
    rejected = workflow.approve(
        incident["incident_id"],
        ApprovalRequest(approved=False, reason="Change window closed"),
        approved_by="security-reviewer", approver_role="approver",
    )
    assert rejected["status"] == "REJECTED"
    with pytest.raises(WorkflowConflict):
        workflow.remediate_and_validate(
            incident["incident_id"], executed_by="executor-test", executor_role="executor"
        )


def test_audit_log_cannot_be_updated_or_deleted(workflow):
    workflow.investigate("sql_injection")
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        with workflow.repository.connect() as connection:
            connection.execute("UPDATE audit_log SET decision='changed'")
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        with workflow.repository.connect() as connection:
            connection.execute("DELETE FROM audit_log")


def test_approval_attestation_is_immutable(workflow):
    incident = workflow.investigate("sql_injection")
    workflow.approve(
        incident["incident_id"], ApprovalRequest(approved=True, reason="Reviewed bound hashes"),
        approved_by="approver-test", approver_role="approver",
    )
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        with workflow.repository.connect() as connection:
            connection.execute("UPDATE approvals SET patch_sha256='changed'")


def test_same_identity_cannot_approve_and_execute(workflow):
    incident = workflow.investigate("sql_injection")
    workflow.approve(
        incident["incident_id"], ApprovalRequest(approved=True, reason="Reviewed hashes"),
        approved_by="same-principal", approver_role="approver",
    )
    with pytest.raises(WorkflowConflict, match="identities must be distinct"):
        workflow.remediate_and_validate(
            incident["incident_id"], executed_by="same-principal", executor_role="executor"
        )


def test_changed_fixed_source_after_approval_is_rejected(workflow):
    incident = workflow.investigate("sql_injection")
    workflow.approve(
        incident["incident_id"], ApprovalRequest(approved=True, reason="Reviewed original artifact"),
        approved_by="approver-test", approver_role="approver",
    )
    original = SCENARIOS["sql_injection"]
    SCENARIOS["sql_injection"] = replace(
        original,
        fixed_source=original.fixed_source + "\nfrom pathlib import Path\nPath('marker').write_text('unreviewed')\n",
    )
    try:
        with pytest.raises(WorkflowConflict, match="approved remediation artifact changed"):
            workflow.remediate_and_validate(
                incident["incident_id"], executed_by="executor-test", executor_role="executor"
            )
    finally:
        SCENARIOS["sql_injection"] = original


def test_prediction_is_independent_of_mutated_ground_truth_labels(tmp_path):
    original = SCENARIOS["sql_injection"]
    mutated = replace(
        original,
        ground_truth_finding=False,
        ground_truth_exploitability="UNLIKELY_EXPLOITABLE",
    )

    class MutatedLabelAdapter:
        def scenario(self, _: str):
            return mutated

    repository = Repository(tmp_path / "labels.db")
    repository.initialize()
    evaluated = RemediationWorkflow(
        repository, tmp_path / "label-workspaces", source_adapter=MutatedLabelAdapter()
    )
    incident = evaluated.investigate("sql_injection")
    summary = repository.evaluation_summary()

    assert incident["investigation"]["exploitability"]["classification"] == "LIKELY_EXPLOITABLE"
    assert summary["finding_validity"] == 0.0
    assert summary["exploitability_accuracy"] == 0.0


def test_persisted_patch_preview_mutation_is_rejected_before_approval(workflow):
    incident = workflow.investigate("sql_injection")
    with workflow.repository.connect() as connection:
        row = connection.execute(
            "SELECT investigation_json FROM incidents WHERE incident_id=?",
            (incident["incident_id"],),
        ).fetchone()
        investigation = json.loads(row["investigation_json"])
        investigation["remediation"]["patch_preview"] = "- harmless display\n+ no security change"
        connection.execute(
            "UPDATE incidents SET investigation_json=? WHERE incident_id=?",
            (json.dumps(investigation), incident["incident_id"]),
        )

    with pytest.raises(WorkflowConflict, match="artifact changed before approval"):
        workflow.approve(
            incident["incident_id"],
            ApprovalRequest(approved=True, reason="Misleading preview must fail"),
            approved_by="approver-test",
            approver_role="approver",
        )


def test_persisted_patch_preview_mutation_is_rejected_after_approval(workflow):
    incident = workflow.investigate("sql_injection")
    workflow.approve(
        incident["incident_id"],
        ApprovalRequest(approved=True, reason="Reviewed exact preview"),
        approved_by="approver-test",
        approver_role="approver",
    )
    with workflow.repository.connect() as connection:
        row = connection.execute(
            "SELECT investigation_json FROM incidents WHERE incident_id=?",
            (incident["incident_id"],),
        ).fetchone()
        investigation = json.loads(row["investigation_json"])
        investigation["remediation"]["patch_preview"] += "\n+ unreviewed display mutation"
        connection.execute(
            "UPDATE incidents SET investigation_json=? WHERE incident_id=?",
            (json.dumps(investigation), incident["incident_id"]),
        )

    with pytest.raises(WorkflowConflict, match="persisted patch preview"):
        workflow.remediate_and_validate(
            incident["incident_id"], executed_by="executor-test", executor_role="executor"
        )


def test_legacy_approval_migration_requires_new_bound_attestation(workflow):
    incident = workflow.investigate("sql_injection")
    workflow.approve(
        incident["incident_id"], ApprovalRequest(approved=True, reason="Legacy review"),
        approved_by="legacy-approver", approver_role="approver",
    )
    with workflow.repository.connect() as connection:
        connection.execute("DROP TRIGGER approvals_no_update")
        connection.execute("DROP TRIGGER approvals_no_delete")
        for column in ("approver_role", "action_id", "patch_sha256", "fixed_source_sha256"):
            connection.execute(f"ALTER TABLE approvals DROP COLUMN {column}")
        connection.execute(
            "DELETE FROM schema_migrations WHERE version IN "
            "('002_bound_approval','003_require_fresh_bound_reapproval')"
        )

    workflow.repository.initialize()
    migrated = workflow.repository.incident(incident["incident_id"])
    assert migrated["status"] == "REAPPROVAL_REQUIRED"
    with pytest.raises(WorkflowConflict, match="requires explicit approval"):
        workflow.remediate_and_validate(
            incident["incident_id"], executed_by="executor-test", executor_role="executor"
        )

    rebound = workflow.approve(
        incident["incident_id"], ApprovalRequest(approved=True, reason="Fresh exact review"),
        approved_by="new-approver", approver_role="approver",
    )
    assert rebound["status"] == "APPROVED"
    assert rebound["approval"]["patch_sha256"]
    assert workflow.remediate_and_validate(
        incident["incident_id"], executed_by="executor-test", executor_role="executor"
    )["status"] == "VALIDATED"


def test_failed_validation_rolls_back_workspace_and_persisted_source(workflow):
    incident = workflow.investigate("sql_injection")
    workflow.approve(
        incident["incident_id"], ApprovalRequest(approved=True, reason="Reviewed exact patch"),
        approved_by="approver-test", approver_role="approver",
    )
    real_validator = workflow.validator

    class FailingValidator:
        def validate(self, scenario, before, after):
            checks = real_validator.validate(scenario, before, after)
            checks["safe_construct_present"] = False
            return checks

    workflow.validator = FailingValidator()
    result = workflow.remediate_and_validate(
        incident["incident_id"], executed_by="executor-test", executor_role="executor"
    )
    workspace_file = workflow.workspace_root / incident["incident_id"] / SCENARIOS["sql_injection"].filename
    assert result["status"] == "VALIDATION_FAILED"
    assert result["source"]["after_sha256"] is None
    assert workspace_file.read_text(encoding="utf-8") == SCENARIOS["sql_injection"].vulnerable_source
    assert workflow.repository.activity(1)[0]["output"]["rolled_back"] is True


def test_validator_exception_rolls_back_and_records_truthful_attempt(workflow):
    incident = workflow.investigate("sql_injection")
    workflow.approve(
        incident["incident_id"], ApprovalRequest(approved=True, reason="Reviewed exact patch"),
        approved_by="approver-test", approver_role="approver",
    )

    class CrashedValidator:
        def validate(self, scenario, before, after):
            raise TimeoutError("synthetic validator outage")

    workflow.validator = CrashedValidator()
    result = workflow.remediate_and_validate(
        incident["incident_id"], executed_by="executor-test", executor_role="executor"
    )
    workspace_file = workflow.workspace_root / incident["incident_id"] / SCENARIOS["sql_injection"].filename
    summary = workflow.repository.evaluation_summary()
    assert result["status"] == "VALIDATION_FAILED"
    assert result["validation"]["result"]["checks"] == {"validator_available": False}
    assert result["source"]["after_sha256"] is None
    assert workspace_file.read_text(encoding="utf-8") == SCENARIOS["sql_injection"].vulnerable_source
    assert summary["attempted_remediations"] == 1
    assert summary["successful_remediations"] == 0
    assert summary["security_regressions"] == 0
    assert summary["test_regressions"] == 0
