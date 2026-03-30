import pytest
from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


class TestHealthCheck:
    """Test suite for /health endpoint."""

    def test_health_check_success(self):
        """Test that health check returns 200 OK."""
        response = client.get("/health")

        assert response.status_code == 200

    def test_health_check_response_structure(self):
        """Test that health check response has correct structure."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "service" in data
        assert "version" in data

    def test_health_check_status_healthy(self):
        """Test that health check status is 'healthy'."""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"

    def test_health_check_service_name(self):
        """Test that service name is correct."""
        response = client.get("/health")
        data = response.json()

        assert data["service"] == "InsureCo Insurance Portal API"

    def test_health_check_version(self):
        """Test that version is present."""
        response = client.get("/health")
        data = response.json()

        assert data["version"] == "1.0.0"

    def test_health_check_returns_json(self):
        """Test that health check returns JSON content type."""
        response = client.get("/health")

        assert "application/json" in response.headers["content-type"]

    def test_health_check_no_authentication_required(self):
        """Test that health check does not require authentication."""
        # Health check should work without any auth headers
        response = client.get("/health")

        assert response.status_code == 200

    def test_health_check_multiple_calls(self):
        """Test that health check can be called multiple times."""
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

    def test_health_check_get_method_only(self):
        """Test that only GET method is allowed."""
        # POST should not be allowed
        response = client.post("/health")
        assert response.status_code in [405, 404]  # Method Not Allowed or Not Found

    def test_health_check_response_time(self):
        """Test that health check responds quickly."""
        import time
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0  # Should respond in under 1 second
