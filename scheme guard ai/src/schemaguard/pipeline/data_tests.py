"""Runs demo_pipeline/tests/data_tests.yaml against a DuckDB warehouse."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import duckdb
import yaml


@dataclass
class DataTestResult:
    name: str
    type: str
    passed: bool
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_tests(path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return list(data.get("tests", []))


def _q(ident: str) -> str:
    return ".".join(f'"{p}"' for p in ident.split("."))


def run_test(con: duckdb.DuckDBPyConnection, t: dict[str, Any]) -> DataTestResult:
    name, ttype = t["name"], t["type"]
    try:
        if ttype == "not_null":
            (n,) = con.execute(
                f"select count(*) from {_q(t['table'])} where {_q(t['column'])} is null"
            ).fetchone()  # type: ignore[misc]
            return DataTestResult(name, ttype, n == 0, f"{n} null rows in {t['table']}.{t['column']}")
        if ttype == "unique":
            (n,) = con.execute(  # type: ignore[misc]
                f"select count(*) from (select {_q(t['column'])} from {_q(t['table'])} "
                f"group by 1 having count(*) > 1)"
            ).fetchone()
            return DataTestResult(name, ttype, n == 0, f"{n} duplicated values in {t['table']}.{t['column']}")
        if ttype == "accepted_values":
            rows = con.execute(
                f"select distinct cast({_q(t['column'])} as varchar) from {_q(t['table'])} "
                f"where {_q(t['column'])} is not null"
            ).fetchall()
            bad = sorted({r[0] for r in rows} - {str(v) for v in t["values"]})
            return DataTestResult(name, ttype, not bad, f"unexpected values: {bad}" if bad else "ok")
        if ttype == "row_count_min":
            (n,) = con.execute(f"select count(*) from {_q(t['table'])}").fetchone()  # type: ignore[misc]
            return DataTestResult(name, ttype, n >= t["min"], f"{n} rows (min {t['min']})")
        if ttype == "reconcile":
            (left,) = con.execute(t["left"]).fetchone()  # type: ignore[misc]
            (right,) = con.execute(t["right"]).fetchone()  # type: ignore[misc]
            left_f, right_f = float(left or 0), float(right or 0)
            denom = max(abs(left_f), 1e-9)
            rel = abs(left_f - right_f) / denom
            return DataTestResult(
                name,
                ttype,
                rel <= float(t.get("tolerance", 0.0)),
                f"left={left_f:.2f} right={right_f:.2f} rel_diff={rel:.5f}",
            )
        return DataTestResult(name, ttype, False, f"unknown test type {ttype!r}")
    except duckdb.Error as exc:
        return DataTestResult(name, ttype, False, f"{type(exc).__name__}: {exc}".splitlines()[0][:300])


def run_data_tests(warehouse: str | Path, tests_file: Path) -> list[DataTestResult]:
    con = duckdb.connect(str(warehouse), read_only=True)
    try:
        return [run_test(con, t) for t in load_tests(tests_file)]
    finally:
        con.close()
