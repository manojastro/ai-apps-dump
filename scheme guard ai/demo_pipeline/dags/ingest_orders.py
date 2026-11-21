"""Land the orders topic into the warehouse raw layer."""

from datetime import datetime

from _pipeline_tasks import ingest_topic
from airflow import DAG
from airflow.operators.python import PythonOperator

with DAG(
    dag_id="ingest_orders",
    start_date=datetime(2026, 1, 1),
    schedule="@hourly",
    catchup=False,
    default_args={"owner": "data-platform"},
    tags=["ingest"],
) as dag:
    ingest = PythonOperator(
        task_id="ingest_orders",
        python_callable=ingest_topic,
        op_kwargs={"topic": "orders.v1", "target": "raw.orders"},
    )
