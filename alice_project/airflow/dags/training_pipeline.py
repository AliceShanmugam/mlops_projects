from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from datetime import datetime

with DAG("training_pipeline",
         start_date=datetime(2024,1,1),
         schedule_interval=None) as dag:

    train = DockerOperator(
        task_id="train_model",
        image="alice_project-training:latest",
        command="python train.py",
        auto_remove=True,
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge",  # ou nom réseau compose
    )