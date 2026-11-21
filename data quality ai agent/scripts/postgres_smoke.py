"""Run in the backend container or with PostgreSQL DATABASE_URL/CHECKPOINT_URL configured."""
import asyncio
from uuid import uuid4

from langgraph.types import Command

from app.config import Settings
from app.db.repository import Repository
from app.graph.persistence import checkpoint_store
from app.graph.workflow import build_graph, initial_state
from app.models.domain import Incident, Scenario
from app.rag.retrieval import HybridKnowledge


async def main():
    config = Settings()
    assert config.database_url.startswith("postgresql"), "This test requires PostgreSQL"
    repo = Repository(config)
    repo.migrate()
    knowledge = HybridKnowledge(repo, config)
    await knowledge.seed()
    docs = await knowledge.retrieve("currency amount cents ledger", "orders_daily", "local")
    assert docs and docs[0].id == "RULE-002"
    case = Incident(id=str(uuid4()), scenario=Scenario.DEPENDENCY)
    repo.create(case)
    thread = {"configurable": {"thread_id": case.id}}
    async with checkpoint_store(config) as saver:
        paused = await build_graph(saver, knowledge=knowledge).ainvoke(initial_state(case), thread)
        assert paused["__interrupt__"]
        repo.project(paused)
    async with checkpoint_store(config) as saver:
        graph = build_graph(saver, knowledge=knowledge)
        snapshot = await graph.aget_state(thread)
        assert snapshot.next == ("human_approval",)
        final = await graph.ainvoke(Command(resume={"actor": "postgres-smoke",
            "comment": "Verified restored checkpoint and vector retrieval", "approved": True}), thread)
        assert final["final_status"] == "COMPLETED"
        repo.project(final)
    assert len(repo.related(case.id, "validations")) == 10
    await knowledge.close()
    repo.close()
    print("PASS: Postgres migration, pgvector retrieval, checkpoint restart and HITL resume")


if __name__ == "__main__":
    asyncio.run(main())
