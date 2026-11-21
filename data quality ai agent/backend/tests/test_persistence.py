from uuid import uuid4

from app.config import Settings
from app.db.repository import Repository
from app.graph.persistence import checkpoint_store
from app.graph.workflow import build_graph, initial_state
from app.models.domain import Incident, Scenario
from langgraph.types import Command


async def test_checkpoint_and_approval_survive_new_connection(tmp_path):
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'app.db'}", checkpoint_url=str(tmp_path / "graph.db")
    )
    repository = Repository(settings)
    repository.migrate()
    case = Incident(id=str(uuid4()), scenario=Scenario.DEPENDENCY)
    repository.create(case)
    config = {"configurable": {"thread_id": case.id}}
    async with checkpoint_store(settings) as saver:
        graph = build_graph(saver)
        paused = await graph.ainvoke(initial_state(case), config)
        repository.project(paused)
        assert paused["__interrupt__"]
    async with checkpoint_store(settings) as saver:
        restored_graph = build_graph(saver)
        snapshot = await restored_graph.aget_state(config)
        assert snapshot.next == ("human_approval",)
        final = await restored_graph.ainvoke(
            Command(
                resume={
                    "actor": "operator",
                    "comment": "Approved after process restart",
                    "approved": True,
                }
            ),
            config,
        )
        repository.project(final)
        assert final["final_status"] == "COMPLETED"
    assert repository.get(case.id)["attempt_count"] == 1
    assert len(repository.related(case.id, "validations")) == 10
    assert repository.related(case.id, "approvals")[0]["approved"] is True
    repository.close()
