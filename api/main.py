from pathlib import Path
import joblib
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

# =========================
# Load artifacts
# =========================
ARTIFACTS_DIR = Path("models/run_linear_svm2")

tfidf = joblib.load(ARTIFACTS_DIR / "tfidf.joblib")
svm = joblib.load(ARTIFACTS_DIR / "svm.joblib")

# =========================
# FastAPI app
# =========================
app = FastAPI(
    title="Rakuten MLOps Inference API",
    description="Minimal FastAPI for product classification",
    version="1.0"
)


# =========================
# Input / Output schemas
# =========================
class PredictRequest(BaseModel):
    text: str


class PredictResponse(BaseModel):
    predicted_label: int
    decision_score: Optional[list[float]] = None
    #probabilities: list[float]


# =========================
# Endpoints
# =========================
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    X = tfidf.transform([request.text])
    pred = svm.predict(X)[0]
    #proba = svm.predict_proba(X)[0].tolist()

    response = {"predicted_label": int(pred)}
    
    if hasattr(svm, "decision_function"):
        scores = svm.decision_function(X)
        response["decision_score"] = scores[0].tolist()

    return response
