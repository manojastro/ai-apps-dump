from pathlib import Path

from schemaguard.lineage.airflow_extractor import parse_dags
from schemaguard.pipeline import order_sql_tasks, run_pipeline, tables_read
from schemaguard.pipeline.generator import generate_all
from schemaguard.schemas.avro import load_pipeline_schemas

REPO = Path(__file__).resolve().parents[2]


def test_avro_schemas_parse():
    schemas = load_pipeline_schemas(REPO / "demo_pipeline" / "avro")
    assert set(schemas) == {"orders.v1", "payments.v1", "customers.v1", "inventory.v1"}
    orders = schemas["orders.v1"]
    assert orders.owner == "checkout-team"
    status = orders.field("status")
    assert status and status.type == "enum" and "CANCELLED" in status.symbols
    coupon = orders.field("coupon_code")
    assert coupon and coupon.nullable and coupon.has_default
    created = orders.field("created_at")
    assert created and created.logical_type == "timestamp-millis"


def test_generator_is_deterministic():
    schemas = load_pipeline_schemas(REPO / "demo_pipeline" / "avro")
    a = generate_all(schemas, seed=7, scale=0.1)
    b = generate_all(schemas, seed=7, scale=0.1)
    c = generate_all(schemas, seed=8, scale=0.1)
    assert a == b
    assert a != c
    order_ids = {o["order_id"] for o in a["orders.v1"]}
    assert all(p["order_id"] in order_ids for p in a["payments.v1"])


def test_dag_parser_extracts_tasks_and_deps():
    dags = {d.dag_id: d for d in parse_dags(REPO / "demo_pipeline" / "dags", root=REPO / "demo_pipeline")}
    assert set(dags) == {"ingest_orders", "ingest_reference", "build_staging", "build_marts"}
    ingest = dags["ingest_orders"].tasks[0]
    assert ingest.reads_topic == "orders.v1" and ingest.target == "raw.orders"
    marts = {t.task_id: t for t in dags["build_marts"].tasks}
    assert marts["daily_revenue"].upstream == ["fct_orders"]
    assert marts["fct_orders"].sql_file == "sql/marts/fct_orders.sql"
    assert dags["build_staging"].owner == "analytics-engineering"


def test_sql_task_order_respects_dependencies():
    pipeline = REPO / "demo_pipeline"
    tasks = [t for d in parse_dags(pipeline / "dags", root=pipeline) for t in d.tasks if t.sql_file]
    order = [t.target for t in order_sql_tasks(pipeline, tasks)]
    assert order.index("stg.stg_orders") < order.index("mart.fct_orders") < order.index("mart.daily_revenue")
    assert tables_read((pipeline / "sql/marts/fct_orders.sql").read_text()) == {
        "stg.stg_orders",
        "stg.stg_payments",
        "stg.stg_customers",
    }


def test_pipeline_end_to_end_passes_data_tests(pipeline_copy, tmp_path):
    result = run_pipeline(pipeline_copy, tmp_path / "wh.duckdb")
    assert result.ok, result.failures()
    assert {t.status for t in result.tasks} == {"success"}
    assert len(result.tests) >= 10


def test_pipeline_reports_broken_sql_and_upstream_failures(pipeline_copy, tmp_path):
    sql = pipeline_copy / "sql/staging/stg_orders.sql"
    sql.write_text(sql.read_text().replace("cast(amount as", "cast(no_such_col as"))
    result = run_pipeline(pipeline_copy, tmp_path / "wh.duckdb")
    status = {t.target: t.status for t in result.tasks}
    assert status["stg.stg_orders"] == "failed"
    assert status["mart.fct_orders"] == "upstream_failed"
    assert status["mart.daily_revenue"] == "upstream_failed"
    assert not result.ok
    assert any("no_such_col" in f for f in result.failures())
