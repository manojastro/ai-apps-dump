"""Tests for the typed tool registry, permissions and audit logging."""
from __future__ import annotations

import pytest

from backend.app.db import SessionLocal
from backend.app.models.entities import ToolCall
from backend.app.tools.base import ToolPermission, ToolRegistry
from backend.app.tools.registry_tools import build_default_registry
from sqlalchemy import select


def test_registry_contains_seven_tools():
    registry = build_default_registry()
    expected = {
        "evaluate_window_tool",
        "train_candidate_tool",
        "evaluate_candidate_tool",
        "shadow_compare_tool",
        "canary_eval_tool",
        "promote_model_tool",
        "rollback_model_tool",
    }
    assert expected == set(registry._tools.keys())


def test_permissions_and_metadata():
    registry = build_default_registry()
    assert registry.get("promote_model_tool").permission is ToolPermission.MUTATING
    assert registry.get("rollback_model_tool").permission is ToolPermission.MUTATING
    for name in ["promote_model_tool", "rollback_model_tool", "train_candidate_tool"]:
        tool = registry.get(name)
        assert tool.permission is ToolPermission.MUTATING
        assert tool.timeout_s > 0
    safe = registry.get("evaluate_window_tool")
    assert safe.permission is ToolPermission.SAFE


def test_unknown_tool_raises():
    registry = ToolRegistry()
    with pytest.raises(KeyError):
        registry.get("does_not_exist")


def test_invoke_validates_input_schema(trained_baseline):
    registry = build_default_registry()
    session = SessionLocal()
    try:
        with pytest.raises(Exception):
            registry.invoke(session, "evaluate_window_tool", {"window_id": "not-an-int"})
    finally:
        session.close()


def test_evaluate_window_tool_audits_call(client, trained_baseline):
    window = client.post(
        "/api/v1/monitoring/windows",
        json={"name": "tool-test", "n_samples": 1500, "seed": 4242},
    ).json()
    registry = build_default_registry()
    session = SessionLocal()
    try:
        output = registry.invoke(session, "evaluate_window_tool", {"window_id": window["id"]})
        assert output["alert"] is False
        rows = list(
            session.scalars(
                select(ToolCall).where(ToolCall.tool_name == "evaluate_window_tool")
            )
        )
        assert len(rows) >= 1
        latest = rows[-1]
        assert latest.success is True
        assert latest.duration_ms > 0
        assert latest.input_payload["window_id"] == window["id"]
    finally:
        session.close()


def test_failed_tool_call_recorded_with_error(trained_baseline):
    registry = build_default_registry()
    session = SessionLocal()
    try:
        with pytest.raises(Exception):
            registry.invoke(session, "evaluate_window_tool", {"window_id": 999999})
        latest = session.scalar(
            select(ToolCall).order_by(ToolCall.id.desc()).limit(1)
        )
        assert latest.success is False
        assert latest.error is not None and "not found" in latest.error
    finally:
        session.close()
