


from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_endpoint():
    payload = {
        "text": "console de jeu portable nintendo"
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert "predicted_label" in data

    assert isinstance(data["predicted_label"], int)


    # optionnel
    if "decision_score" in data:
        assert isinstance(data["decision_score"], list)