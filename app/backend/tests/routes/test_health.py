"""
Comprehensive unit tests for health check route.
Tests health endpoint response and structure.
"""
import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check_returns_200(self):
        """Test that health check returns 200 OK."""
        response = client.get("/health")

        assert response.status_code == 200

    def test_health_check_returns_json(self):
        """Test that health check returns JSON response."""
        response = client.get("/health")

        assert response.headers["content-type"] == "application/json"

    def test_health_check_includes_status(self):
        """Test that health check includes status field."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_check_includes_service_name(self):
        """Test that health check includes service name."""
        response = client.get("/health")
        data = response.json()

        assert "service" in data
        assert data["service"] == "InsureCo Insurance Portal API"

    def test_health_check_includes_version(self):
        """Test that health check includes version."""
        response = client.get("/health")
        data = response.json()

        assert "version" in data
        assert data["version"] == "1.0.0"

    def test_health_check_response_structure(self):
        """Test complete health check response structure."""
        response = client.get("/health")
        data = response.json()

        expected_keys = {"status", "service", "version"}
        assert set(data.keys()) == expected_keys

    def test_health_check_status_is_healthy(self):
        """Test that status is explicitly 'healthy'."""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"
        assert isinstance(data["status"], str)

    def test_health_check_service_name_not_empty(self):
        """Test that service name is not empty."""
        response = client.get("/health")
        data = response.json()

        assert len(data["service"]) > 0

    def test_health_check_version_format(self):
        """Test that version follows semantic versioning format."""
        response = client.get("/health")
        data = response.json()

        version = data["version"]
        parts = version.split(".")
        assert len(parts) == 3  # Major.Minor.Patch
        assert all(part.isdigit() for part in parts)

    def test_health_check_multiple_calls_consistent(self):
        """Test that multiple health check calls return same response."""
        response1 = client.get("/health")
        response2 = client.get("/health")

        assert response1.status_code == response2.status_code
        assert response1.json() == response2.json()

    def test_health_check_no_authentication_required(self):
        """Test that health check doesn't require authentication."""
        # Health check should work without any auth headers
        response = client.get("/health")

        assert response.status_code == 200

    def test_health_check_with_trailing_slash(self):
        """Test health check endpoint with trailing slash."""
        response = client.get("/health/")

        # FastAPI should handle this
        assert response.status_code in [200, 404, 307]  # 307 is redirect

    def test_health_check_only_get_method(self):
        """Test that only GET method is allowed on health endpoint."""
        response_post = client.post("/health")
        response_put = client.put("/health")
        response_delete = client.delete("/health")

        # All should be method not allowed
        assert response_post.status_code == 405
        assert response_put.status_code == 405
        assert response_delete.status_code == 405

    def test_health_check_case_sensitive_path(self):
        """Test that health check path is case sensitive."""
        response_lower = client.get("/health")
        response_upper = client.get("/Health")

        assert response_lower.status_code == 200
        # Upper case should not match
        assert response_upper.status_code == 404

    def test_health_check_response_time_reasonable(self):
        """Test that health check responds quickly."""
        import time

        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0  # Should respond in less than 1 second
