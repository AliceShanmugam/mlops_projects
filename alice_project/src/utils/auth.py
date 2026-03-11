"""
Authentication utilities for API security
"""

from fastapi import HTTPException, status
from fastapi.security import APIKeyHeader
import os
from config.logging_config import get_logger
from src.utils.exceptions import AuthenticationError


logger = get_logger(__name__)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = None) -> bool:
    """
    Verify API key from request header
    
    Args:
        api_key: API key from request header
    
    Returns:
        True if valid, raises HTTPException otherwise
    
    Raises:
        HTTPException: If API key is missing or invalid
    """
    valid_key = os.getenv("API_KEY", "dev-key-insecure")
    
    if not api_key:
        logger.warning("Request without API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if api_key != valid_key:
        logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    
    return True


def get_current_user(api_key: str = None) -> dict:
    """
    Dependency for FastAPI to validate API key
    
    Usage:
        @app.get("/protected")
        def protected_endpoint(user: dict = Depends(get_current_user)):
            return {"user": user}
    """
    verify_api_key(api_key)
    return {"api_key": api_key[:5] + "..."}