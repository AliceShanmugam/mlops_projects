"""
Airflow DAG - ML training pipeline
Tasks: dvc_pull_raw → preprocess → train → evaluate → model_registry

Download mensuel : géré par GitHub Actions (.github/workflows/monthly.yml)
Ce DAG est déclenché via l'API Airflow (admin) après chaque nouveau download.
"""

from datetime import datetime as dt
from datetime import timedelta
import logging
import os

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.utils.dates import days_ago
from airflow.models import Param
from docker.types import Mount

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'alice-mlops',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': days_ago(1),
}

dag = DAG(
    'training_pipeline',
    default_args=default_args,
    description='dvc_pull_raw → preprocess → train → evaluate → registry',
    schedule_interval=None,  # Déclenché via API après le download mensuel GitHub Actions
    catchup=False,
    tags=['mlops', 'training'],
    params={
        "download_date": Param(
            "", 
            type=["string", "null"],
            minLength=0,
            description="YYYY-MM — vide = dernière version, ex: 2026-01 pour janvier"
        )
    },
)

# Get project root
PROJECT_ROOT = os.getenv("PROJECT_ROOT", "/home/sakura/Project/mlops_projects/alice_project")

# Common Docker config
DOCKER_BASE_CONFIG = {
    'docker_url': 'unix://var/run/docker.sock',
    'network_mode': 'alice_network',
    'auto_remove': True,
    'mount_tmp_dir': False,
}

DAGSHUB_ENV = {
    'DAGSHUB_USERNAME': os.getenv('DAGSHUB_USERNAME'),
    'DAGSHUB_USER_TOKEN': os.getenv('DAGSHUB_USER_TOKEN'),
}

MLFLOW_ENV = {
    'MLFLOW_TRACKING_URI': 'https://dagshub.com/AliceShanmugam/mlops_projects.mlflow',
    'MLFLOW_TRACKING_USERNAME': os.getenv('DAGSHUB_USERNAME'),
    'MLFLOW_TRACKING_PASSWORD': os.getenv('DAGSHUB_USER_TOKEN'),
}

# ─── Bind mounts ─────────────────────────────────────────────────────────────
# /tmp partagé entre les tâches pour passer data_version et mlflow_run_id
COMMON_MOUNTS = [
    Mount(source=f'{PROJECT_ROOT}/logs', target='/app/logs', type='bind'),
    Mount(source='/tmp', target='/tmp', type='bind'),
]

# data/ partagé : tous les containers voient le même data/raw/ et data/processed/
# .dvc/ partagé : dvc_pull_task connaît le remote et la version exacte à télécharger
DATA_MOUNTS = [
    Mount(source=f'{PROJECT_ROOT}/data', target='/app/data', type='bind'),
    Mount(source=f'{PROJECT_ROOT}/.dvc', target='/app/.dvc', type='bind'),
]

# models/ partagé : train écrit les .joblib, l'API les lit en temps réel
MODEL_MOUNTS = [
    Mount(source=f'{PROJECT_ROOT}/models', target='/app/models', type='bind'),
]

# ============================================================================
# TASK 0 : DVC PULL — raw data depuis DagsHub → data/raw/
# ============================================================================
dvc_pull_task = DockerOperator(
    task_id='dvc_pull_raw',
    image='alice_project-preprocessing:latest',
    command=['/bin/sh', '-c', (
        'DOWNLOAD_DATE="{{ dag_run.conf.get(\'download_date\') or \'\' }}" && '
        'if [ -n "$DOWNLOAD_DATE" ] && [ "$DOWNLOAD_DATE" != "None" ]; then '
        '  git -C /app fetch --tags https://$DAGSHUB_USERNAME:$DAGSHUB_USER_TOKEN@dagshub.com/AliceShanmugam/mlops_projects.git && '
        '  git -C /app checkout "data-raw-${DOWNLOAD_DATE}" -- data/raw.dvc; '
        'fi && '
        'dvc pull data/raw/'
    )],
    container_name='airflow-dvcpull-{{ execution_date.strftime("%s") }}',
    mounts=COMMON_MOUNTS + DATA_MOUNTS,
    environment={
        **DAGSHUB_ENV,
        'LOG_LEVEL': 'INFO',
        'LOG_DIR': '/app/logs',
        'PYTHONPATH': '/app',
    },
    dag=dag,
    **DOCKER_BASE_CONFIG,
)

# ============================================================================
# TASK 1: PREPROCESSING — data/raw/ → data/processed/
# ============================================================================
preprocess_task = DockerOperator(
    task_id='preprocess_data',
    image='alice_project-preprocessing:latest',
    command='python -u src/preprocessing/run.py',
    container_name='airflow-preprocess-{{ execution_date.strftime("%s") }}',
    mounts=COMMON_MOUNTS + DATA_MOUNTS,
    environment={
        **DAGSHUB_ENV, 
        'DATA_RAW_DIR': '/app/data/raw',
        'DATA_PROCESSED_DIR': '/app/data/processed',
        'DOWNLOAD_DATE': '{{ dag_run.conf.get("download_date") or "" }}',
        'LOG_LEVEL': 'INFO',
        'LOG_DIR': '/app/logs',
        'PYTHONPATH': '/app',
    },
    dag=dag,
    **DOCKER_BASE_CONFIG,
)

# ============================================================================
# TASK 2: TRAINING — data/processed/ → models/ + run MLFlow sur DagsHub
# ============================================================================
train_task = DockerOperator(
    task_id='train_model',
    image='alice_project-training:latest',
    command=['/bin/sh', '-c', 'python -u src/training/train.py --data_version $(cat /tmp/data_version.txt)'],
    container_name='airflow-train-{{ execution_date.strftime("%s") }}',
    mounts=COMMON_MOUNTS + DATA_MOUNTS + MODEL_MOUNTS,
    environment={
        **MLFLOW_ENV,
        'DATA_PROCESSED_DIR': '/app/data/processed',
        'MODELS_PATH': '/app/models',
        'LOG_LEVEL': 'INFO',
        'LOG_DIR': '/app/logs',
        'PYTHONPATH': '/app',
    },
    dag=dag,
    **DOCKER_BASE_CONFIG,
)

# ============================================================================
# TASK 3: EVALUATION — compare nouveau modèle vs production dans MLFlow
# ============================================================================

evaluate_task = DockerOperator(
    task_id='evaluate_model',
    image='alice_project-training:latest',
    command=['/bin/sh', '-c', 'python -u src/training/evaluate.py "$(cat /tmp/mlflow_run_id.txt)" $(cat /tmp/data_version.txt)'],
    container_name='airflow-eval-{{ execution_date.strftime("%s") }}',
    mounts=COMMON_MOUNTS,
    environment={
        **MLFLOW_ENV,
        'LOG_LEVEL': 'INFO',
        'LOG_DIR': '/app/logs',
        'PYTHONPATH': '/app',
    },
    dag=dag,
    **DOCKER_BASE_CONFIG,
)

# ============================================================================
# TASK 4: MODEL REGISTRY — promeut le modèle si meilleur que la production
# ============================================================================

registry_task = DockerOperator(
    task_id='model_registry',
    image='alice_project-training:latest',
    command=['/bin/sh', '-c', (
        'python -u src/training/model_registry.py '
        '"$(cat /tmp/mlflow_run_id.txt)"'
    )],
    container_name='airflow-registry-{{ execution_date.strftime("%s") }}',
    mounts=COMMON_MOUNTS + MODEL_MOUNTS,
    environment={
        **MLFLOW_ENV,
        'ADMIN_API_KEY': os.getenv('ADMIN_API_KEY'),
        'API_SERVICE_URL': 'http://api:8000',
        'LOG_LEVEL': 'INFO',
        'LOG_DIR': '/app/logs',
        'PYTHONPATH': '/app',
    },
    dag=dag,
    **DOCKER_BASE_CONFIG,
)


# ============================================================================
# DEPENDENCIES
# ============================================================================

dvc_pull_task >> preprocess_task >> train_task >> evaluate_task >> registry_task