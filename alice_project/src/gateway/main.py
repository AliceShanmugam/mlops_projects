from fastapi import FastAPI
import requests

app = FastAPI()

PREDICT_SERVICE = "http://api:8000"
TRAINING_SERVICE = "http://training:8001"

@app.post("/predict")
def predict(payload: dict):
    response = requests.post(f"{PREDICT_SERVICE}/predict", json=payload)
    return response.json()

@app.post("/train")
def train():
    response = requests.post(f"{TRAINING_SERVICE}/train")
    return response.json()
