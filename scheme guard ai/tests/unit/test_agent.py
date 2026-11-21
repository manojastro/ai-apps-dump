"""Agent flows with the fake LLM and SQLite checkpointer (no Docker needed)."""

from __future__ import annotations

import subprocess

import pytest

from schemaguard.config import Settings
from schemaguard.llm.base import LLMResponse
from schemaguard.llm.fake import FakeLLM
from schemaguard.service import SchemaGuardService
from tests.conftest import PIPELINE, mutated

RENAME = [{"op": "rename_field", "field": "amount", "to": "total_amount"}]


@pytest.fixture
def svc(settings):
    s = SchemaGuardService(settings)
    yield s
    s.close()


def verdicts(run):
    return {a["asset"]: a["verdict"] for a in run["state"]["assessments"]}


def test_safe_change_ends_with_report_and_no_fix(svc):
    rid, _ = svc.submit_change(
        "orders.v1",
        mutated([{"op": "add_field", "field": "channel", "type": ["null", "string"], "default": None}]),
    )
    run = svc.get_run(rid)
    assert run["status"] == "no_impact"
    st = run["state"]
    assert st["assessments"] == [] and "fix_plan" not in st
    assert "No downstream asset is affected" in st["report"]


def test_unused_field_drop_is_safe(svc):
    rid, _ = svc.submit_change("orders.v1", mutated([{"op": "drop_field", "field": "coupon_code"}]))
    run = svc.get_run(rid)
    assert run["status"] == "no_impact"
    assert run["state"]["change_class"]["change_class"] == "breaking"  # registry view says breaking...
    assert run["state"]["aggregate"]["has_impact"] is False  # ...but nothing downstream reads it


def test_topic_without_consumers(svc):
    rid, _ = svc.submit_change(
        "inventory.v1", mutated([{"op": "drop_field", "field": "delta"}], topic="inventory.v1")
    )
    run = svc.get_run(rid)
    assert run["status"] == "no_impact" and run["state"]["impacted_nodes"] == []


def test_rename_verdicts_fix_and_pause_for_approval(svc):
    rid, created = svc.submit_change("orders.v1", mutated(RENAME))
    assert created
    run = svc.get_run(rid)
    assert run["status"] == "awaiting_approval" and run["next"] == ["human_approval"]
    v = verdicts(run)
    for asset in [
        "column:stg.stg_orders.amount",
        "column:mart.daily_revenue.revenue",
        "visual:Sales Overview/Revenue by Day",
        "visual:Customer Health/LTV Distribution",
        "test:revenue_reconciles_with_staging",
    ]:
        assert v[asset] == "breaking", asset
    assert v.get("column:stg.stg_orders.status") is None  # column-level lineage: status is not affected
    st = run["state"]
    assert st["aggregate"]["dashboards"]["Sales Overview"] == "breaking"
    assert st["baseline_results"]["ok"] is False
    assert st["test_results"]["ok"] is True and st["retry_count"] == 0
    assert "+    cast(total_amount as decimal(12, 2)) as amount," in st["patch"]["diff"]
    assert run["pending_approval"][0]["strategy"] == "update_sql_transform"
    bi = st["aggregate"]["build_impact"]
    assert bi["failing_tables"] == ["stg.stg_orders"]
    assert "mart.daily_revenue" in bi["stale_tables"] and "fct_orders_rows" in bi["blocked_tests"]


def test_idempotent_submission(svc):
    rid1, c1 = svc.submit_change("orders.v1", mutated(RENAME))
    rid2, c2 = svc.submit_change("orders.v1", mutated(RENAME))
    assert (rid1, c1, c2) == (rid2, True, False)
    assert len(svc.list_runs()) == 1


def test_approval_survives_restart_and_creates_branch(settings):
    a = SchemaGuardService(settings)
    rid, _ = a.submit_change("orders.v1", mutated(RENAME))
    assert a.get_run(rid)["status"] == "awaiting_approval"
    a.close()  # simulate API process restart: all in-memory state is gone

    b = SchemaGuardService(settings)
    assert b.get_run(rid)["status"] == "awaiting_approval"
    b.approve(rid, reviewer="alice", comment="looks right")
    run = b.get_run(rid)
    assert run["status"] == "completed"
    st = run["state"]
    assert st["approval"]["reviewer"] == "alice" and st["approval_status"] == "approved"
    assert "branch schemaguard/" in st["pr_url_or_patch_path"]
    repo = settings.resolved_target_repo
    branches = subprocess.run(["git", "-C", str(repo), "branch"], capture_output=True, text=True).stdout
    assert f"schemaguard/{rid[:8]}-orders-v1" in branches
    show = subprocess.run(
        ["git", "-C", str(repo), "show", f"schemaguard/{rid[:8]}-orders-v1:sql/staging/stg_orders.sql"],
        capture_output=True,
        text=True,
    ).stdout
    assert "cast(total_amount as decimal(12, 2)) as amount" in show
    assert (settings.artifacts_dir / rid / "fix.patch").exists()
    assert "approve** by `alice`" in st["report"]
    with pytest.raises(ValueError):
        b.approve(rid, "alice")  # cannot approve twice
    b.close()


def test_reject_path_writes_report_without_branch(svc):
    rid, _ = svc.submit_change("orders.v1", mutated(RENAME))
    svc.reject(rid, reviewer="bob", comment="talk to checkout-team first")
    run = svc.get_run(rid)
    assert run["status"] == "rejected"
    assert "pr_url_or_patch_path" not in run["state"]
    assert "talk to checkout-team first" in run["state"]["report"]


def test_dropped_used_field_retries_then_escalates(svc):
    rid, _ = svc.submit_change("orders.v1", mutated([{"op": "drop_field", "field": "amount"}]))
    run = svc.get_run(rid)
    st = run["state"]
    assert run["status"] == "escalated"
    assert [a["strategy"] for a in st["attempts"]] == ["add_coalesce_default"]
    assert st["attempts"][0]["ok"] is False and any(
        "not_null" in f or "null rows" in f for f in st["attempts"][0]["failures"]
    )
    assert st["retry_count"] == 1
    assert "pin_schema_version" in st["escalation_reason"]
    assert "Escalated" in st["report"]


def test_type_change_int_to_string_fix(svc):
    rid, _ = svc.submit_change(
        "orders.v1", mutated([{"op": "change_type", "field": "quantity", "type": "string"}])
    )
    run = svc.get_run(rid)
    v = verdicts(run)
    assert v["column:mart.daily_revenue.items_sold"] == "breaking"  # sum() on varchar
    assert v["column:stg.stg_orders.quantity"] == "degraded"  # passthrough: type changes
    assert run["status"] == "awaiting_approval"
    assert "cast(quantity as INTEGER) as quantity" in run["state"]["patch"]["diff"]


def test_new_enum_value_breaks_accepted_values_test(svc):
    rid, _ = svc.submit_change(
        "orders.v1", mutated([{"op": "add_enum_symbol", "field": "status", "symbol": "REFUNDED"}])
    )
    run = svc.get_run(rid)
    v = verdicts(run)
    assert v["test:stg_orders_status_accepted"] == "breaking"
    assert v["column:mart.daily_revenue.revenue"] == "degraded"  # REFUNDED now passes status <> 'CANCELLED'
    assert v["visual:Sales Overview/Orders by Status"] == "degraded"
    assert v["column:stg.stg_orders.status"] == "safe"
    assert run["status"] == "awaiting_approval"
    assert "CANCELLED, REFUNDED]" in run["state"]["patch"]["diff"]


def test_budget_exceeded_escalates(settings):
    class PricyLLM(FakeLLM):
        def complete(self, task, system, user, context, json_mode=True):
            r = super().complete(task, system, user, context, json_mode)
            return LLMResponse(r.text, r.tokens_in, r.tokens_out, 0.30, "pricy")

    s = Settings(**{**settings.model_dump(), "run_budget_usd": 0.50})
    svc = SchemaGuardService(s, llm=PricyLLM())
    rid, _ = svc.submit_change("orders.v1", mutated(RENAME))
    run = svc.get_run(rid)
    assert run["status"] == "escalated"
    assert "budget" in run["state"]["escalation_reason"]
    assert "patch" not in run["state"] or not run["state"]["test_results"]
    svc.close()


def test_invalid_schema_marks_run_failed(svc):
    bad = {"type": "record", "name": "X", "fields": [{"name": "a", "type": "not_a_type"}]}
    rid, _ = svc.submit_change("orders.v1", bad)
    run = svc.get_run(rid)
    assert run["status"] == "failed" and run["error"]


def test_mermaid_export(svc):
    m = svc.mermaid()
    for node in ["assess_asset", "human_approval", "plan_fix", "run_tests", "escalate"]:
        assert node in m


def test_pipeline_dir_untouched_by_runs(svc):
    before = {p: p.read_text() for p in (PIPELINE / "sql").rglob("*.sql")}
    svc.submit_change("orders.v1", mutated(RENAME))
    assert {p: p.read_text() for p in (PIPELINE / "sql").rglob("*.sql")} == before


def test_otel_span_per_node(settings):
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    from schemaguard.observability import add_span_processor

    exporter = InMemorySpanExporter()
    add_span_processor(SimpleSpanProcessor(exporter))
    svc = SchemaGuardService(settings)
    rid, _ = svc.submit_change("orders.v1", mutated([{"op": "drop_field", "field": "coupon_code"}]))
    names = {s.name for s in exporter.get_finished_spans() if s.attributes.get("schemaguard.run_id") == rid}
    assert {
        "node.ingest_change",
        "node.diff_schema",
        "node.traverse_lineage",
        "node.aggregate",
        "node.write_report",
    } <= names
    svc.close()
