"""Task callables shared by the demo DAGs.

Kept free of Airflow imports so the same functions run under Airflow (optional compose
profile) and under SchemaGuard's local pipeline runner / sandbox.
"""

from __future__ import annotations

import os
from pathlib import Path

PIPELINE_DIR = Path(os.environ.get("DEMO_PIPELINE_DIR", Path(__file__).resolve().parents[1]))
WAREHOUSE = os.environ.get("DEMO_WAREHOUSE", str(PIPELINE_DIR / "warehouse.duckdb"))


def ingest_topic(topic: str, target: str, **_: object) -> int:
    """Load a topic's events (JSONL landing file) into a raw table, typed by its Avro schema."""
    from schemaguard.pipeline import ingest_topic_to_table

    return ingest_topic_to_table(PIPELINE_DIR, WAREHOUSE, topic, target)


def run_sql_file(sql_file: str, target: str, **_: object) -> int:
    """CREATE OR REPLACE <target> AS <select in sql_file>."""
    from schemaguard.pipeline import run_sql_transform

    return run_sql_transform(PIPELINE_DIR, WAREHOUSE, sql_file, target)
