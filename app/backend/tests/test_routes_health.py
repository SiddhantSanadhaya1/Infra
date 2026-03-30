"""Unit tests for src.routes.health module."""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.routes.health import router


# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check_returns_200(self):
        """Test health check returns 200 status code."""
        response = client.get("/health")

        assert response.status_code == 200

    def test_health_check_returns_healthy_status(self):
        """Test health check returns healthy status."""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"

    def test_health_check_returns_service_name(self):
        """Test health check returns service name."""
        response = client.get("/health")
        data = response.json()

        assert data["service"] == "InsureCo Insurance Portal API"

    def test_health_check_returns_version(self):
        """Test health check returns version number."""
        response = client.get("/health")
        data = response.json()

        assert "version" in data
        assert data["version"] == "1.0.0"

    def test_health_check_response_structure(self):
        """Test health check response has correct structure."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert len(data) == 3

    def test_health_check_content_type(self):
        """Test health check returns JSON content type."""
        response = client.get("/health")

        assert "application/json" in response.headers["content-type"]

    def test_health_check_multiple_calls(self):
        """Test health check endpoint is idempotent."""
        response1 = client.get("/health")
        response2 = client.get("/health")
        response3 = client.get("/health")

        assert response1.json() == response2.json() == response3.json()

    def test_health_check_with_query_params(self):
        """Test health check ignores query parameters."""
        response = client.get("/health?test=param")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_health_check_response_is_dict(self):
        """Test health check response is a dictionary."""
        response = client.get("/health")
        data = response.json()

        assert isinstance(data, dict)
