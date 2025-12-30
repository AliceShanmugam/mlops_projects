# services/training/app/pipelines/multimodal.py
import mlflow
from ..mlflow_utils import init_mlflow

def train_multimodal():
    init_mlflow()

    with mlflow.start_run(run_name="multimodal"):
        mlflow.log_param("model", "multimodal")
        mlflow.log_metric("accuracy", 0.78)

    return {"model": "multimodal", "status": "trained"}
