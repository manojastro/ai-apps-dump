import pytest
from app.config import Settings
from app.db.repository import Repository
from app.models.domain import Candidate, Operation, Risk
from app.rag.retrieval import HybridKnowledge
from app.security.policy import Role, authorize, risk_for


async def test_metadata_filter_excludes_other_environments_and_unknown_pipelines(tmp_path):
    repo = Repository(Settings(database_url=f"sqlite:///{tmp_path / 'rag.db'}"))
    repo.migrate()
    knowledge = HybridKnowledge(repo, repo.settings)
    await knowledge.seed()
    results = await knowledge.retrieve("amount cents conversion ledger", "orders_daily", "local")
    assert results[0].id == "RULE-002"
    assert all(r.environment == "local" for r in results)
    assert await knowledge.retrieve("amount", "unknown_pipeline", "local") == []
    assert await knowledge.retrieve("amount", "orders_daily", "production") == []
    repo.close()


def test_read_only_investigator_cannot_invoke_a_mutation():
    with pytest.raises(PermissionError):
        authorize(Role.INVESTIGATOR, "sandbox_apply")
    with pytest.raises(PermissionError):
        authorize(Role.INVESTIGATOR, "execute_sql")


@pytest.mark.parametrize(
    "operation,risk",
    [
        (Operation.MAP_CUSTOMER, Risk.LOW),
        (Operation.CONFIGURATION, Risk.MEDIUM),
        (Operation.SCHEMA, Risk.HIGH),
        (Operation.DELETE, Risk.CRITICAL),
        (Operation.REWRITE, Risk.CRITICAL),
    ],
)
def test_risk_cannot_be_downgraded_by_model(operation, risk):
    assert risk_for(Candidate(summary="This is totally safe", operations=[operation])) == risk
