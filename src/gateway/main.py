# src/gateway/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import requests
import logging
import uvicorn

from src.gateway.auth import (
    authenticate_user,
    create_access_token,
    require_admin,
    require_user,
)
from src.gateway.schemas import Token, PredictRequest, PredictImageRequest
from src.gateway.config import TRAINING_SERVICE_URL, INFERENCE_SERVICE_URL

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

    token = create_access_token({"sub": user["username"], "role": user["role"]})

    return {"access_token": token, "token_type": "bearer"}


# ======================================================
# TRAINING (ADMIN ONLY)
# ======================================================

logger = logging.getLogger(__name__)


@app.post("/train/svm", status_code=status.HTTP_202_ACCEPTED)
def train_svm(current_user=Depends(require_admin)):
    try:
        requests.post(
            f"{TRAINING_SERVICE_URL}/train/svm",
            timeout=5,  # juste le temps de déclencher
        )
        return {
            "status": "training_started",
            "model": "svm",
        }
    except requests.RequestException as e:
        logger.error(f"SVM training trigger failed: {e}")
        raise HTTPException(
            status_code=502,
            detail="Training service unavailable",
        )


@app.post("/train/cnn", status_code=status.HTTP_202_ACCEPTED)
def train_cnn(current_user=Depends(require_admin)):
    try:
        requests.post(
            f"{TRAINING_SERVICE_URL}/train/cnn",
            timeout=5,
        )
        return {
            "status": "training_started",
            "model": "cnn",
        }
    except requests.RequestException as e:
        logger.error(f"CNN training trigger failed: {e}")
        raise HTTPException(
            status_code=502,
            detail="Training service unavailable",
        )


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


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
