from fastapi import FastAPI
from pathlib import Path
import mlflow

from train_linearsvm import train_and_evaluate_svm

app = FastAPI(title="Training Service")

DATA_PATH = Path("/data/processed/train_clean.csv")
ARTIFACTS_DIR = Path("/models/run_linear_svm2")

@app.get("/")
def health():
    return {"status": "ok", "service": "training"}

@app.post("/train/svm")
def train_svm():
    mlflow.set_tracking_uri("http://mlflow:5000")
    mlflow.set_experiment("rakuten-linear-svm")

    with mlflow.start_run():
        metrics = train_and_evaluate_svm(
            data_path=DATA_PATH,
            artifacts_dir=ARTIFACTS_DIR
        )

        mlflow.log_metrics(metrics)
        mlflow.log_param("model", "LinearSVM")
        mlflow.log_artifacts(str(ARTIFACTS_DIR))

    return {
        "model": "linear_svm",
        "metrics": metrics
    }
