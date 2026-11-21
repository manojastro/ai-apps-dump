from contextlib import asynccontextmanager

import aiosqlite
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.config import Settings


@asynccontextmanager
async def checkpoint_store(settings: Settings):
    # Explicit reconstruction allowlist; pickle deserialization is never enabled.
    domain = "app.models.domain"
    serde = JsonPlusSerializer(
        allowed_msgpack_modules=[
            (domain, name)
            for name in (
                "Incident",
                "Evidence",
                "Hypothesis",
                "Candidate",
                "Attempt",
                "ValidationResult",
                "Verification",
                "ReplayResult",
                "KnowledgeDocument",
                "Scenario",
                "Status",
                "Risk",
                "Operation",
            )
        ]
        + [("simulator.pipeline", "Fixture")]
    )
    if settings.checkpoint_url.startswith("postgresql://"):
        async with AsyncPostgresSaver.from_conn_string(
            settings.checkpoint_url, serde=serde
        ) as saver:
            await saver.setup()
            yield saver
    else:
        async with aiosqlite.connect(settings.checkpoint_url) as connection:
            sqlite_saver = AsyncSqliteSaver(connection, serde=serde)
            await sqlite_saver.setup()
            yield sqlite_saver
