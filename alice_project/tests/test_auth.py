"""
Tests d'authentification et d'autorisation.
Vérifie que les rôles user/admin sont correctement appliqués.
"""

import pytest


class TestAuthentication:

    def test_health_no_auth_required(self, api_client):
        """Health check accessible sans clé."""
        resp = api_client.get("/health")
        assert resp.status_code == 200

    def test_predict_text_valid_user_key(self, api_client, user_headers, sample_text):
        """User peut appeler /predict/text."""
        resp = api_client.post(
            "/predict/text",
            json={"text": sample_text},
            headers=user_headers,
        )
        assert resp.status_code == 200

    def test_predict_text_valid_admin_key(self, api_client, admin_headers, sample_text):
        """Admin peut aussi appeler /predict/text."""
        resp = api_client.post(
            "/predict/text",
            json={"text": sample_text},
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_predict_text_missing_key(self, api_client, no_headers, sample_text):
        """Sans clé → 401."""
        resp = api_client.post(
            "/predict/text",
            json={"text": sample_text},
            headers=no_headers,
        )
        assert resp.status_code == 401

    def test_predict_text_invalid_key(self, api_client, sample_text):
        """Clé invalide → 403."""
        resp = api_client.post(
            "/predict/text",
            json={"text": sample_text},
            headers={"X-API-Key": "invalid-key"},
        )
        assert resp.status_code == 403


class TestAuthorization:

    def test_training_trigger_user_forbidden(self, api_client, user_headers):
        """User ne peut pas déclencher un entraînement → 403."""
        resp = api_client.post("/training/trigger", headers=user_headers)
        assert resp.status_code == 403

    def test_training_trigger_admin_allowed(self, api_client, admin_headers):
        """Admin peut déclencher un entraînement (même si Airflow indispo → 500/503)."""
        resp = api_client.post("/training/trigger", headers=admin_headers)
        assert resp.status_code in (200, 202, 500, 503)

    def test_models_reload_user_forbidden(self, api_client, user_headers):
        """User ne peut pas recharger les modèles → 403."""
        resp = api_client.post("/models/reload", headers=user_headers)
        assert resp.status_code == 403

    def test_models_reload_admin_allowed(self, api_client, admin_headers):
        """Admin peut recharger les modèles."""
        resp = api_client.post("/models/reload", headers=admin_headers)
        assert resp.status_code == 200

    def test_training_status_user_forbidden(self, api_client, user_headers):
        """User ne peut pas voir le statut d'entraînement → 403."""
        resp = api_client.get("/training/status/some-run-id", headers=user_headers)
        assert resp.status_code == 403