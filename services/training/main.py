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
        metrics = train_and_evaluate_svm()

        # ✅ PARAMS
        mlflow.log_param("model", "linear_svm")
        mlflow.log_param("vectorizer", "tfidf")

        # ✅ METRICS (SCALAIRES UNIQUEMENT)
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                mlflow.log_metric(key, value)

    return {
        "status": "success",
        "model": "linear_svm",
        "metrics": {
            k: v for k, v in metrics.items()
            if isinstance(v, (int, float))
        }
    }
