"""
Functional tests for health endpoint.
"""
import httpx
import pytest


def test_health_check_returns_healthy_status(client: httpx.Client):
    """
    Test that health endpoint returns healthy status.
    """
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "InsureCo Insurance Portal API"
    assert data["version"] == "1.0.0"


def test_health_check_no_authentication_required(client: httpx.Client):
    """
    Test that health endpoint does not require authentication.
    """
    response = client.get("/health")

    assert response.status_code == 200
    assert "status" in response.json()
