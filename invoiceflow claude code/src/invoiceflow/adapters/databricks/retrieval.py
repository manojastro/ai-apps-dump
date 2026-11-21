"""Databricks AI Search (formerly Vector Search) retriever and index setup.

Free Edition: one AI Search endpoint, one search unit, Delta Sync indexes only (ADR 0001).
Chunks are written to a Delta table with Change Data Feed enabled; a Delta Sync index
computes embeddings with the endpoint named in EMBEDDING_ENDPOINT. Queries use
`query_type="hybrid"` and metadata filters, so access control is applied by the index.

Index management and queries go through databricks-sdk's vector_search services, which
authenticate with the Databricks CLI profile.
"""

import io
import json
from collections.abc import Sequence
from typing import Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.vectorsearch import (
    DeltaSyncVectorIndexSpecRequest,
    EmbeddingSourceColumn,
    EndpointType,
    PipelineType,
    VectorIndexType,
)

from invoiceflow.adapters.databricks.sql import SqlRunner, identifier
from invoiceflow.data.models import Role
from invoiceflow.retrieval.models import (
    GLOBAL_VENDOR,
    AccessScope,
    Chunk,
    DocType,
    Hit,
    RetrievalResult,
)

COLUMNS = [
    "chunk_id",
    "doc_id",
    "doc_type",
    "section",
    "title",
    "text",
    "vendor_id",
    "effective_from",
    "effective_to",
    "allowed_roles",
]


def chunk_row(chunk: Chunk) -> dict[str, Any]:
    return {
        "chunk_id": chunk.chunk_id,
        "doc_id": chunk.doc_id,
        "doc_type": chunk.doc_type,
        "section": chunk.section,
        "title": chunk.title,
        "text": chunk.text,
        "vendor_id": chunk.vendor_id,
        "effective_from": chunk.effective_from.isoformat() if chunk.effective_from else None,
        "effective_to": chunk.effective_to.isoformat() if chunk.effective_to else None,
        # space-separated so the AI Search LIKE filter matches whole role names
        "allowed_roles": " ".join(role.value for role in chunk.allowed_roles),
    }


def scope_filters(scope: AccessScope, doc_types: Sequence[DocType] | None) -> dict[str, Any]:
    filters: dict[str, Any] = {"allowed_roles LIKE": scope.role.value}
    if scope.vendor_ids is not None:
        filters["vendor_id"] = [GLOBAL_VENDOR, *sorted(scope.vendor_ids)]
    if doc_types:
        filters["doc_type"] = list(doc_types)
    return filters


def write_chunk_table(
    runner: SqlRunner,
    client: Any,
    chunks: Sequence[Chunk],
    catalog: str,
    schema: str,
    volume: str,
) -> str:
    table = f"{identifier(catalog)}.{identifier(schema)}.`policy_chunks`"
    identifier(volume)
    path = f"/Volumes/{catalog}/{schema}/{volume}/policy_chunks.jsonl"
    data = "".join(json.dumps(chunk_row(c), ensure_ascii=False) + "\n" for c in chunks)
    client.files.upload(path, io.BytesIO(data.encode("utf-8")), overwrite=True)
    properties = "TBLPROPERTIES (delta.enableChangeDataFeed = true)"  # required by Delta Sync
    source = f"read_files('{path}', format => 'json')"  # validated identifiers only
    runner.execute(f"CREATE OR REPLACE TABLE {table} {properties} AS SELECT * FROM {source}")  # noqa: S608
    return table.replace("`", "")


def ensure_endpoint(w: WorkspaceClient, endpoint: str) -> None:
    """Create the AI Search endpoint if missing (Free Edition allows exactly one)."""
    if any(e.name == endpoint for e in w.vector_search_endpoints.list_endpoints()):
        return
    w.vector_search_endpoints.create_endpoint(
        name=endpoint, endpoint_type=EndpointType.STANDARD
    ).result()


def create_index(
    w: WorkspaceClient, endpoint: str, index_name: str, source_table: str, embedding_endpoint: str
) -> str:
    """Create a triggered Delta Sync index over the chunk table, or re-sync it if it exists.

    Uses databricks-sdk (auth via the Databricks CLI profile); the separate
    databricks-ai-search client only accepts a PAT or a service principal from a laptop.
    """
    existing = {i.name for i in w.vector_search_indexes.list_indexes(endpoint_name=endpoint)}
    if index_name in existing:
        w.vector_search_indexes.sync_index(index_name=index_name)
        return "synced"
    w.vector_search_indexes.create_index(
        name=index_name,
        endpoint_name=endpoint,
        primary_key="chunk_id",
        index_type=VectorIndexType.DELTA_SYNC,
        delta_sync_index_spec=DeltaSyncVectorIndexSpecRequest(
            source_table=source_table,
            pipeline_type=PipelineType.TRIGGERED,
            embedding_source_columns=[
                EmbeddingSourceColumn(name="text", embedding_model_endpoint_name=embedding_endpoint)
            ],
            columns_to_sync=COLUMNS,
        ),
    )
    return "created"


class SdkIndex:
    """Adapts `w.vector_search_indexes.query_index` to the `similarity_search` shape the
    retriever expects (manifest columns + data_array)."""

    def __init__(self, w: WorkspaceClient, index_name: str) -> None:
        self._w = w
        self._name = index_name

    def similarity_search(
        self,
        columns: list[str],
        query_text: str,
        filters: dict[str, Any],
        num_results: int,
        query_type: str,
    ) -> dict[str, Any]:
        response = self._w.vector_search_indexes.query_index(
            index_name=self._name,
            columns=columns,
            query_text=query_text,
            filters_json=json.dumps(filters),
            num_results=num_results,
            query_type=query_type.upper(),
        )
        manifest = (
            response.manifest.columns if response.manifest and response.manifest.columns else []
        )
        rows = response.result.data_array if response.result and response.result.data_array else []
        return {
            "manifest": {"columns": [{"name": c.name} for c in manifest]},
            "result": {"data_array": rows},
        }


class AISearchRetriever:
    def __init__(self, index: Any, min_score: float = 0.0) -> None:
        self._index = index
        self._min_score = min_score

    def search(
        self,
        query: str,
        scope: AccessScope,
        k: int = 5,
        doc_types: Sequence[DocType] | None = None,
    ) -> RetrievalResult:
        response = self._index.similarity_search(
            columns=COLUMNS,
            query_text=query,
            filters=scope_filters(scope, doc_types),
            num_results=k,
            query_type="hybrid",
        )
        manifest = [c["name"] for c in response.get("manifest", {}).get("columns", [])]
        rows = response.get("result", {}).get("data_array", []) or []
        hits = []
        for row in rows:
            record = dict(zip(manifest, row, strict=False))
            score = float(record.pop("score", 0.0))
            if score < self._min_score:
                continue
            roles = tuple(Role(r) for r in str(record.pop("allowed_roles", "")).split())
            chunk = Chunk.model_validate(
                {**{c: record.get(c) for c in COLUMNS[:-1]}, "allowed_roles": roles}
            )
            if scope.allows(chunk):  # defence in depth: re-check the index's filtering
                hits.append(Hit(chunk=chunk, score=score))
        if not hits:
            return RetrievalResult(
                query=query, hits=(), abstained=True, reason="insufficient evidence"
            )
        return RetrievalResult(query=query, hits=tuple(hits))
