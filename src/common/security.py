# src/common/security.py
"""
Security utilities: validation, rate limiting, error handling.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field, validator
from typing import Optional, List
import logging
import time
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)

# Rate limiter: 100 requests per minute per IP
limiter = Limiter(key_func=get_remote_address)


@limiter.limit("100/minute")
async def rate_limit_handler(request: Request):
    """Explicit rate limit handler."""
    pass


def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit error response."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Rate limit exceeded",
            "detail": "Too many requests. Maximum 100 requests per minute allowed.",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# ============================================================
# PYDANTIC MODELS WITH VALIDATION
# ============================================================

class PredictTextRequest(BaseModel):
    """Validated text prediction request."""
    text: str = Field(..., min_length=1, max_length=5000, description="Product description text")
    
    @validator("text")
    def text_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be empty or whitespace only")
        return v.strip()


class PredictImageRequest(BaseModel):
    """Validated image prediction request."""
    image_filename: str = Field(..., description="Image filename (no path, only filename)")
    
    @validator("image_filename")
    def validate_filename(cls, v):
        # Only allow alphanumeric, underscore, hyphen, and common extensions
        import re
        if not re.match(r"^[\w\-\.]+\.(jpg|jpeg|png|gif)$", v, re.IGNORECASE):
            raise ValueError("Invalid image filename format")
        return v


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status (ok/degraded/error)")
    service: str = Field(..., description="Service name")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    version: Optional[str] = None
    models_available: Optional[List[str]] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error details")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    request_id: Optional[str] = None


# ============================================================
# DECORATORS FOR LOGGING & METRICS
# ============================================================

def log_request(func):
    """Decorator to log request details."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        request_id = kwargs.get("request_id", "unknown")
        
        try:
            result = await func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "function": func.__name__,
                    "duration_ms": duration_ms,
                    "status": "success",
                }
            )
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "request_id": request_id,
                    "function": func.__name__,
                    "duration_ms": duration_ms,
                    "status": "error",
                    "error": str(e),
                },
                exc_info=True,
            )
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        request_id = kwargs.get("request_id", "unknown")
        
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "function": func.__name__,
                    "duration_ms": duration_ms,
                    "status": "success",
                }
            )
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "request_id": request_id,
                    "function": func.__name__,
                    "duration_ms": duration_ms,
                    "status": "error",
                    "error": str(e),
                },
                exc_info=True,
            )
            raise
    
    # Return async wrapper if function is async, else sync
    if hasattr(func, '__await__'):
        return async_wrapper
    return sync_wrapper
