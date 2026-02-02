"""Tests for the API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


def test_health(client: TestClient) -> None:
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_stats(client: TestClient) -> None:
    """Test stats endpoint."""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "by_type" in data


def test_entity_not_found(client: TestClient) -> None:
    """Test 404 for missing entity."""
    response = client.get("/entity/Q999999999")
    assert response.status_code == 404


def test_search_empty(client: TestClient) -> None:
    """Test search with no results."""
    response = client.get("/search?q=xyznonexistent")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "xyznonexistent"
    assert "results" in data


def test_search_requires_query(client: TestClient) -> None:
    """Test search requires a query parameter."""
    response = client.get("/search")
    assert response.status_code == 422  # Validation error
