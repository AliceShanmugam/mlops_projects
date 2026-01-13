# services/gateway/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import requests

from gateway.auth import authenticate_user, create_access_token, require_admin, require_user
from gateway.schemas import Token, PredictRequest, PredictImageRequest
from gateway.config import TRAINING_SERVICE_URL, INFERENCE_SERVICE_URL

app = FastAPI(
    title="MLOps Secure Gateway",
    description="Gateway sécurisée pour training et inference",
)

# ======================================================
# HEALTH
# ======================================================
@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway"}


# ======================================================
# AUTH
# ======================================================
@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
        )

    token = create_access_token(
        {"sub": user["username"], "role": user["role"]}
    )

    return {"access_token": token, "token_type": "bearer"}


# ======================================================
# TRAINING (ADMIN ONLY)
# ======================================================
@app.post("/train/svm")
def train_svm(current_user=Depends(require_admin)):
    response = requests.post(
        f"{TRAINING_SERVICE_URL}/train/svm",
        timeout=3600,
    )
    response.raise_for_status()
    return response.json()


@app.post("/train/cnn")
def train_cnn(current_user=Depends(require_admin)):
    response = requests.post(
        f"{TRAINING_SERVICE_URL}/train/cnn",
        timeout=3600,
    )
    response.raise_for_status()
    return response.json()


# ======================================================
# PREDICTION (USER + ADMIN)
# ======================================================
@app.post("/predict/svm")
def predict_svm(
    predict_request: PredictRequest,
    current_user=Depends(require_user),
):
    response = requests.post(
        f"{INFERENCE_SERVICE_URL}/predict/svm",
        json=predict_request.dict(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


@app.post("/predict/cnn")
def predict_cnn(
    predict_request: PredictImageRequest,
    current_user=Depends(require_user),
):
    response = requests.post(
        f"{INFERENCE_SERVICE_URL}/predict/cnn",
        json=predict_request.dict(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
