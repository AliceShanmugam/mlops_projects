import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from gateway.gateway_main import app

client = TestClient(app)

# =========================
# HEALTH
# =========================
def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# =========================
# AUTH
# =========================
@patch("httpx.AsyncClient.post")
def test_login(mock_post):
    mock_post.return_value = AsyncMock(
        json=lambda: {"access_token": "fake", "token_type": "bearer"}
    )

    response = client.post(
        "/token",
        data={"username": "test", "password": "test"},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


# =========================
# AUTH HEADER
# =========================
def test_missing_token():
    response = client.post("/predict/text", json={"text": "hello"})
    assert response.status_code == 401


# =========================
# PREDICT TEXT
# =========================
@patch("httpx.AsyncClient.post")
def test_predict_text(mock_post):
    mock_post.return_value = AsyncMock(
        json=lambda: {"prediction": "spam"}
    )

    response = client.post(
        "/predict/text",
        json={"text": "hello"},
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 200
    assert "prediction" in response.json()


# =========================
# PREDICT IMAGE
# =========================
@patch("httpx.AsyncClient.post")
def test_predict_image(mock_post):
    mock_post.return_value = AsyncMock(
        json=lambda: {"prediction": "cat"}
    )

    response = client.post(
        "/predict/image",
        json={"image_path": "img.jpg"},
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 200


# =========================
# TRAIN TEXT
# =========================
@patch("httpx.AsyncClient.post")
def test_train_text(mock_post):
    mock_post.return_value = AsyncMock()

    response = client.post(
        "/train/text",
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 200
    assert response.json()["model"] == "text"


# =========================
# TRAIN IMAGE
# =========================
@patch("httpx.AsyncClient.post")
def test_train_image(mock_post):
    mock_post.return_value = AsyncMock()

    response = client.post(
        "/train/image",
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 200
    assert response.json()["model"] == "image"


# =========================
# RELOAD TEXT
# =========================
@patch("httpx.AsyncClient.post")
def test_reload_text(mock_post):
    mock_post.return_value = AsyncMock(
        json=lambda: {"status": "reloaded"}
    )

    response = client.post(
        "/reload/text",
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 200


# =========================
# INFO
# =========================
@patch("httpx.AsyncClient.get")
def test_info(mock_get):
    mock_get.return_value = AsyncMock(
        json=lambda: {"status": "ok"}
    )

    response = client.get(
        "/info",
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "models" in data


# =========================
# ROOT
# =========================
def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "routes" in response.json()