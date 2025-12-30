# services/training/app/main.py
from fastapi import FastAPI, HTTPException
from .pipelines.cnn import train_cnn
from .pipelines.multimodal import train_multimodal
from fastapi import FastAPI
from .pipelines.svm import run_svm_training

app = FastAPI(title="Training Service")

@app.post("/train/svm")
def train_svm():
    return run_svm_training()


@app.get("/health")
def health():
    return {"status": "ok"}



