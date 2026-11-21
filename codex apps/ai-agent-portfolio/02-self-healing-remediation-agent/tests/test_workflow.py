from app.catalog import get_scenario
from app.repository import Repository
from app.settings import PROJECT_ROOT
from services.agent import RemediationWorkflow
from services.agent.model import DeterministicDiagnosticModel
from services.policy import PolicyEngine
from services.tools import MemorySandbox


def engine(settings):
    repo = Repository(settings.database_url, PROJECT_ROOT / "migrations" / "001_initial.sql")
    repo.initialize()
    sandbox = MemorySandbox()
    return repo, sandbox, RemediationWorkflow(repo, PolicyEngine(settings.policy_path, repo), sandbox, DeterministicDiagnosticModel())


def create(repo, workflow, scenario, fail=False):
    incident = repo.create_incident(get_scenario(scenario).model_dump(mode="json"), fail)
    return incident["id"], workflow.run(incident["id"])


def test_low_risk_auto_executes_with_evidence(settings):
    repo, _, workflow = engine(settings)
    incident_id, state = create(repo, workflow, "crashloop")
    assert state["status"] == "RESOLVED"
    assert state["verification"]["healthy"] is True
    assert state["hypotheses"][0]["evidence_refs"]
    assert state["trace"] == [node for node in workflow.NODE_ORDER if node not in {"approval_checkpoint", "rollback"}]
    assert repo.count("executions") == 1


def test_medium_risk_persists_approval_and_resumes(settings):
    repo, _, workflow = engine(settings)
    incident_id, state = create(repo, workflow, "bad_deployment")
    assert state["status"] == "PENDING_APPROVAL"
    repo.record_approval(incident_id, "APPROVED", "operator", "change reviewed")
    state = workflow.run(incident_id)
    assert state["status"] == "RESOLVED"
    assert repo.approval(incident_id)["comment"] == "change reviewed"


def test_rejected_approval_never_executes(settings):
    repo, _, workflow = engine(settings)
    incident_id, state = create(repo, workflow, "bad_deployment")
    repo.record_approval(incident_id, "REJECTED", "operator", "too risky")
    state = workflow.run(incident_id)
    assert state["status"] == "REJECTED"
    assert repo.count("executions") == 0


def test_high_risk_action_is_blocked(settings):
    repo, _, workflow = engine(settings)
    _, state = create(repo, workflow, "unsafe_no_remediation")
    assert state["status"] == "BLOCKED"
    assert state["policy"]["risk_tier"] == "HIGH"
    assert repo.count("executions") == 0


def test_failed_verification_rolls_back_original_state(settings):
    repo, sandbox, workflow = engine(settings)
    _, state = create(repo, workflow, "excessive_latency", fail=True)
    assert state["status"] == "ROLLED_BACK"
    assert state["rollback"]["status"] == "SUCCEEDED"
    assert repo.count("rollback_records") == 1
    assert sandbox.snapshot(state["plan"])["cache_entries"] == 100


def test_terminal_rerun_has_no_duplicate_side_effect(settings):
    repo, sandbox, workflow = engine(settings)
    incident_id, state = create(repo, workflow, "failing_job")
    workflow.run(incident_id)
    assert repo.count("executions") == 1
    assert sandbox.side_effect_count["jobs/reconcile"] == 1

