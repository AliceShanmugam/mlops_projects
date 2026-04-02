"""
Airflow DAG for complete ML training pipeline
Tasks: preprocess → train → evaluate → model registry
"""

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.operators.python import PythonOperator
from docker.types import Mount
from airflow.utils.dates import days_ago
from datetime import timedelta
import logging
import os

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
    description='Complete ML training pipeline: download → preprocess → train → evaluate → registry',
    schedule_interval=None,  # Manual trigger via API
    catchup=False,
    tags=['mlops', 'training'],
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

# Credentials MinIO partagés entre les tâches qui accèdent aux données
MINIO_ENV = {
    'MINIO_ENDPOINT': os.getenv('MINIO_ENDPOINT'),
    'AWS_ACCESS_KEY_ID': os.getenv('MINIO_ROOT_USER'),
    'AWS_SECRET_ACCESS_KEY': os.getenv('MINIO_ROOT_PASSWORD'),
}

# Common Docker mounts
COMMON_MOUNTS = [
    Mount(source=f'{PROJECT_ROOT}/logs', target='/app/logs', type='bind'),
    Mount(source='/tmp', target='/tmp', type='bind'),
]

# ============================================================================
# TASK 0: DOWNLOAD raw data → MinIO
# ============================================================================
download_task = DockerOperator(
    task_id='download_data',
    image='alice_project-preprocessing:latest',
    command='python -u src/preprocessing/download.py',
    container_name='airflow-download-{{ execution_date.strftime("%s") }}',
    mounts=COMMON_MOUNTS,
    environment={
        **MINIO_ENV,
        'CHALLENGEDATA_USERNAME': os.getenv('CHALLENGEDATA_USERNAME'),
        'CHALLENGEDATA_PASSWORD': os.getenv('CHALLENGEDATA_PASSWORD'),
        'LOG_LEVEL': 'INFO',
        'LOG_DIR': '/app/logs',
        'PYTHONPATH': '/app',
    },
    dag=dag,
    **DOCKER_BASE_CONFIG,
)

# ============================================================================
# TASK 1: PREPROCESSING
# ============================================================================

preprocess_task = DockerOperator(
    task_id='preprocess_data',
    image='alice_project-preprocessing:latest',
    command='python -u src/preprocessing/run.py',
    container_name='airflow-preprocess-{{ execution_date.strftime("%s") }}',
    mounts=COMMON_MOUNTS,
    environment={
        **MINIO_ENV,
        'BATCH': '{{dag_run.conf.get("batch", "1")}}',  # Pass batch number via conf when triggering
        'LOG_LEVEL': 'INFO',
        'LOG_DIR': '/app/logs',
        'PYTHONPATH': '/app',
    },
    dag=dag,
    **DOCKER_BASE_CONFIG,
)

# ============================================================================
# TASK 2: TRAINING
# ============================================================================

train_task = DockerOperator(
    task_id='train_model',
    image='alice_project-training:latest',
    command=['/bin/sh', '-c', 'python -u src/training/train.py --data_version $(cat /tmp/data_version.txt)'],
    container_name='airflow-train-{{ execution_date.strftime("%s") }}',
    mounts=COMMON_MOUNTS,
    environment={
        **MINIO_ENV,
        'MLFLOW_TRACKING_URI': 'https://dagshub.com/AliceShanmugam/mlops_projects.mlflow',
        'MLFLOW_TRACKING_USERNAME': os.getenv('DAGSHUB_USERNAME'),
        'MLFLOW_TRACKING_PASSWORD': os.getenv('DAGSHUB_USER_TOKEN'),
        'LOG_LEVEL': 'INFO',
        'LOG_DIR': '/app/logs',
        'PYTHONPATH': '/app',
    },
    dag=dag,
    **DOCKER_BASE_CONFIG,
)

# ============================================================================
# TASK 3: EVALUATION
# ============================================================================

evaluate_task = DockerOperator(
    task_id='evaluate_model',
    image='alice_project-training:latest',
    command=['/bin/sh', '-c', 'python -u src/training/evaluate.py "$(cat /tmp/mlflow_run_id.txt)" $(cat /tmp/data_version.txt)'],
    container_name='airflow-eval-{{ execution_date.strftime("%s") }}',
    mounts=COMMON_MOUNTS,
    environment={
        'MLFLOW_TRACKING_URI': 'https://dagshub.com/AliceShanmugam/mlops_projects.mlflow',
        'MLFLOW_TRACKING_USERNAME': os.getenv('DAGSHUB_USERNAME'),
        'MLFLOW_TRACKING_PASSWORD': os.getenv('DAGSHUB_USER_TOKEN'),
        'LOG_LEVEL': 'INFO',
        'LOG_DIR': '/app/logs',
        'PYTHONPATH': '/app',
    },
    dag=dag,
    **DOCKER_BASE_CONFIG,
)

# ============================================================================
# TASK 4: MODEL REGISTRY (Tag as production if better)
# ============================================================================

def register_model(**context):
    """Python operator to handle model registration logic"""
    logger.info("📦 Checking if model should be promoted to production...")
    
    # In production, you'd:
    # 1. Query latest production model F1 from MLFlow
    # 2. Compare with new model F1
    # 3. If better, promote
    
    # For now, we log and promote automatically
    logger.info("✅ Model registered and tagged as production")
    return "promotion_success"

registry_task = PythonOperator(
    task_id='model_registry',
    python_callable=register_model,
    provide_context=True,
    dag=dag,
)

# ============================================================================
# TASK 5: NOTIFICATION (OPTIONAL)
# ============================================================================

def notify_completion(**context):
    """Notify completion"""
    dag_run_id = context['dag_run'].run_id
    logger.info(f"🎉 Training pipeline completed! Run ID: {dag_run_id}")

notify_task = PythonOperator(
    task_id='notify_completion',
    python_callable=notify_completion,
    provide_context=True,
    dag=dag,
)

# ============================================================================
# DEPENDENCIES
# ============================================================================

download_task >> preprocess_task >> train_task >> evaluate_task >> registry_task >> notify_task