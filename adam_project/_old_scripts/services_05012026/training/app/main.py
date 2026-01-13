# services/training/app/main.py
from fastapi import FastAPI, HTTPException

from train_linearsvm import train_and_evaluate_svm
from train_cnn import train_cnn

app = FastAPI(title="Training service")


@app.get("/health")
def health():
    return {"status": "ok", "service": "training"}

@app.post("/train/svm")
def train_svm():
    metrics = train_and_evaluate_svm(
        data_path="/data/processed/train_clean.csv",
        artifacts_dir="/models/text"
    )
    return metrics

@app.post("/train/cnn")
def train_cnn_endpoint():
    metrics = train_cnn(
        data_path="/data/processed/train_clean.csv",
        artifacts_dir="/models/images"
    )
    return metrics



