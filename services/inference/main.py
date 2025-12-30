from pathlib import Path
import joblib
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

# Chemin vers les modèles montés par Docker
ARTIFACTS_DIR = Path("/models/run_linear_svm2")

tfidf = joblib.load(ARTIFACTS_DIR / "tfidf.joblib")
svm = joblib.load(ARTIFACTS_DIR / "svm.joblib")

app = FastAPI(title="Inference Service")

class PredictRequest(BaseModel):
    text: str

class PredictResponse(BaseModel):
    predicted_label: int
    decision_score: Optional[list[float]] = None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    X = tfidf.transform([req.text])
    pred = svm.predict(X)[0]

    response = {"predicted_label": int(pred)}

    if hasattr(svm, "decision_function"):
        response["decision_score"] = svm.decision_function(X)[0].tolist()

    return response
