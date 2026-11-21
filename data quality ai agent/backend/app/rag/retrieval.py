import asyncio
import hashlib
import math
import re

from openai import AsyncOpenAI
from pgvector.sqlalchemy import Vector
from sqlalchemy import cast, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import EMBEDDING_DIMENSIONS, ChunkRow, KnowledgeRow
from app.db.repository import Repository, record
from app.models.domain import KnowledgeDocument
from app.rag.local import DOCUMENTS


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def local_embedding(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSIONS
    for word in tokens(text):
        digest = hashlib.sha256(word.encode()).digest()
        vector[int.from_bytes(digest[:4]) % EMBEDDING_DIMENSIONS] += 1
    norm = math.sqrt(sum(v * v for v in vector)) or 1
    return [v / norm for v in vector]


class HybridKnowledge:
    def __init__(self, repository: Repository, settings: Settings):
        self.repository, self.settings = repository, settings
        self.embedding_id = (
            "local-feature-hash-v1"
            if settings.embedding_provider == "local"
            else (settings.embedding_model)
        )
        self.client = (
            AsyncOpenAI(
                api_key=settings.llm_api_key.get_secret_value(),
                base_url=settings.llm_base_url,
                timeout=30,
                max_retries=2,
            )
            if (settings.embedding_provider == "openai")
            else None
        )

    async def embed(self, text: str) -> list[float]:
        if self.client is None:
            return local_embedding(text)
        result = await self.client.embeddings.create(
            model=self.settings.embedding_model, input=text, dimensions=EMBEDDING_DIMENSIONS
        )
        return result.data[0].embedding

    async def close(self) -> None:
        if self.client:
            await self.client.close()

    async def seed(self) -> None:
        for document in DOCUMENTS:
            vector = await self.embed(document.title + " " + document.content)
            for environment in ("local", "staging"):
                copy = document.model_copy(
                    update={
                        "environment": environment,
                        "id": document.id if environment == "local" else document.id + "-staging",
                    }
                )
                await asyncio.to_thread(self._store, copy, vector)

    def _store(self, document: KnowledgeDocument, vector: list[float]) -> None:
        with Session(self.repository.engine) as session, session.begin():
            session.merge(KnowledgeRow(**document.model_dump(exclude={"score"})))
            session.flush()
            session.merge(
                ChunkRow(
                    id=document.id + ":0",
                    document_id=document.id,
                    content=document.content,
                    embedding=vector,
                    embedding_model=self.embedding_id,
                )
            )

    async def retrieve(
        self, query: str, pipeline_id: str, environment: str
    ) -> list[KnowledgeDocument]:
        vector = await self.embed(query)
        return await asyncio.to_thread(self._search, query, vector, pipeline_id, environment)

    def _search(self, query, vector, pipeline_id, environment) -> list[KnowledgeDocument]:
        with Session(self.repository.engine) as session:
            statement = (
                select(KnowledgeRow, ChunkRow)
                .join(ChunkRow, ChunkRow.document_id == KnowledgeRow.id)
                .where(
                    KnowledgeRow.pipeline_id == pipeline_id,
                    KnowledgeRow.environment == environment,
                    ChunkRow.embedding_model == self.embedding_id,
                )
            )
            if self.repository.engine.dialect.name == "postgresql":
                statement = statement.order_by(
                    cast(ChunkRow.embedding, Vector(EMBEDDING_DIMENSIONS)).cosine_distance(vector)
                )
            documents = []
            for row, chunk in session.execute(statement.limit(100)):
                dot = sum(a * b for a, b in zip(vector, chunk.embedding, strict=True))
                norm = (
                    math.sqrt(sum(v * v for v in vector) * sum(v * v for v in chunk.embedding)) or 1
                )
                overlap = len(tokens(query) & tokens(row.content)) / max(len(tokens(query)), 1)
                documents.append(
                    KnowledgeDocument(**record(row), score=0.7 * dot / norm + 0.3 * overlap)
                )
            return sorted(documents, key=lambda d: d.score, reverse=True)[:4]
