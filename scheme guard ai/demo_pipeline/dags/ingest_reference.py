"""Land payments and customers topics into the raw layer."""

from datetime import datetime

from _pipeline_tasks import ingest_topic
from airflow import DAG
from airflow.operators.python import PythonOperator

with DAG(
    dag_id="ingest_reference",
    start_date=datetime(2026, 1, 1),
    schedule="@hourly",
    catchup=False,
    default_args={"owner": "data-platform"},
    tags=["ingest"],
) as dag:
    payments = PythonOperator(
        task_id="ingest_payments",
        python_callable=ingest_topic,
        op_kwargs={"topic": "payments.v1", "target": "raw.payments"},
    )
    customers = PythonOperator(
        task_id="ingest_customers",
        python_callable=ingest_topic,
        op_kwargs={"topic": "customers.v1", "target": "raw.customers"},
    )
