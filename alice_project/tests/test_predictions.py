"""
Tests des endpoints de prédiction.
"""

import pytest


class TestPredictText:

    def test_returns_label(self, api_client, user_headers, sample_text):
        """Retourne un label entier."""
        resp = api_client.post(
            "/predict/text",
            json={"text": sample_text},
            headers=user_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "label" in data
        assert isinstance(data["label"], int)
        assert 0 <= data["label"] <= 7

    def test_label_in_valid_range(self, api_client, user_headers):
        resp = api_client.post(
            "/predict/text",
            json={"text": "ordinateur portable Dell 15 pouces"},
            headers=user_headers,
        )
        assert resp.status_code == 200
        assert 0 <= resp.json()["label"] <= 7

    def test_source_is_text(self, api_client, user_headers, sample_text):
        resp = api_client.post(
            "/predict/text",
            json={"text": sample_text},
            headers=user_headers,
        )
        assert resp.json()["source"] == "text"

    def test_empty_text_rejected(self, api_client, user_headers):
        """Texte vide → 422 (validation Pydantic)."""
        resp = api_client.post(
            "/predict/text",
            json={"text": ""},
            headers=user_headers,
        )
        assert resp.status_code == 422

    def test_text_too_short_rejected(self, api_client, user_headers):
        resp = api_client.post(
            "/predict/text",
            json={"text": "ab"},
            headers=user_headers,
        )
        assert resp.status_code == 422


class TestPredictImage:

    def test_image_model_unavailable_returns_503(self, api_client, user_headers):
        """Modèle image non disponible → 503."""
        resp = api_client.post(
            "/predict/image",
            json={"image_path": "/app/data/images/test.jpg"},
            headers=user_headers,
        )
        assert resp.status_code == 503


class TestPredictCombined:

    def test_text_only_falls_back_gracefully(self, api_client, user_headers, sample_text):
        """Avec seulement text, image absent → fallback=True si image demandée."""
        resp = api_client.post(
            "/predict",
            json={"text": sample_text},
            headers=user_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "label" in data
        assert data["source"] in ("text", "combined")

    def test_combined_no_input_rejected(self, api_client, user_headers):
        """Ni text ni image → 422."""
        resp = api_client.post(
            "/predict",
            json={},
            headers=user_headers,
        )
        assert resp.status_code == 422

    def test_image_unavailable_fallback_to_text(self, api_client, user_headers, sample_text):
        """Image demandée mais modèle indispo → fallback sur texte, fallback=True."""
        resp = api_client.post(
            "/predict",
            json={"text": sample_text, "image_path": "/app/data/images/test.jpg"},
            headers=user_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["fallback"] is True
        assert data["source"] == "text"