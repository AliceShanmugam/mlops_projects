from fastapi import FastAPI
from pathlib import Path
import mlflow

#from src.models.train_linearsvm import train_and_evaluate_svm
from train_linearsvm import train_and_evaluate_svm

app = FastAPI(title="Training Service")

DATA_PATH = Path("/data/processed/train_clean.csv")
ARTIFACTS_DIR = Path("/models/run_linear_svm2")

@app.post("/train")
def train():
    # Connexion à MLflow (via Docker network)
    mlflow.set_tracking_uri("http://mlflow:5000")
    mlflow.set_experiment("rakuten-linear-svm")

    with mlflow.start_run():
        # Entraînement
        metrics = train_and_evaluate_svm(
            data_path=DATA_PATH,
            artifacts_dir=ARTIFACTS_DIR
        )

        # Log metrics
        mlflow.log_metric("f1_macro", metrics["f1_macro"])

        # Log params (exemple)
        mlflow.log_param("model", "LinearSVC")
        mlflow.log_param("vectorizer", "TF-IDF")

        # Log artefacts
        mlflow.log_artifacts(str(ARTIFACTS_DIR))

    return {
        "status": "training completed",
        "f1_macro": metrics["f1_macro"]
    }
