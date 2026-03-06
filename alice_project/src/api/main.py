from fastapi import FastAPI, HTTPException
from schemas import PredictionRequest, PredictionResponse
from model import predict

app = FastAPI(
    title="Text Classification API",
    description="API d'inférence pour la classification de textes (TF-IDF + modèle ML)",
    version="1.0.0"
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictionResponse)
def predict_endpoint(request: PredictionRequest):
    try:
        label = predict(request.text)
        return PredictionResponse(label=label)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))