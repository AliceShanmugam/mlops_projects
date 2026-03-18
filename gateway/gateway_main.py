#gateway.gateway_main.py

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import httpx
import os

# =========================
# CONFIG SERVICES
# =========================
PREDICT_API_URL = os.getenv("PREDICT_API_URL", "http://predict-api:8001")
TRAIN_API_URL = os.getenv("TRAIN_API_URL", "http://airflow-api:8002")
AUTH_API_URL = os.getenv("AUTH_API_URL", "http://auth-api:8003")

# =========================
# FASTAPI INIT
# =========================
app = FastAPI(
    title="MLOps API Gateway",
    description="Gateway multi-modèles (text + image)",
    version="3.0.0",
)

# =========================
# SCHEMAS
# =========================
class PredictTextRequest(BaseModel):
    text: str

class PredictImageRequest(BaseModel):
    image_path: str

# =========================
# AUTH HELPERS
# =========================
async def get_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    return authorization

# =========================
# HEALTH
# =========================
@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway"}

# =========================
# AUTH ROUTES
# =========================
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AUTH_API_URL}/token",
                data={
                    "username": form_data.username,
                    "password": form_data.password,
                },
            )
        return response.json()
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Auth service unavailable")


@app.get("/me")
async def me(authorization: str = Depends(get_token)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{AUTH_API_URL}/me",
            headers={"Authorization": authorization},
        )
    return response.json()

# =========================
# PREDICTION ROUTES
# =========================
@app.post("/predict/text")
async def predict_text(
    request: PredictTextRequest,
    authorization: str = Depends(get_token),
):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PREDICT_API_URL}/predict/svm",
            json=request.dict(),
            headers={"Authorization": authorization},
        )
    return response.json()


@app.post("/predict/image")
async def predict_image(
    request: PredictImageRequest,
    authorization: str = Depends(get_token),
):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PREDICT_API_URL}/predict/cnn",
            json=request.dict(),
            headers={"Authorization": authorization},
        )
    return response.json()

# =========================
# TRAINING ROUTES
# =========================
@app.post("/train/text")
async def train_text(authorization: str = Depends(get_token)):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{TRAIN_API_URL}/train/svm",
                headers={"Authorization": authorization},
                timeout=10.0,
            )
        return {"status": "training_started", "model": "text"}
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Training service unavailable")


@app.post("/train/image")
async def train_image(authorization: str = Depends(get_token)):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{TRAIN_API_URL}/train/cnn",
                headers={"Authorization": authorization},
                timeout=10.0,
            )
        return {"status": "training_started", "model": "image"}
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Training service unavailable")

# =========================
# MODEL RELOAD ROUTES
# =========================
@app.post("/reload/text")
async def reload_text_model(authorization: str = Depends(get_token)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PREDICT_API_URL}/reload/text",
                headers={"Authorization": authorization},
            )
        return response.json()
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Predict service unavailable")


@app.post("/reload/image")
async def reload_image_model(authorization: str = Depends(get_token)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PREDICT_API_URL}/reload/image",
                headers={"Authorization": authorization},
            )
        return response.json()
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Predict service unavailable")

# =========================
# INFO (MULTI-MODELS)
# =========================
@app.get("/info")
async def get_info(authorization: str = Depends(get_token)):
    try:
        async with httpx.AsyncClient() as client:
            predict_health = await client.get(
                f"{PREDICT_API_URL}/health",
                headers={"Authorization": authorization},
            )

            text_info = await client.get(
                f"{PREDICT_API_URL}/info/text",
                headers={"Authorization": authorization},
            )

            image_info = await client.get(
                f"{PREDICT_API_URL}/info/image",
                headers={"Authorization": authorization},
            )

            train_health = await client.get(
                f"{TRAIN_API_URL}/health",
                headers={"Authorization": authorization},
            )

        return {
            "gateway": "ok",
            "predict_api": predict_health.json(),
            "training_api": train_health.json(),
            "models": {
                "text_model": text_info.json(),
                "image_model": image_info.json(),
            },
        }

    except Exception:
        raise HTTPException(status_code=500, detail="Error fetching services info")

# =========================
# ROOT
# =========================
@app.get("/")
async def root():
    return {
        "message": "MLOps Gateway (multi-model)",
        "routes": {
            "auth": "/token",
            "predict": {
                "text": "/predict/text",
                "image": "/predict/image",
            },
            "train": {
                "text": "/train/text",
                "image": "/train/image",
            },
            "reload": {
                "text": "/reload/text",
                "image": "/reload/image",
            },
            "info": "/info",
        },
    }

# =========================
# RUN
# =========================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "gateway_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )