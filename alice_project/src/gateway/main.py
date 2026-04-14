"""
Gateway — point d'entrée unique pour les clients externes.

Responsabilités :
  - Authentification : vérifie la clé API et détermine le rôle
  - Routage : redirige vers le service api (port 8000)
  - Contrôle d'accès : bloque les endpoints admin pour les users

Endpoints exposés (port 8080) → forwarded vers api:8000 :
  GET  /health
  POST /predict             → user + admin
  POST /predict/text        → user + admin
  POST /predict/image       → user + admin
  POST /training/trigger    → admin uniquement
  GET  /training/status/:id → admin uniquement
  GET  /training/logs/:id   → admin uniquement
  POST /models/reload       → admin uniquement
"""

import os
import logging

import requests
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

API_URL   = os.getenv("API_SERVICE_URL", "http://api:8000")
API_KEY   = os.getenv("API_KEY",         "dev-key-insecure")
ADMIN_KEY = os.getenv("ADMIN_API_KEY",   "dev-admin-key-insecure")

# Endpoints accessibles uniquement par un admin
ADMIN_ONLY_PATHS = {
    "/training/trigger",
    "/training/status",
    "/training/logs",
    "/models/reload",
}

app = FastAPI(
    title="Alice MLOps — Gateway",
    description="Point d'entrée unique. Gère l'auth et route vers le service API.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

def _get_role(api_key: str | None) -> str | None:
    """Retourne 'admin', 'user' ou None si clé invalide/absente."""
    if api_key == ADMIN_KEY:
        return "admin"
    if api_key == API_KEY:
        return "user"
    return None

def _is_admin_path(path: str) -> bool:
    return any(path.startswith(p) for p in ADMIN_ONLY_PATHS)


def _proxy(request_method: str, path: str, payload: dict | None,
           api_key: str) -> dict:
    """Forwarder la requête vers api:8000 avec la clé dans le header."""
    url = f"{API_URL}{path}"
    headers = {"X-API-Key": api_key}
    try:
        if request_method == "GET":
            resp = requests.get(url, headers=headers, timeout=30)
        else:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Service API indisponible")
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Service API timeout")
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code,
                            detail=e.response.json().get("detail", str(e)))


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health():
    """Vérifie le gateway ET le service API en aval."""
    try:
        resp = requests.get(f"{API_URL}/health", timeout=5)
        api_status = resp.json().get("status", "unknown")
    except Exception:
        api_status = "unreachable"
    return {"gateway": "healthy", "api": api_status}


# ── Predict ───────────────────────────────────────────────────────────────────

@app.post("/predict", tags=["Predictions"])
async def predict_combined(request: Request):
    """Prédiction combinée texte + image — user et admin."""
    api_key = request.headers.get("X-API-Key")
    role    = _get_role(api_key)
    if not role:
        raise HTTPException(status_code=401, detail="API key invalide ou manquante")
    body = await request.json()
    return _proxy("POST", "/predict", body, api_key)


@app.post("/predict/text", tags=["Predictions"])
async def predict_text(request: Request):
    """Prédiction texte uniquement — user et admin."""
    api_key = request.headers.get("X-API-Key")
    if not _get_role(api_key):
        raise HTTPException(status_code=401, detail="API key invalide ou manquante")
    body = await request.json()
    return _proxy("POST", "/predict/text", body, api_key)


@app.post("/predict/image", tags=["Predictions"])
async def predict_image(request: Request):
    """Prédiction image uniquement — user et admin."""
    api_key = request.headers.get("X-API-Key")
    if not _get_role(api_key):
        raise HTTPException(status_code=401, detail="API key invalide ou manquante")
    body = await request.json()
    return _proxy("POST", "/predict/image", body, api_key)


# ── Training (admin) ──────────────────────────────────────────────────────────

@app.post("/training/trigger", tags=["Admin"])
async def trigger_training(request: Request):
    """Déclenche le pipeline d'entraînement — admin uniquement."""
    api_key = request.headers.get("X-API-Key")
    if _get_role(api_key) != "admin":
        raise HTTPException(status_code=403, detail="Droits administrateur requis")
    body = await request.json() if request.headers.get("content-length", "0") != "0" else {}
    return _proxy("POST", "/training/trigger", body, api_key)


@app.get("/training/status/{dag_run_id}", tags=["Admin"])
def training_status(dag_run_id: str, request: Request):
    """Statut d'un run d'entraînement — admin uniquement."""
    api_key = request.headers.get("X-API-Key")
    if _get_role(api_key) != "admin":
        raise HTTPException(status_code=403, detail="Droits administrateur requis")
    return _proxy("GET", f"/training/status/{dag_run_id}", None, api_key)


@app.get("/training/logs/{dag_run_id}", tags=["Admin"])
def training_logs(dag_run_id: str, request: Request):
    """Logs d'un run d'entraînement — admin uniquement."""
    api_key = request.headers.get("X-API-Key")
    if _get_role(api_key) != "admin":
        raise HTTPException(status_code=403, detail="Droits administrateur requis")
    return _proxy("GET", f"/training/logs/{dag_run_id}", None, api_key)


# ── Admin ─────────────────────────────────────────────────────────────────────

@app.post("/models/reload", tags=["Admin"])
async def reload_models(request: Request):
    """Recharge les modèles en mémoire — admin uniquement."""
    api_key = request.headers.get("X-API-Key")
    if _get_role(api_key) != "admin":
        raise HTTPException(status_code=403, detail="Droits administrateur requis")
    return _proxy("POST", "/models/reload", {}, api_key)