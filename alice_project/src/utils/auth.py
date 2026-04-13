"""
Authentication utilities for API security.

Deux niveaux d'accès :
  - User  : API_KEY       → /predict uniquement
  - Admin : ADMIN_API_KEY → /predict + /training/* + /models/reload
"""

import os

from fastapi import HTTPException, status
from fastapi.security import APIKeyHeader

from config.logging_config import get_logger

logger = get_logger(__name__)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = None) -> bool:
    """Vérifie qu'une clé est valide (user OU admin)."""
    user_key  = os.getenv("API_KEY", "dev-key-insecure")
    admin_key = os.getenv("ADMIN_API_KEY", "dev-admin-key-insecure")

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key manquante",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if api_key not in (user_key, admin_key):
        logger.warning(f"Clé invalide : {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key invalide",
        )

    return True


def verify_admin(api_key: str = None) -> bool:
    """Vérifie que la clé est la clé admin."""
    admin_key = os.getenv("ADMIN_API_KEY", "dev-admin-key-insecure")

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key manquante",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if api_key != admin_key:
        logger.warning(f"Accès admin refusé : {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Droits administrateur requis",
        )

    return True


def get_current_user(api_key: str = None) -> dict:
    """Dependency FastAPI — retourne le rôle de l'utilisateur."""
    user_key  = os.getenv("API_KEY", "dev-key-insecure")
    admin_key = os.getenv("ADMIN_API_KEY", "dev-admin-key-insecure")

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key manquante",
        )

    if api_key == admin_key:
        return {"role": "admin"}
    if api_key == user_key:
        return {"role": "user"}

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="API key invalide",
    )