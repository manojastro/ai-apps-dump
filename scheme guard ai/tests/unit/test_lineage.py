from pathlib import Path

import pytest

from schemaguard.lineage.airflow_extractor import parse_dags
from schemaguard.lineage.builder import build_lineage
from schemaguard.lineage.extractors import (
    extract_airflow,
    extract_avro,
    extract_dashboards,
    extract_data_tests,
    extract_sql,
)
from schemaguard.lineage.model import LineageGraph
from schemaguard.lineage.store import SqlLineageStore
from schemaguard.pipeline import order_sql_tasks
from schemaguard.schemas.avro import load_pipeline_schemas
from schemaguard.store.db import Database

REPO = Path(__file__).resolve().parents[2]
PIPE = REPO / "demo_pipeline"


@pytest.fixture(scope="module")
def lg() -> LineageGraph:
    r = build_lineage(PIPE)
    assert r.warnings == []
    return r.graph


def _edge(lg, src, dst, type_):
    return [d for d in (lg.g.get_edge_data(src, dst) or {}).values() if d["type"] == type_]


# --- extractor unit tests --------------------------------------------------------------------
def test_avro_extractor():
    g = LineageGraph()
    extract_avro(g, load_pipeline_schemas(PIPE / "avro"))
    assert g.node("field:orders.v1.status")["symbols"] == ["PLACED", "PAID", "SHIPPED", "CANCELLED"]
    assert _edge(g, "topic:orders.v1", "field:orders.v1.amount", "HAS_FIELD")
    assert _edge(g, "topic:orders.v1", "owner:checkout-team", "OWNED_BY")


def test_airflow_extractor():
    g = LineageGraph()
    schemas = load_pipeline_schemas(PIPE / "avro")
    extract_avro(g, schemas)
    extract_airflow(g, parse_dags(PIPE / "dags", root=PIPE), schemas)
    assert _edge(g, "topic:orders.v1", "task:ingest_orders.ingest_orders", "CONSUMED_BY")
    assert _edge(g, "task:build_staging.stg_orders", "table:stg.stg_orders", "WRITES")
    assert _edge(g, "task:build_staging.stg_orders", "dag:build_staging", "PART_OF")
    (e,) = _edge(g, "column:raw.orders.amount", "field:orders.v1.amount", "DERIVES_FROM")
    assert e["via"] == "ingest"
    assert "topic:inventory.v1" in g.g and not g.out("topic:inventory.v1", "CONSUMED_BY")


def test_sql_extractor_value_and_filter_edges():
    g = LineageGraph()
    schemas = load_pipeline_schemas(PIPE / "avro")
    dags = parse_dags(PIPE / "dags", root=PIPE)
    extract_avro(g, schemas)
    extract_airflow(g, dags, schemas)
    tasks = order_sql_tasks(PIPE, [t for d in dags for t in d.tasks if t.sql_file])
    assert extract_sql(g, PIPE, tasks) == []
    (cast_edge,) = _edge(g, "column:stg.stg_orders.amount", "column:raw.orders.amount", "DERIVES_FROM")
    assert cast_edge["transform"] == "cast" and cast_edge["line"] == 6 and "DECIMAL" in cast_edge["cast_to"]
    (agg,) = _edge(g, "column:mart.daily_revenue.revenue", "column:mart.fct_orders.amount", "DERIVES_FROM")
    assert agg["transform"] == "aggregate"
    (flt,) = _edge(g, "column:mart.daily_revenue.revenue", "column:mart.fct_orders.status", "DERIVES_FROM")
    assert flt["via"] == "filter" and flt["line"] == 9
    joins = _edge(g, "column:mart.fct_orders.country", "column:stg.stg_orders.customer_id", "DERIVES_FROM")
    assert joins and joins[0]["via"] == "join"
    # alias rename inside SQL: paid_amount comes from raw.payments.amount
    assert _edge(g, "column:stg.stg_payments.paid_amount", "column:raw.payments.amount", "DERIVES_FROM")


def test_dashboard_and_test_extractors(lg):
    assert _edge(lg, "column:mart.daily_revenue.revenue", "visual:Sales Overview/Revenue by Day", "USED_BY")
    assert _edge(lg, "visual:Sales Overview/Revenue by Day", "dashboard:Sales Overview", "PART_OF")
    assert _edge(lg, "dashboard:Customer Health", "owner:customer-success", "OWNED_BY")
    assert _edge(lg, "column:stg.stg_orders.status", "test:stg_orders_status_accepted", "TESTED_BY")
    assert _edge(lg, "column:mart.daily_revenue.revenue", "test:revenue_reconciles_with_staging", "TESTED_BY")


def test_dashboard_extractor_flags_unknown_columns(tmp_path):
    m = tmp_path / "d.yaml"
    m.write_text(
        "dashboards:\n- name: X\n  owner: t\n  visuals:\n  - name: V\n    columns: [mart.nope.col]\n"
    )
    g = LineageGraph()
    warnings = extract_dashboards(g, m)
    assert warnings and "unknown column" in warnings[0]
    assert g.node("column:mart.nope.col")["missing"] is True


def test_data_test_extractor_on_reconcile(tmp_path):
    f = tmp_path / "t.yaml"
    f.write_text("tests:\n- name: r\n  type: reconcile\n  left: select sum(a) from s.t\n  right: select 1\n")
    g = LineageGraph()
    g.add_node("column:s.t.a", "Column", name="a", table="s.t")
    extract_data_tests(g, f)
    assert _edge(g, "column:s.t.a", "test:r", "TESTED_BY")


# --- graph queries ---------------------------------------------------------------------------
def test_impact_paths_for_amount_reach_dashboards(lg):
    paths = lg.impact_paths("field:orders.v1.amount")
    assert (
        "orders.v1.amount → stg_orders.amount → fct_orders.amount → daily_revenue.revenue → Sales Overview / Revenue by Day"
        in paths
    )
    assert any(p.endswith("Customer Health / LTV Distribution") for p in paths)
    assert any(p.endswith("Finance Reconciliation / Paid vs Ordered") for p in paths)


def test_downstream_returns_paths_and_context(lg):
    nodes = {n.id: n for n in lg.downstream("field:orders.v1.amount")}
    assert nodes["visual:Sales Overview/Revenue by Day"].path[0] == "field:orders.v1.amount"
    assert nodes["dashboard:Sales Overview"].type == "Dashboard"
    assert nodes["task:build_staging.stg_orders"].context is True
    # value path is preferred over filter path
    assert nodes["column:mart.daily_revenue.revenue"].vias == ["ingest", "value", "value", "value"]
    assert "column:mart.fct_orders.status" not in nodes


def test_downstream_max_depth(lg):
    shallow = {n.id for n in lg.downstream("field:orders.v1.amount", max_depth=2, include_context=False)}
    assert shallow == {"column:raw.orders.amount", "column:stg.stg_orders.amount"}


def test_unused_field_and_unconsumed_topic(lg):
    flow = [n for n in lg.downstream("field:orders.v1.coupon_code") if not n.context]
    assert [n.id for n in flow] == ["column:raw.orders.coupon_code"]
    assert [n.id for n in lg.downstream("field:inventory.v1.delta")] == []


def test_upstream_for_root_cause(lg):
    ups = {n.id for n in lg.upstream("column:mart.daily_revenue.revenue")}
    assert {"field:orders.v1.amount", "field:orders.v1.status", "topic:orders.v1"} <= ups
    assert "field:payments.v1.amount" not in ups


def test_blast_radius_summary(lg):
    s = lg.blast_radius_summary("field:orders.v1.amount")
    assert s["dashboards"] == ["Customer Health", "Finance Reconciliation", "Sales Overview"]
    assert {"finance", "sales-analytics", "customer-success"} <= set(s["by_owner"])
    assert s["by_type"]["Visual"] == 3


def test_status_change_reaches_revenue_through_filter(lg):
    paths = lg.impact_paths("field:orders.v1.status")
    assert any("Revenue by Day" in p and "(via filter)" in p for p in paths)
    assert any(p.endswith("Sales Overview / Orders by Status") and "via" not in p for p in paths)


def test_unknown_node_raises(lg):
    with pytest.raises(KeyError):
        lg.downstream("field:nope.x")


# --- store -----------------------------------------------------------------------------------
def test_sql_store_roundtrip_and_versioning(lg, tmp_path):
    store = SqlLineageStore(Database(tmp_path / "s.db"))
    v1 = store.save(lg, source="test")
    assert store.save(lg) == v1  # identical content -> same version
    loaded = store.load(v1)
    assert loaded.content_hash() == lg.content_hash()
    assert loaded.impact_paths("field:orders.v1.amount") == lg.impact_paths("field:orders.v1.amount")
    lg2 = LineageGraph.from_records(*lg.to_records())
    lg2.add_node("owner:new", "Owner", name="new")
    assert store.save(lg2) == v1 + 1
    assert store.latest_version() == v1 + 1
    with pytest.raises(LookupError):
        store.load(99)
