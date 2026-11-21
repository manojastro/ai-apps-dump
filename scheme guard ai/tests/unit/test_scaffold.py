import json
import logging

from schemaguard.config import Settings
from schemaguard.observability import JsonFormatter, run_context
from schemaguard.store.db import Database


def test_settings_defaults_are_offline(tmp_path):
    s = Settings(home=tmp_path)
    assert s.llm_provider == "fake"
    assert s.database_url == ""
    assert s.sqlite_path == tmp_path / "state.db"


def test_sqlite_database_roundtrip(tmp_path):
    db = Database(tmp_path / "x.db")
    db.execute("create table t (a text, b integer)")
    db.executemany("insert into t values (?, ?)", [("x", 1), ("y", 2)])
    assert db.query("select a, b from t where b > ?", (1,)) == [("y", 2)]
    db.close()


def test_json_log_includes_run_id():
    rec = logging.LogRecord("schemaguard.t", logging.INFO, "f", 1, "hello", (), None)
    rec.duration_ms = 3.5
    with run_context("run-123"):
        out = json.loads(JsonFormatter().format(rec))
    assert out["run_id"] == "run-123"
    assert out["msg"] == "hello"
    assert out["duration_ms"] == 3.5
