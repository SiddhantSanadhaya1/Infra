"""Tests for src/routes/health.py"""
import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check_returns_200(self):
        """Test that health endpoint returns 200 OK."""
        response = client.get("/health")

        assert response.status_code == 200

    def test_health_check_response_structure(self):
        """Test that health endpoint returns correct structure."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "service" in data
        assert "version" in data

    def test_health_check_status_healthy(self):
        """Test that health endpoint reports healthy status."""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"

    def test_health_check_service_name(self):
        """Test that health endpoint includes service name."""
        response = client.get("/health")
        data = response.json()

        assert "InsureCo Insurance Portal API" in data["service"]

    def test_health_check_version(self):
        """Test that health endpoint includes version."""
        response = client.get("/health")
        data = response.json()

        assert data["version"] == "1.0.0"

    def test_health_check_returns_json(self):
        """Test that health endpoint returns JSON."""
        response = client.get("/health")

        assert response.headers["content-type"] == "application/json"

    def test_health_check_multiple_calls(self):
        """Test that health endpoint is consistent across multiple calls."""
        responses = [client.get("/health") for _ in range(3)]

        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    def test_health_check_no_auth_required(self):
        """Test that health endpoint doesn't require authentication."""
        # Should work without any Authorization header
        response = client.get("/health")

        assert response.status_code == 200

    def test_health_check_post_method_not_allowed(self):
        """Test that POST method is not allowed on health endpoint."""
        response = client.post("/health")

        assert response.status_code == 405  # Method Not Allowed

    def test_health_check_put_method_not_allowed(self):
        """Test that PUT method is not allowed on health endpoint."""
        response = client.put("/health")

        assert response.status_code == 405

    def test_health_check_delete_method_not_allowed(self):
        """Test that DELETE method is not allowed on health endpoint."""
        response = client.delete("/health")

        assert response.status_code == 405
