"""Isolated patch-apply + test run.

1. copy the pipeline into a fresh sandbox directory (the real pipeline is never modified)
2. apply the candidate patch there
3. install the NEW schema for the changed topic and generate sample data under it
4. run transforms + data tests in a subprocess with a timeout and no network
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from schemaguard.pipeline.generator import generate_all, write_jsonl
from schemaguard.sandbox.patching import PatchError, apply_unified_diff
from schemaguard.schemas.avro import load_pipeline_schemas, parse_schema
from schemaguard.schemas.diff import diff_schemas
from schemaguard.schemas.evolve import evolve_events

IGNORE = shutil.ignore_patterns("data", "*.duckdb", "*.duckdb.wal", "__pycache__")


def prepare_sandbox(
    pipeline_dir: Path, work: Path, topic: str | None, new_schema: dict[str, Any] | None, seed: int = 42
) -> None:
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(pipeline_dir, work, ignore=IGNORE)
    old_schemas = load_pipeline_schemas(work / "avro")
    events = generate_all(old_schemas, seed=seed, scale=0.5)
    if topic and new_schema is not None:
        new = parse_schema(new_schema)
        if topic in old_schemas:
            d = diff_schemas(old_schemas[topic], new, topic)
            events[topic] = evolve_events(events[topic], old_schemas[topic], new, d, seed=seed)
        (work / "avro" / f"{topic}.avsc").write_text(json.dumps(new_schema, indent=2), encoding="utf-8")
    write_jsonl(events, work / "data")


def run_sandbox(
    pipeline_dir: Path,
    work: Path,
    diff: str,
    topic: str | None,
    new_schema: dict[str, Any] | None,
    timeout_s: float = 120.0,
) -> dict[str, Any]:
    started = time.perf_counter()
    work = Path(work).resolve()
    pipeline_dir = Path(pipeline_dir).resolve()
    prepare_sandbox(pipeline_dir, work, topic, new_schema)
    applied: list[str] = []
    if diff:
        try:
            applied = apply_unified_diff(work, diff)
        except PatchError as exc:
            return _result(False, [f"patch does not apply: {exc}"], started, work, applied=[])
    out = work / "_sandbox_result.json"
    env = {
        k: os.environ[k]
        for k in ("PATH", "SYSTEMROOT", "TEMP", "TMP", "HOME", "USERPROFILE")
        if k in os.environ
    }
    env["DEMO_PIPELINE_DIR"] = str(work)
    try:
        proc = subprocess.run(
            [
                sys.executable,
                "-I",
                "-m",
                "schemaguard.sandbox.runner",
                "--pipeline",
                str(work),
                "--out",
                str(out),
            ],
            cwd=work,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        return _result(False, [f"sandbox timed out after {timeout_s}s"], started, work, applied)
    if not out.exists():
        return _result(
            False,
            [f"sandbox produced no result (exit {proc.returncode}): {proc.stderr[-500:]}"],
            started,
            work,
            applied,
        )
    data = json.loads(out.read_text(encoding="utf-8"))
    data.update(
        {
            "duration_s": round(time.perf_counter() - started, 3),
            "patch_applied": applied,
            "sandbox": str(work),
        }
    )
    return data


def _result(ok: bool, failures: list[str], started: float, work: Path, applied: list[str]) -> dict[str, Any]:
    return {
        "ok": ok,
        "tasks": [],
        "tests": [],
        "failures": failures,
        "error": failures[0] if failures else "",
        "duration_s": round(time.perf_counter() - started, 3),
        "patch_applied": applied,
        "sandbox": str(work),
    }
