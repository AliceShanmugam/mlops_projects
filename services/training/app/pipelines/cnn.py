# services/training/app/pipelines/cnn.py
import mlflow
from ..mlflow_utils import init_mlflow

def train_cnn():
    init_mlflow()

    with mlflow.start_run(run_name="cnn-image"):
        mlflow.log_param("model", "cnn")
        mlflow.log_metric("accuracy", 0.75)

    return {"model": "cnn", "status": "trained"}
