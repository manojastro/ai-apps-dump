"""A SQLite stand-in for a Databricks SQL warehouse, for unit tests only.

It loads the same flat rows that `setup.py` uploads, and runs the reader's real SQL after
stripping the catalog.schema prefix and backticks. It proves the reader's queries, named
parameters and row mapping; it does not prove Databricks itself.
"""

import re
import sqlite3
from collections.abc import Mapping
from typing import Any

from invoiceflow.data.dataset import Dataset
from invoiceflow.data.tables import AP_TABLES, flat_rows


class SqliteRunner:
    def __init__(self, dataset: Dataset, prefix: str = "`invoiceflow`.`ap`.") -> None:
        self._prefix = prefix
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.statements: list[str] = []
        for table, columns in AP_TABLES.items():
            names = [c for c, _ in columns]
            self.conn.execute(f"CREATE TABLE {table} ({', '.join(names)})")
            marks = ", ".join(f":{n}" for n in names)
            self.conn.executemany(
                f"INSERT INTO {table} VALUES ({marks})",  # noqa: S608 - test fixture
                list(flat_rows(dataset, table)),
            )

    def _sql(self, statement: str) -> str:
        return re.sub(r"`([A-Za-z0-9_]+)`", r"\1", statement.replace(self._prefix, ""))

    def query(
        self, statement: str, params: Mapping[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        self.statements.append(statement)
        cursor = self.conn.execute(self._sql(statement), dict(params or {}))
        return [dict(row) for row in cursor.fetchall()]

    def execute(self, statement: str) -> None:
        self.statements.append(statement)
