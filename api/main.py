from pathlib import Path
import joblib
from fastapi import FastAPI
from pydantic import BaseModel

# =========================
# Load artifacts
# =========================
ARTIFACTS_DIR = Path("models/run_linear_svm")

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
    probabilities: list[float]


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
    proba = svm.predict_proba(X)[0].tolist()

    return {
        "predicted_label": int(pred),
        "probabilities": proba,
    }
