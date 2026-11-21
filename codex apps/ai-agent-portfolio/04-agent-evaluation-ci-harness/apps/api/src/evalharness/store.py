from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4

from .dataset import generate_demo_cases
from .models import RunReport, SampleResult, TargetResponse, TestCase


DDL = [
    "CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS datasets (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, name TEXT NOT NULL, version TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS test_cases (id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL, payload TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS experiments (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, target TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, experiment_id TEXT NOT NULL, dataset_id TEXT NOT NULL, target TEXT NOT NULL, aggregate TEXT NOT NULL, categories TEXT NOT NULL, intervals TEXT NOT NULL, metadata TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS samples (id TEXT PRIMARY KEY, run_id TEXT NOT NULL, case_id TEXT NOT NULL, payload TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS metric_results (id TEXT PRIMARY KEY, run_id TEXT NOT NULL, sample_id TEXT, metric TEXT NOT NULL, value REAL NOT NULL)",
    "CREATE TABLE IF NOT EXISTS baselines (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, run_id TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS judge_configs (id TEXT PRIMARY KEY, run_id TEXT NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL, config TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS cost_records (id TEXT PRIMARY KEY, run_id TEXT NOT NULL, sample_id TEXT NOT NULL, prompt_tokens INTEGER NOT NULL, completion_tokens INTEGER NOT NULL, cost_usd REAL NOT NULL)",
    "CREATE TABLE IF NOT EXISTS gate_configs (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, config TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS gate_results (id TEXT PRIMARY KEY, run_id TEXT NOT NULL, passed INTEGER NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL)",
]


class Database:
    def __init__(self, url: str | None = None) -> None:
        self.url = url or os.getenv("DATABASE_URL", "sqlite:///evalharness.db")
        self.postgres = self.url.startswith(("postgresql://", "postgres://"))

    @contextmanager
    def connection(self) -> Iterator[Any]:
        if self.postgres:
            import psycopg
            from psycopg.rows import dict_row
            connection = psycopg.connect(self.url, row_factory=dict_row)
        else:
            path = self.url.removeprefix("sqlite:///")
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(path)
            connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _sql(self, query: str) -> str:
        return query.replace("?", "%s") if self.postgres else query

    def execute(self, query: str, params: tuple = ()) -> None:
        with self.connection() as connection:
            connection.execute(self._sql(query), params)

    def rows(self, query: str, params: tuple = ()) -> list[dict]:
        with self.connection() as connection:
            cursor = connection.execute(self._sql(query), params)
            return [dict(row) for row in cursor.fetchall()]

    def initialize(self) -> None:
        with self.connection() as connection:
            for statement in DDL:
                connection.execute(statement)

    def seed_demo(self) -> dict[str, int]:
        from datetime import UTC, datetime
        now = datetime.now(UTC).isoformat()
        self.execute(
            "INSERT INTO projects (id,name,created_at) VALUES (?,?,?) ON CONFLICT (id) DO NOTHING",
            ("demo-project", "Enterprise Support Demo", now),
        )
        self.execute(
            "INSERT INTO datasets (id,project_id,name,version,created_at) VALUES (?,?,?,?,?) ON CONFLICT (id) DO NOTHING",
            ("demo-200", "demo-project", "Golden Support Questions", "1.0.0", now),
        )
        for case in generate_demo_cases():
            self.execute(
                "INSERT INTO test_cases (id,dataset_id,payload) VALUES (?,?,?) ON CONFLICT (id) DO NOTHING",
                (case.id, "demo-200", json.dumps(case.to_dict())),
            )
        return {"projects": 1, "datasets": 1, "test_cases": 200}

    def get_cases(self, dataset_id: str = "demo-200") -> list[TestCase]:
        return [
            TestCase.from_dict(json.loads(row["payload"]))
            for row in self.rows("SELECT payload FROM test_cases WHERE dataset_id=? ORDER BY id", (dataset_id,))
        ]

    def save_dataset(
        self, cases: list[TestCase], dataset_id: str, name: str, project_id: str = "demo-project"
    ) -> None:
        from datetime import UTC, datetime
        now = datetime.now(UTC).isoformat()
        self.execute(
            "INSERT INTO projects (id,name,created_at) VALUES (?,?,?) ON CONFLICT (id) DO NOTHING",
            (project_id, project_id.replace("-", " ").title(), now),
        )
        self.execute(
            "INSERT INTO datasets (id,project_id,name,version,created_at) VALUES (?,?,?,?,?) ON CONFLICT (id) DO NOTHING",
            (dataset_id, project_id, name, "imported", now),
        )
        for case in cases:
            self.execute(
                "INSERT INTO test_cases (id,dataset_id,payload) VALUES (?,?,?) ON CONFLICT (id) DO UPDATE SET payload=excluded.payload",
                (case.id, dataset_id, json.dumps(case.to_dict())),
            )

    def save_run(self, report: RunReport) -> None:
        experiment_id = str(uuid4())
        self.execute(
            "INSERT INTO experiments (id,project_id,target,created_at) VALUES (?,?,?,?)",
            (experiment_id, report.project_id, report.target, report.created_at),
        )
        self.execute(
            "INSERT INTO runs (id,experiment_id,dataset_id,target,aggregate,categories,intervals,metadata,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (report.id, experiment_id, report.dataset_id, report.target,
             json.dumps(report.aggregate), json.dumps(report.category_metrics),
             json.dumps(report.confidence_intervals), json.dumps(report.metadata), report.created_at),
        )
        self.execute(
            "INSERT INTO judge_configs (id,run_id,provider,model,config) VALUES (?,?,?,?,?)",
            (str(uuid4()), report.id, report.judge_config["provider"],
             report.judge_config["model"], json.dumps(report.judge_config)),
        )
        for sample in report.samples:
            sample_id = str(uuid4())
            self.execute(
                "INSERT INTO samples (id,run_id,case_id,payload) VALUES (?,?,?,?)",
                (sample_id, report.id, sample.case.id, json.dumps(sample.to_dict())),
            )
            for metric, value in sample.metrics.items():
                self.execute(
                    "INSERT INTO metric_results (id,run_id,sample_id,metric,value) VALUES (?,?,?,?,?)",
                    (str(uuid4()), report.id, sample_id, metric, value),
                )
            self.execute(
                "INSERT INTO cost_records (id,run_id,sample_id,prompt_tokens,completion_tokens,cost_usd) VALUES (?,?,?,?,?,?)",
                (str(uuid4()), report.id, sample_id, sample.response.prompt_tokens,
                 sample.response.completion_tokens, sample.response.cost_usd),
            )

    def get_run(self, run_id: str) -> RunReport | None:
        rows = self.rows("SELECT * FROM runs WHERE id=?", (run_id,))
        if not rows:
            return None
        run = rows[0]
        samples = []
        for row in self.rows("SELECT payload FROM samples WHERE run_id=? ORDER BY case_id", (run_id,)):
            value = json.loads(row["payload"])
            samples.append(SampleResult(
                TestCase.from_dict(value["case"]), TargetResponse.from_dict(value["response"]),
                value["metrics"], value.get("violations", []),
            ))
        judge_rows = self.rows("SELECT config FROM judge_configs WHERE run_id=?", (run_id,))
        experiment = self.rows("SELECT project_id FROM experiments WHERE id=?", (run["experiment_id"],))[0]
        return RunReport(
            id=run["id"], project_id=experiment["project_id"], dataset_id=run["dataset_id"],
            target=run["target"], judge_config=json.loads(judge_rows[0]["config"]),
            aggregate=json.loads(run["aggregate"]), category_metrics=json.loads(run["categories"]),
            confidence_intervals=json.loads(run["intervals"]), samples=samples,
            created_at=run["created_at"], metadata=json.loads(run["metadata"]),
        )

    def list_runs(self) -> list[dict]:
        return self.rows("SELECT id,dataset_id,target,aggregate,created_at FROM runs ORDER BY created_at DESC")

    def mark_baseline(self, project_id: str, run_id: str) -> None:
        from datetime import UTC, datetime
        self.execute("DELETE FROM baselines WHERE project_id=?", (project_id,))
        self.execute(
            "INSERT INTO baselines (id,project_id,run_id,created_at) VALUES (?,?,?,?)",
            (str(uuid4()), project_id, run_id, datetime.now(UTC).isoformat()),
        )

    def get_baseline(self, project_id: str) -> RunReport | None:
        rows = self.rows("SELECT run_id FROM baselines WHERE project_id=?", (project_id,))
        return self.get_run(rows[0]["run_id"]) if rows else None
