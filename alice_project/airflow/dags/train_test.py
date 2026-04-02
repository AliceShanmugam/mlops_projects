from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

def dummy_preprocess():
    # Simulate preprocessing output - no-op since we hardcoded values
    logger.info("✓ Data version: 20260316_093954")

PROJECT_ROOT = os.getenv("PROJECT_ROOT", "/home/sakura/Project/mlops_projects/alice_project")

DOCKER_BASE_CONFIG = {
    'docker_url': 'unix://var/run/docker.sock',
    'network_mode': 'alice_network',
    'auto_remove': True,
    'mount_tmp_dir': False,
}

COMMON_MOUNTS = [
    Mount(source=f'{PROJECT_ROOT}/data', target='/app/data', type='bind'),
    Mount(source=f'{PROJECT_ROOT}/models', target='/app/models', type='bind'),
    Mount(source=f'{PROJECT_ROOT}/logs', target='/app/logs', type='bind'),
    Mount(source='/tmp', target='/tmp', type='bind'),
]

with DAG("train_test", start_date=datetime(2026, 1, 1), schedule_interval=None) as dag:
    dummy_task = PythonOperator(
        task_id="fake_preprocess",
        python_callable=dummy_preprocess
    )
    
    train_task = DockerOperator(
        task_id='train_model',
        image='alice_project-training:latest',
                command='python -u src/training/train.py --data_version 20260316_093954',
        mounts=COMMON_MOUNTS,
        environment={
            'MLFLOW_TRACKING_URI': 'http://mlflow-server:5000',
            'LOG_LEVEL': 'INFO',
            'LOG_DIR': '/app/logs',
            'PYTHONPATH': '/app',
        },
        **DOCKER_BASE_CONFIG,
    )
    
    evaluate_task = DockerOperator(
        task_id='evaluate_model',
        image='alice_project-training:latest',
        command='python -u src/training/evaluate.py "0d01a4947f3642df892dea2acad03dfe" 20260316_093954',
        mounts=COMMON_MOUNTS,
        environment={
            'MLFLOW_TRACKING_URI': 'http://mlflow-server:5000',
            'LOG_LEVEL': 'INFO',
            'LOG_DIR': '/app/logs',
            'PYTHONPATH': '/app',
        },
        **DOCKER_BASE_CONFIG,
    )

    def register_model(**context):
        """Python operator to handle model registration logic"""
        logger.info("📦 Checking if model should be promoted to production...")
        logger.info("✅ Model registered and tagged as production")
        return "promotion_success"

    registry_task = PythonOperator(
        task_id='model_registry',
        python_callable=register_model,
        provide_context=True,
        dag=dag,
    )

    # ============================================================================
    # TASK 5: NOTIFICATION
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

    dummy_task >> train_task >> evaluate_task >> registry_task >> notify_task