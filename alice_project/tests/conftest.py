"""
Fixtures partagées pour tous les tests.
Utilise des mocks pour ne dépendre d'aucun service externe.
"""

import os
import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from scipy.sparse import csr_matrix

# Variables d'environnement pour les tests (avant tout import applicatif)
os.environ.setdefault("API_KEY",             "test-user-key")
os.environ.setdefault("ADMIN_API_KEY",       "test-admin-key")
os.environ.setdefault("MODELS_PATH",         "models")
os.environ.setdefault("DATA_RAW_DIR",        "data/raw")
os.environ.setdefault("DATA_PROCESSED_DIR",  "data/processed")
os.environ.setdefault("MLFLOW_TRACKING_URI", "")
os.environ.setdefault("AIRFLOW_WEBSERVER_URL", "http://localhost:8080")


# ── Modèles mockés ────────────────────────────────────────────────────────────

@pytest.fixture
def mock_tfidf():
    tfidf = MagicMock()
    tfidf.transform.return_value = csr_matrix(np.array([[0.1, 0.5, 0.3]]))
    return tfidf


@pytest.fixture
def mock_svm():
    svm = MagicMock()
    svm.predict.return_value = np.array([3])
    return svm


@pytest.fixture
def api_client(mock_tfidf, mock_svm):
    """Client FastAPI avec modèles mockés — pas besoin de vrais .joblib."""
    with patch("src.api.model.tfidf_vectorizer", mock_tfidf), \
         patch("src.api.model.svm_model",        mock_svm), \
         patch("src.api.model.TEXT_MODEL_OK",    True), \
         patch("src.api.model.IMAGE_MODEL_OK",   False):
        from src.api.main import app
        yield TestClient(app)


@pytest.fixture
def user_headers():
    return {"X-API-Key": "test-user-key"}


@pytest.fixture
def admin_headers():
    return {"X-API-Key": "test-admin-key"}


@pytest.fixture
def no_headers():
    return {}


# ── Données de test ───────────────────────────────────────────────────────────

@pytest.fixture
def sample_text():
    return "Chaussures de sport Nike homme taille 42"


@pytest.fixture
def sample_df():
    import pandas as pd
    return pd.DataFrame({
        "designation":  ["Chaussures Nike", "Livre Python", "Table basse"],
        "description":  ["Sport running", "Programmation", "Meuble salon"],
        "productid":    [1, 2, 3],
        "imageid":      [10, 20, 30],
        "prdtypecode":  [40, 2705, 1560],
        "text":         ["chaussures nike", "livre python", "table basse"],
    })