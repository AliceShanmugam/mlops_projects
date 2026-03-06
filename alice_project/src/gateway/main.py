from fastapi import FastAPI
import requests

app = FastAPI()

PREDICT_SERVICE = "http://api:8000"
AIRFLOW_URL = "http://airflow:8080"

@app.post("/predict")
def predict(payload: dict):
    response = requests.post(f"{PREDICT_SERVICE}/predict", json=payload)
    return response.json()

@app.post("/train")
def trigger_training():

    response = requests.post(
        f"{AIRFLOW_URL}/api/v1/dags/training_pipeline/dagRuns",
        json={"conf": {"data_version": "latest"}},
        auth=("airflow", "airflow")  # si auth activée
    )

    return response.json()