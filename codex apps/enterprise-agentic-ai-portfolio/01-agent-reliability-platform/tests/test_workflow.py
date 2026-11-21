import sqlite3

import pytest

from backend.app.database import Database
from backend.app.workflow import ReliabilityWorkflow


@pytest.fixture
def database(tmp_path):
    db = Database(tmp_path / "test.db")
    db.migrate()
    return db


def test_workflow_persists_trace_evidence_rca_action_and_validation(database):
    result = ReliabilityWorkflow(database).run("hallucinated_success", "1.0.0")
    assert result.incident_id
    assert result.rca.probable_root_cause == "Hallucinated success"
    assert result.proposed_action.required_approval is True
    assert result.validation.passed is False
    assert database.query_one("SELECT COUNT(*) count FROM agent_runs")["count"] == 1
    window = database.query_one(
        "SELECT observed_started_at,verification_deadline FROM agent_runs WHERE run_id=?",
        (result.run_id,),
    )
    assert window["observed_started_at"]
    assert window["verification_deadline"] > window["observed_started_at"]
    assert database.query_one("SELECT COUNT(*) count FROM evidence")["count"] >= 2
    assert database.query_one("SELECT COUNT(*) count FROM audit_events")["count"] == 2


def test_approval_is_required_before_medium_risk_execution(database):
    workflow = ReliabilityWorkflow(database)
    action = workflow.run("hallucinated_success", "1.0.0").proposed_action
    with pytest.raises(PermissionError):
        workflow.execute(action.action_id)
    approval = workflow.approve(action.action_id, "reviewer@example.test", "APPROVED", "Evidence supports policy change")
    assert approval["decision"] == "APPROVED"
    execution = workflow.execute(action.action_id)
    assert execution["status"] == "EXECUTED"
    assert execution["mode"] == "safe-simulation"


def test_low_risk_action_can_execute_without_approval(database):
    workflow = ReliabilityWorkflow(database)
    action = workflow.run("looping", "1.0.0").proposed_action
    assert action.required_approval is False
    assert workflow.execute(action.action_id)["validation"]["passed"] is True


def test_audit_log_is_immutable(database):
    ReliabilityWorkflow(database).run("reliable", "1.0.0")
    with pytest.raises(sqlite3.IntegrityError):
        database.execute("UPDATE audit_events SET action = 'tampered'")
