"""
FastAPI application with logging, authentication, and rate limiting
"""

import time
import uuid
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from src.api.airflow_service import airflow_client

from config.logging_config import get_logger
from config.settings import settings
from src.api.schemas import (
    PredictionRequest, 
    PredictionResponse, 
    ErrorResponse,
    HealthResponse
)
from src.api.model import predict
from src.utils.auth import verify_api_key
from src.utils.exceptions import PredictionError, AuthenticationError

from src.utils.auth import verify_api_key, verify_admin, API_KEY_HEADER
import src.api.model as model

# Setup logging
logger = get_logger(__name__)

# Initialize app
app = FastAPI(
    title="Alice MLOps - Text Classification API",
    description="API d'inférence pour la classification de textes (TF-IDF + SVM)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Middleware for request logging and tracking
@app.middleware("http")
async def log_requests(request, call_next):
    """
    Log all incoming requests and responses
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown",
        }
    )
    
    # Call next middleware/route
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(
            f"Request failed: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response
    logger.info(
        f"Response: {response.status_code} ({process_time:.3f}s)",
        extra={
            "request_id": request_id,
            "status_code": response.status_code,
            "process_time_ms": process_time * 1000,
        }
    )
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    return response


# Exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    """Handle rate limit exceeded"""
    logger.warning(f"Rate limit exceeded for {request.client.host}")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": "Rate limit exceeded"}
    )


# Routes

@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """
    Health check endpoint - no authentication required
    """
    logger.info("Health check called")
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION
    )


@app.post(
    "/predict",
    response_model=PredictionResponse,
    tags=["Predictions"],
    responses={
        400: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    }
)
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
def predict_endpoint(request:Request, prediction_request: PredictionRequest):
    """
    Predict label for input text
    
    No authentication required
    """
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        logger.info(
            "Prediction request received",
            extra={
                "request_id": request_id,
                "text_length": len(prediction_request.text)
            }
        )
        
        # Get prediction
        label = predict(prediction_request.text)
        
        logger.info(
            "Prediction successful",
            extra={
                "request_id": request_id,
                "predicted_label": label
            }
        )
        
        return PredictionResponse(label=label)
    
    except PredictionError as e:
        logger.error(
            f"Prediction error: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# ============================================================================
# TRAINING ENDPOINTS
# ============================================================================

@app.post(
    "/training/trigger",
    tags=["Training"],
    responses={
        202: {"description": "Training pipeline triggered"},
        400: {"description": "Invalid request"},
        500: {"description": "Internal server error"},
    }
)
def trigger_training(request: Request):
    """
    Trigger training pipeline asynchronously via Airflow
    
    Returns:
        dag_run_id for tracking progress
    """
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        logger.info(
            "🚀 Training triggered",
            extra={"request_id": request_id}
        )
        
        # Trigger Airflow DAG
        result = airflow_client.trigger_dag(
            dag_id='training_pipeline',
            conf={'triggered_by': 'api', 'request_id': request_id}
        )
        
        dag_run_id = result.get('dag_run_id')
        
        logger.info(
            "✅ Training pipeline started",
            extra={"request_id": request_id, "dag_run_id": dag_run_id}
        )
        
        return {
            "status": "triggered",
            "dag_run_id": dag_run_id,
            "message": f"Training pipeline started. Monitor at: http://localhost:8081/dags/training_pipeline/grid"
        }
    
    except Exception as e:
        logger.error(
            f"❌ Failed to trigger training: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger training: {str(e)}"
        )


@app.get(
    "/training/status/{dag_run_id}",
    tags=["Training"],
)
def get_training_status(dag_run_id: str, request: Request):
    """
    Get status of a training run
    
    Args:
        dag_run_id: DAG run ID from trigger response
    
    Returns:
        Status: running, success, failed, queued
    """
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        logger.info(
            f"🔍 Checking training status",
            extra={"request_id": request_id, "dag_run_id": dag_run_id}
        )
        
        result = airflow_client.get_dag_run_status(
            dag_id='training_pipeline',
            dag_run_id=dag_run_id
        )
        
        state = result.get('state', 'unknown')
        
        return {
            "dag_run_id": dag_run_id,
            "status": state,
            "start_date": result.get('start_date'),
            "end_date": result.get('end_date'),
            "dashboard_url": f"http://localhost:8081/dags/training_pipeline/grid?dag_run_id={dag_run_id}"
        }
    
    except Exception as e:
        logger.error(
            f"❌ Failed to get training status: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get training status: {str(e)}"
        )


@app.get(
    "/training/logs/{dag_run_id}",
    tags=["Training"],
)
def get_training_logs(dag_run_id: str, task_id: str = "train_model", request: Request = None):
    """
    Get logs from a training run task
    
    Args:
        dag_run_id: DAG run ID
        task_id: Task ID (default: train_model)
    
    Returns:
        Task execution logs
    """
    request_id = request.headers.get("X-Request-ID", "unknown") if request else "unknown"
    
    try:
        logger.info(
            f"📜 Fetching logs",
            extra={"request_id": request_id, "dag_run_id": dag_run_id, "task_id": task_id}
        )
        
        logs = airflow_client.get_task_instance_logs(
            dag_id='training_pipeline',
            dag_run_id=dag_run_id,
            task_id=task_id
        )
        
        return {"logs": logs}
    
    except Exception as e:
        logger.error(
            f"❌ Failed to get logs: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get logs: {str(e)}"
        )
    
@app.on_event("startup")
async def startup_event():
    """Called when application starts"""
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started")
    logger.info(f"API Key authentication: {'✓ Enabled' if settings.API_KEY != 'dev-key-insecure' else '⚠ DEV MODE'}")


@app.on_event("shutdown")
async def shutdown_event():
    """Called when application stops"""
    logger.info("🛑 Application shutting down")

@app.post("/models/reload", tags=["Admin"])
def reload_models_endpoint(api_key: str = Depends(API_KEY_HEADER)):
    """Recharge les modèles en mémoire après un entraînement — admin uniquement."""
    verify_admin(api_key)       # rôle admin requis
    model.reload_models()
    logger.info("✅ Modèles rechargés via endpoint admin")
    return {"status": "reloaded"}