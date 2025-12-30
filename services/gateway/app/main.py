# services/gateway/app/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from .auth import (
    authenticate_user,
    create_access_token,
    require_admin,
    require_user,
)
from .schemas import Token

app = FastAPI(
    title="MLOps Secure Gateway",
    version="1.0.0",
)

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

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/train")
def train(current_user=Depends(require_admin)):
    return {"message": "Training authorized"}

@app.post("/predict")
def predict(current_user=Depends(require_user)):
    return {"message": "Prediction authorized"}
