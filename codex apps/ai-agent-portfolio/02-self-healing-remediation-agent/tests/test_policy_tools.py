import pytest

from app.repository import Repository
from app.settings import PROJECT_ROOT
from services.policy import PolicyEngine
from services.tools import MemorySandbox


@pytest.fixture
def policy(settings):
    repo = Repository(settings.database_url, PROJECT_ROOT / "migrations" / "001_initial.sql")
    repo.initialize()
    return PolicyEngine(settings.policy_path, repo)


def plan(**changes):
    value = {"action": "scale_deployment", "namespace": "selfheal-demo", "resource_kind": "deployments",
             "resource": "worker", "parameters": {"replicas": 3}, "recovery_criterion": "ready"}
    value.update(changes)
    return value


def test_scale_within_limit_is_low(policy):
    decision = policy.evaluate(plan())
    assert decision.allowed and decision.risk_tier.value == "LOW"


def test_scale_above_normal_requires_approval(policy):
    decision = policy.evaluate(plan(parameters={"replicas": 4}))
    assert decision.allowed and decision.risk_tier.value == "MEDIUM" and decision.approval_required


def test_scale_above_max_is_blocked(policy):
    decision = policy.evaluate(plan(parameters={"replicas": 6}))
    assert not decision.allowed and decision.risk_tier.value == "HIGH"


def test_namespace_escape_is_blocked(policy):
    assert not policy.evaluate(plan(namespace="default")).allowed


def test_arbitrary_action_is_high_and_blocked(policy):
    decision = policy.evaluate(plan(action="run_shell"))
    assert not decision.allowed and decision.risk_tier.value == "HIGH"


def test_sandbox_rejects_namespace_and_unknown_tool():
    sandbox = MemorySandbox()
    with pytest.raises(PermissionError):
        sandbox.execute(plan(namespace="production"))
    with pytest.raises(PermissionError):
        sandbox.execute(plan(action="run_shell"))
