"""Build the full lineage graph for a pipeline directory."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from schemaguard.lineage.airflow_extractor import parse_dags
from schemaguard.lineage.extractors import (
    extract_airflow,
    extract_avro,
    extract_dashboards,
    extract_data_tests,
    extract_sql,
)
from schemaguard.lineage.model import LineageGraph
from schemaguard.pipeline import order_sql_tasks
from schemaguard.schemas.avro import RecordSchema, load_pipeline_schemas


@dataclass
class BuildResult:
    graph: LineageGraph
    warnings: list[str] = field(default_factory=list)


def build_lineage(pipeline_dir: Path, schemas: dict[str, RecordSchema] | None = None) -> BuildResult:
    pipeline_dir = Path(pipeline_dir)
    schemas = schemas if schemas is not None else load_pipeline_schemas(pipeline_dir / "avro")
    lg = LineageGraph()
    warnings: list[str] = []
    extract_avro(lg, schemas)
    dags = parse_dags(pipeline_dir / "dags", root=pipeline_dir)
    extract_airflow(lg, dags, schemas)
    sql_tasks = [t for d in dags for t in d.tasks if t.sql_file and t.target]
    warnings += extract_sql(lg, pipeline_dir, order_sql_tasks(pipeline_dir, sql_tasks))
    warnings += extract_dashboards(lg, pipeline_dir / "dashboards.yaml")
    extract_data_tests(lg, pipeline_dir / "tests" / "data_tests.yaml")
    return BuildResult(lg, warnings)
