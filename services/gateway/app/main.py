# services/gateway/app/main.py
import time
import requests
from fastapi import FastAPI, Depends, HTTPException, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from slowapi.errors import RateLimitExceeded

from .auth import authenticate_user, create_access_token, require_admin, require_user
from .schemas import Token, PredictRequest
from .config import TRAINING_SERVICE_URL, INFERENCE_SERVICE_URL
from .middleware import (
    LoggingMiddleware,
    SecurityHeadersMiddleware,
    limiter,
    rate_limit_handler,
    logger,
)

# ---------------- METRICS ----------------
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"]
)

PREDICTION_COUNT = Counter(
    "predictions_total",
    "Total predictions",
    ["status"]
)

TRAINING_COUNT = Counter(
    "trainings_total",
    "Total training jobs",
    ["status"]
)

# ---------------- APP ----------------
app = FastAPI(
    title="MLOps Secure Gateway",
    version="1.0.0",
    description="Secure API Gateway with OAuth2, JWT, rate limiting and metrics",
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# ---------------- METRICS MIDDLEWARE ----------------
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    return response

# ---------------- HEALTH ----------------
@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# ---------------- AUTH ----------------
@app.post("/token", response_model=Token)
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    logger.info("login_attempt", username=form_data.username)

    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning("login_failed", username=form_data.username)
        raise HTTPException(status_code=401, detail="Incorrect credentials")

    token = create_access_token(
        {"sub": user["username"], "role": user["role"]}
    )

    logger.info(
        "login_success",
        username=user["username"],
        role=user["role"]
    )

    return {"access_token": token, "token_type": "bearer"}

# ---------------- TRAINING (ADMIN) ----------------
@app.post("/train/svm")
def train(
    request: Request,
    current_user=Depends(require_admin)
):
    logger.info("training_requested", user=current_user["username"])

    try:
        response = requests.post(
            f"{TRAINING_SERVICE_URL}/train/svm",
            timeout=3600,
        )
        response.raise_for_status()

        TRAINING_COUNT.labels(status="success").inc()
        return response.json()

    except requests.exceptions.RequestException as e:
        TRAINING_COUNT.labels(status="error").inc()
        logger.error("training_failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Training service unavailable"
        )

# ---------------- PREDICT (USER + ADMIN) ----------------

@app.post("/predict")
def predict(
    predict_request: PredictRequest,
    current_user=Depends(require_user),
):
    if not predict_request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    logger.info(
        "prediction_requested",
        user=current_user["username"]
    )

    try:
        response = requests.post(
            f"{INFERENCE_SERVICE_URL}/predict",
            json={"text": predict_request.text},
            timeout=30,
        )
        response.raise_for_status()

        PREDICTION_COUNT.labels(status="success").inc()
        return response.json()

    except requests.exceptions.Timeout:
        PREDICTION_COUNT.labels(status="timeout").inc()
        raise HTTPException(504, "Inference timeout")

    except requests.exceptions.RequestException:
        PREDICTION_COUNT.labels(status="error").inc()
        raise HTTPException(
            status_code=503,
            detail="Inference service unavailable"
        )
