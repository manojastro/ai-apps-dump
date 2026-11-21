"""Local runner for the demo pipeline: ingest topics -> raw, run SQL transforms, run data tests.

Used by the demo (`schemaguard pipeline run`), by Airflow task callables, and by the sandbox.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import duckdb
import sqlglot
from sqlglot import exp

from schemaguard.lineage.airflow_extractor import TaskSpec, parse_dags
from schemaguard.pipeline.data_tests import DataTestResult, run_data_tests
from schemaguard.schemas.avro import RecordSchema, load_pipeline_schemas


def _q(ident: str) -> str:
    return ".".join(f'"{p}"' for p in ident.split("."))


def create_raw_table(
    con: duckdb.DuckDBPyConnection, schema: RecordSchema, target: str, jsonl: Path | None
) -> int:
    db_schema = target.split(".")[0]
    con.execute(f'create schema if not exists "{db_schema}"')
    cols = ", ".join(f'"{f.name}" {f.duckdb_type}' for f in schema.fields)
    con.execute(f"create or replace table {_q(target)} ({cols})")
    if jsonl and jsonl.exists() and jsonl.stat().st_size > 0:
        col_map = "{" + ", ".join(f"'{f.name}': '{f.duckdb_type}'" for f in schema.fields) + "}"
        path = str(jsonl).replace("\\", "/").replace("'", "''")
        con.execute(
            f"insert into {_q(target)} select * from read_json('{path}', "
            f"format='newline_delimited', columns={col_map})"
        )
    (n,) = con.execute(f"select count(*) from {_q(target)}").fetchone()  # type: ignore[misc]
    return int(n)


def ingest_topic_to_table(pipeline_dir: Path, warehouse: str, topic: str, target: str) -> int:
    schemas = load_pipeline_schemas(Path(pipeline_dir) / "avro")
    con = duckdb.connect(warehouse)
    try:
        return create_raw_table(con, schemas[topic], target, Path(pipeline_dir) / "data" / f"{topic}.jsonl")
    finally:
        con.close()


def read_sql(pipeline_dir: Path, sql_file: str) -> str:
    return (Path(pipeline_dir) / sql_file).read_text(encoding="utf-8")


def tables_read(sql: str) -> set[str]:
    tree = sqlglot.parse_one(sql, dialect="duckdb")
    out = set()
    for t in tree.find_all(exp.Table):
        if t.db:
            out.add(f"{t.db}.{t.name}")
    return out


def run_sql_transform_con(
    con: duckdb.DuckDBPyConnection, pipeline_dir: Path, sql_file: str, target: str
) -> int:
    sql = read_sql(pipeline_dir, sql_file).strip().rstrip(";")
    con.execute(f'create schema if not exists "{target.split(".")[0]}"')
    con.execute(f"create or replace table {_q(target)} as {sql}")
    (n,) = con.execute(f"select count(*) from {_q(target)}").fetchone()  # type: ignore[misc]
    return int(n)


def run_sql_transform(pipeline_dir: Path, warehouse: str, sql_file: str, target: str) -> int:
    con = duckdb.connect(warehouse)
    try:
        return run_sql_transform_con(con, pipeline_dir, sql_file, target)
    finally:
        con.close()


@dataclass
class TaskRun:
    task_id: str
    target: str
    status: str  # success | failed | upstream_failed
    rows: int = 0
    error: str = ""


@dataclass
class PipelineResult:
    tasks: list[TaskRun] = field(default_factory=list)
    tests: list[DataTestResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(t.status == "success" for t in self.tasks) and all(t.passed for t in self.tests)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "tasks": [asdict(t) for t in self.tasks],
            "tests": [t.to_dict() for t in self.tests],
        }

    def failures(self) -> list[str]:
        out = [f"task {t.task_id} {t.status}: {t.error}" for t in self.tasks if t.status != "success"]
        out += [f"test {t.name} failed: {t.detail}" for t in self.tests if not t.passed]
        return out


def order_sql_tasks(pipeline_dir: Path, tasks: list[TaskSpec]) -> list[TaskSpec]:
    """Topological order of SQL tasks by the tables each one reads/writes."""
    by_target = {t.target: t for t in tasks if t.target}
    deps: dict[str, set[str]] = {}
    for t in tasks:
        assert t.sql_file and t.target
        try:
            reads = tables_read(read_sql(pipeline_dir, t.sql_file))
        except Exception:
            reads = set()
        deps[t.target] = {r for r in reads if r in by_target and r != t.target}
    ordered: list[TaskSpec] = []
    done: set[str] = set()
    while len(ordered) < len(tasks):
        ready = sorted(tgt for tgt, d in deps.items() if tgt not in done and d <= done)
        if not ready:  # cycle: append the rest in file order
            ordered += [t for t in tasks if t.target not in done]
            break
        for tgt in ready:
            ordered.append(by_target[tgt])
            done.add(tgt)
    return ordered


def run_pipeline(pipeline_dir: Path, warehouse: Path | str, run_tests: bool = True) -> PipelineResult:
    pipeline_dir = Path(pipeline_dir)
    dags = parse_dags(pipeline_dir / "dags", root=pipeline_dir)
    all_tasks = [t for d in dags for t in d.tasks]
    ingest = [t for t in all_tasks if t.reads_topic and t.target]
    sql_tasks = [t for t in all_tasks if t.sql_file and t.target]
    schemas = load_pipeline_schemas(pipeline_dir / "avro")
    result = PipelineResult()
    failed_tables: set[str] = set()
    Path(warehouse).parent.mkdir(parents=True, exist_ok=True)
    Path(warehouse).unlink(missing_ok=True)
    con = duckdb.connect(str(warehouse))
    try:
        for t in ingest:
            assert t.reads_topic and t.target
            try:
                n = create_raw_table(
                    con, schemas[t.reads_topic], t.target, pipeline_dir / "data" / f"{t.reads_topic}.jsonl"
                )
                result.tasks.append(TaskRun(t.id, t.target, "success", n))
            except Exception as exc:
                failed_tables.add(t.target)
                result.tasks.append(TaskRun(t.id, t.target, "failed", error=_err(exc)))
        for t in order_sql_tasks(pipeline_dir, sql_tasks):
            assert t.sql_file and t.target
            try:
                reads = tables_read(read_sql(pipeline_dir, t.sql_file))
            except Exception:
                reads = set()
            if reads & failed_tables:
                failed_tables.add(t.target)
                con.execute(f"drop table if exists {_q(t.target)}")
                result.tasks.append(
                    TaskRun(
                        t.id, t.target, "upstream_failed", error=f"upstream: {sorted(reads & failed_tables)}"
                    )
                )
                continue
            try:
                n = run_sql_transform_con(con, pipeline_dir, t.sql_file, t.target)
                result.tasks.append(TaskRun(t.id, t.target, "success", n))
            except Exception as exc:
                failed_tables.add(t.target)
                result.tasks.append(TaskRun(t.id, t.target, "failed", error=_err(exc)))
    finally:
        con.close()
    if run_tests:
        result.tests = run_data_tests(warehouse, pipeline_dir / "tests" / "data_tests.yaml")
    return result


def _err(exc: Exception) -> str:
    return f"{type(exc).__name__}: {str(exc).splitlines()[0][:300]}"


def dump_result(result: PipelineResult, path: Path) -> None:
    path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
