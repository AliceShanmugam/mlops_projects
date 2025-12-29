# -*- coding: utf-8 -*-
"""
Created on Mon Dec 29 23:39:14 2025

@author: coach
"""

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
