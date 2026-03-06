from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG("test_dag", start_date=datetime(2026, 2, 26), schedule_interval=None) as dag:
    t1 = BashOperator(task_id="hello", bash_command="echo 'Hello Airflow'")