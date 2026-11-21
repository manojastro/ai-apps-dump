"""Build typed staging tables from the raw layer."""

from datetime import datetime

from _pipeline_tasks import run_sql_file
from airflow import DAG
from airflow.operators.python import PythonOperator

with DAG(
    dag_id="build_staging",
    start_date=datetime(2026, 1, 1),
    schedule="@hourly",
    catchup=False,
    default_args={"owner": "analytics-engineering"},
    tags=["transform"],
) as dag:
    stg_orders = PythonOperator(
        task_id="stg_orders",
        python_callable=run_sql_file,
        op_kwargs={"sql_file": "sql/staging/stg_orders.sql", "target": "stg.stg_orders"},
    )
    stg_payments = PythonOperator(
        task_id="stg_payments",
        python_callable=run_sql_file,
        op_kwargs={"sql_file": "sql/staging/stg_payments.sql", "target": "stg.stg_payments"},
    )
    stg_customers = PythonOperator(
        task_id="stg_customers",
        python_callable=run_sql_file,
        op_kwargs={"sql_file": "sql/staging/stg_customers.sql", "target": "stg.stg_customers"},
    )
