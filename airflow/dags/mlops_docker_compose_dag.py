# -*- coding: utf-8 -*-
"""
Created on Mon Feb 16 02:04:03 2026

@author: coach
"""
#airflow/dags/mlops_docker_compose_dag.py
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.utils.dates import days_ago

default_args = {
    "owner": "mlops",
    "retries": 1,
}

with DAG(
    dag_id="mlops_docker_compose_pipeline",
    default_args=default_args,
    start_date=days_ago(1),
    schedule_interval=None,
    catchup=False,
    max_active_runs=1,
) as dag:

    start_mlflow = DockerOperator(
        task_id="start_mlflow",
        image="mlops_projects-mlflow",
        container_name="mlflow_AF",
        auto_remove=False,
        command="mlflow server --host 0.0.0.0 --port 5000",
        network_mode="mlops_network",
        docker_url="unix://var/run/docker.sock",
    )

    training = DockerOperator(
        task_id="training",
        image="mlops_projects-training",
        container_name="training_AF",
        auto_remove=False,
        network_mode="mlops_network",
        docker_url="unix://var/run/docker.sock",
    )

    inference = DockerOperator(
        task_id="inference",
        image="mlops_projects-inference",
        container_name="inference_AF",
        auto_remove=False,
        network_mode="mlops_network",
        docker_url="unix://var/run/docker.sock",
    )

    gateway = DockerOperator(
        task_id="gateway",
        image="mlops_projects-gateway",
        container_name="gateway_AF",
        auto_remove=False,
        network_mode="mlops_network",
        docker_url="unix://var/run/docker.sock",
    )

    streamlit = DockerOperator(
        task_id="streamlit",
        image="mlops_projects-streamlit",
        container_name="streamlit_AF",
        auto_remove=False,
        network_mode="mlops_network",
        docker_url="unix://var/run/docker.sock",
    )

    gateway >> start_mlflow >> training >> inference >>  streamlit