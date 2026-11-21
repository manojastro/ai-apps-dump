"""Build business marts used by the BI dashboards."""

from datetime import datetime

from _pipeline_tasks import run_sql_file
from airflow import DAG
from airflow.operators.python import PythonOperator

with DAG(
    dag_id="build_marts",
    start_date=datetime(2026, 1, 1),
    schedule="@hourly",
    catchup=False,
    default_args={"owner": "analytics-engineering"},
    tags=["transform"],
) as dag:
    fct_orders = PythonOperator(
        task_id="fct_orders",
        python_callable=run_sql_file,
        op_kwargs={"sql_file": "sql/marts/fct_orders.sql", "target": "mart.fct_orders"},
    )
    daily_revenue = PythonOperator(
        task_id="daily_revenue",
        python_callable=run_sql_file,
        op_kwargs={"sql_file": "sql/marts/daily_revenue.sql", "target": "mart.daily_revenue"},
    )
    customer_ltv = PythonOperator(
        task_id="customer_ltv",
        python_callable=run_sql_file,
        op_kwargs={"sql_file": "sql/marts/customer_ltv.sql", "target": "mart.customer_ltv"},
    )
    fct_orders >> [daily_revenue, customer_ltv]
