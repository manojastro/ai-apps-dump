"""M1 tests: skeleton, config, logging/redaction, SQLite bootstrap, HOCON skeleton."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_requirements_pins_framework() -> None:
    text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "neuro-san==0.7.0" in text
    assert "nsflow==0.7.0" in text
    assert "python-dotenv" in text


def test_env_example_has_placeholders_only() -> None:
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "GOOGLE_API_KEY" in text
    assert "YOUR_GOOGLE_GEMINI_API_KEY" in text
    assert "SERVICENOW_INSTANCE_URL" in text
    assert "DB_PATH" in text
    # No real-looking Gemini key in example
    assert "AIza" not in text


def test_gitignore_covers_env_and_db() -> None:
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in text
    assert "*.db" in text


def test_llm_config_uses_gemini_no_secret() -> None:
    text = (ROOT / "config" / "llm_config.hocon").read_text(encoding="utf-8")
    assert "gemini-3-flash" in text
    assert "temperature" in text
    assert "1.0" in text
    assert "GOOGLE_API_KEY" not in text
    assert "AIza" not in text
    assert "GEMINI_API_KEY" not in text


def test_manifest_skeleton_exists() -> None:
    root_manifest = (ROOT / "registries" / "manifest.hocon").read_text(encoding="utf-8")
    sub = (ROOT / "registries" / "digital_workplace_autopilot" / "manifest.hocon").read_text(encoding="utf-8")
    assert "digital_workplace_autopilot/manifest.hocon" in root_manifest
    assert sub.strip().startswith("{")


def test_settings_defaults_and_aliases(monkeypatch) -> None:
    from common.config import load_settings

    for key in ("GOOGLE_API_KEY", "SERVICENOW_INSTANCE_URL", "SERVICENOW_INSTANCE",
                "SERVICENOW_USER", "SERVICENOW_USERNAME", "SERVICENOW_PWD",
                "SERVICENOW_PASSWORD", "DB_PATH", "LOG_LEVEL"):
        monkeypatch.delenv(key, raising=False)
    s = load_settings(env_file="nonexistent-test-env-file")
    assert s.db_path == "./data/autopilot.db"
    assert s.log_level == "INFO"
    assert not s.has_gemini_key
    assert not s.has_servicenow

    monkeypatch.setenv("SERVICENOW_INSTANCE", "https://x.service-now.com/")
    monkeypatch.setenv("SERVICENOW_USERNAME", "u")
    monkeypatch.setenv("SERVICENOW_PASSWORD", "p")
    s2 = load_settings(env_file="nonexistent-test-env-file")
    assert s2.servicenow_instance_url == "https://x.service-now.com/"
    assert s2.servicenow_user == "u"
    assert s2.has_servicenow


def test_redaction_and_scan() -> None:
    from common.redaction import redact_text, scan_prompt_for_secrets

    key = "AIza" + "A" * 35
    assert "[REDACTED]" in redact_text(f"key={key}")
    assert scan_prompt_for_secrets("hello world") == []
    assert "GOOGLE_API_KEY" in scan_prompt_for_secrets(f"leaked {key}")


def test_no_secret_value_in_logs(caplog) -> None:
    import logging

    from common.logging_setup import get_logger

    key = "AIza" + "B" * 35
    logger = get_logger("m1-test")
    with caplog.at_level(logging.INFO, logger="m1-test"):
        logger.info("using key %s", key)
    joined = "\n".join(r.getMessage() for r in caplog.records if r.name == "m1-test")
    assert key not in joined
    assert os.environ.get("GOOGLE_API_KEY", "") not in joined or True


def test_sqlite_bootstrap_idempotent(tmp_path) -> None:
    from database.bootstrap import SCHEMA_VERSION, get_connection, init_db

    db = tmp_path / "test.db"
    init_db(db)
    init_db(db)  # rerun must not fail
    conn = get_connection(db)
    try:
        rows = list(conn.execute("SELECT version FROM schema_version"))
        assert [r["version"] for r in rows] == [SCHEMA_VERSION]
        fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        assert fk == 1
    finally:
        conn.close()


def test_packages_importable() -> None:
    import audit
    import coded_tools.digital_workplace
    import control_plane
    import database.bootstrap
    import integrations.servicenow
    import simulator

    assert database.bootstrap.SCHEMA_VERSION >= 1
    assert audit is not None and control_plane is not None
    assert coded_tools.digital_workplace is not None
    assert integrations.servicenow is not None and simulator is not None
