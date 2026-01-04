
# services/gateway/app/main.py
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
import requests

from .auth import authenticate_user, create_access_token, require_admin, require_user
from .schemas import Token, PredictRequest
from .config import TRAINING_SERVICE_URL, INFERENCE_SERVICE_URL

app = FastAPI(
    title="MLOps Secure Gateway",
    description="Gateway sécurisée pour training et inference",
)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# ---------- HEALTH ----------
@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway"}

# ---------- AUTH ----------
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

# ---------- TRAINING (ADMIN) ----------
@app.post("/train/svm")
def train(current_user=Depends(require_admin)):
    response = requests.post(f"{TRAINING_SERVICE_URL}/train/svm", timeout=3600)
    response.raise_for_status()
    return response.json()

# ---------- PREDICT (USER + ADMIN) ----------
@app.post("/predict")
def predict(
    predict_request: PredictRequest,
    current_user=Depends(require_user),
):
    response = requests.post(
        f"{INFERENCE_SERVICE_URL}/predict",
        json=predict_request.dict(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()

