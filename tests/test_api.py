"""
Unit Tests for FastAPI REST Endpoints and Security.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.auth.security import auth_manager


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "mqtt_broker" in data
    assert "database" in data


def test_auth_and_protected_flow():
    # Login with valid admin credentials
    res = client.post("/api/auth/login", json={"username": "admin", "password": "Admin@2026"})
    assert res.status_code == 200
    token = res.json()["token"]
    assert token

    # Protected alert ack endpoint
    headers = {"Authorization": f"Bearer {token}"}
    ack_res = client.post("/api/alerts/999999/ack", json={"username": "admin"}, headers=headers)
    # Alert 999999 doesn't exist, should return 404
    assert ack_res.status_code == 404

    # Unauthenticated request should fail with 401
    fail_res = client.post("/api/alerts/1/ack", json={"username": "admin"})
    assert fail_res.status_code == 401


def test_model_metrics_endpoint():
    res = client.get("/api/model/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "metrics" in data
    assert "confusion_matrix" in data

