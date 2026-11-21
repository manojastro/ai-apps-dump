from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from schemaguard.config import Settings
from schemaguard.pipeline.generator import generate_all, write_jsonl
from schemaguard.schemas.avro import load_pipeline_schemas
from schemaguard.schemas.mutate import apply_mutations

REPO = Path(__file__).resolve().parents[1]
PIPELINE = REPO / "demo_pipeline"


@pytest.fixture
def pipeline_copy(tmp_path: Path) -> Path:
    """A throwaway copy of demo_pipeline with freshly generated synthetic data."""
    dst = tmp_path / "pipeline"
    shutil.copytree(PIPELINE, dst, ignore=shutil.ignore_patterns("data", "*.duckdb", "__pycache__"))
    schemas = load_pipeline_schemas(dst / "avro")
    write_jsonl(generate_all(schemas, seed=42, scale=0.5), dst / "data")
    return dst


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(home=tmp_path / "sg", pipeline_dir=PIPELINE, database_url="", llm_provider="fake")


def orders_schema() -> dict:
    return json.loads((PIPELINE / "avro" / "orders.v1.avsc").read_text())


def mutated(ops: list[dict], topic: str = "orders.v1") -> dict:
    base = json.loads((PIPELINE / "avro" / f"{topic}.avsc").read_text())
    return apply_mutations(base, ops)
