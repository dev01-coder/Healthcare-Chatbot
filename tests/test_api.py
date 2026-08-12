"""Tests for the API endpoints."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_stats():
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data


def test_emergency_check():
    response = client.post(
        "/emergency-check",
        json={"message": "I have a headache"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "emergency" in data
    assert data["emergency"] is None


def test_emergency_check_positive():
    response = client.post(
        "/emergency-check",
        json={"message": "I'm having chest pain"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["emergency"] is not None


def test_chat_message_too_long():
    response = client.post(
        "/chat",
        json={"message": "x" * 2001}
    )
    assert response.status_code == 422  # Validation error


def test_chat_empty_message():
    response = client.post(
        "/chat",
        json={"message": ""}
    )
    assert response.status_code == 422  # Validation error


def test_suggest_empty_query():
    response = client.get("/api/suggest?q=")
    assert response.status_code == 422  # min_length=1 validation


def test_suggest_returns_list():
    response = client.get("/api/suggest?q=what")
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)


if __name__ == "__main__":
    test_root()
    test_health()
    test_stats()
    test_emergency_check()
    test_emergency_check_positive()
    test_chat_message_too_long()
    test_chat_empty_message()
    print("All API tests passed!")
