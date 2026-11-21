"""Run SQL on a Databricks SQL warehouse through the Statement Execution API.

`SqlRunner` is the seam: the Databricks reader and setup depend on it, and tests swap in a
SQLite-backed runner. Parameters use named markers (`:name`); identifiers (catalog, schema,
table) are validated, never taken from data.
"""

import re
from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementParameterListItem, StatementState

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class DatabricksSqlError(RuntimeError):
    def __init__(self, state: str, message: str) -> None:
        super().__init__(f"statement {state}: {message}")
        self.state = state


def identifier(name: str) -> str:
    if not _IDENTIFIER.match(name):
        raise ValueError(f"unsafe SQL identifier {name!r}")
    return f"`{name}`"


class SqlRunner(Protocol):
    def query(
        self, statement: str, params: Mapping[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Rows as dicts. Values may come back as strings; models parse them."""
        ...

    def execute(self, statement: str) -> None: ...


class StatementRunner:
    """SqlRunner over a SQL warehouse. Auth comes from the Databricks CLI profile."""

    def __init__(
        self, warehouse_id: str, client: WorkspaceClient | None = None, wait_timeout: str = "50s"
    ) -> None:
        self._client = client or WorkspaceClient()
        self._warehouse_id = warehouse_id
        self._wait_timeout = wait_timeout

    @property
    def client(self) -> WorkspaceClient:
        return self._client

    def _run(self, statement: str, params: Mapping[str, Any] | None) -> list[dict[str, Any]]:
        parameters = [
            StatementParameterListItem(name=name, value=None if value is None else str(value))
            for name, value in (params or {}).items()
        ]
        response = self._client.statement_execution.execute_statement(
            statement=statement,
            warehouse_id=self._warehouse_id,
            parameters=parameters or None,
            wait_timeout=self._wait_timeout,
        )
        status = response.status
        state = status.state if status else None
        if state is not StatementState.SUCCEEDED:
            message = status.error.message if status and status.error else "no detail"
            raise DatabricksSqlError(str(state), str(message))
        columns = [
            column.name or f"col{i}"
            for i, column in enumerate(
                (response.manifest.schema.columns or [])
                if response.manifest and response.manifest.schema
                else []
            )
        ]
        data: Sequence[Sequence[Any]] = (
            response.result.data_array if response.result and response.result.data_array else []
        )
        return [dict(zip(columns, row, strict=False)) for row in data]

    def query(
        self, statement: str, params: Mapping[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        return self._run(statement, params)

    def execute(self, statement: str) -> None:
        self._run(statement, None)
