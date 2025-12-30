# services/training/app/mlflow_utils.py
import mlflow
from .config import MLFLOW_TRACKING_URI, EXPERIMENT_NAME

def init_mlflow():
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)
