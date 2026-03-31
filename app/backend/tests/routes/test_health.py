"""
Unit tests for src.routes.health
Tests health check endpoint.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock


class TestHealthCheck:
    """Test health check endpoint"""

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy_status(self):
        """Test health check endpoint returns healthy status"""
        from src.routes.health import health_check

        result = await health_check()

        assert result["status"] == "healthy"
        assert result["service"] == "InsureCo Insurance Portal API"
        assert result["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_health_check_returns_dict(self):
        """Test health check endpoint returns dictionary"""
        from src.routes.health import health_check

        result = await health_check()

        assert isinstance(result, dict)
        assert "status" in result
        assert "service" in result
        assert "version" in result

    @pytest.mark.asyncio
    async def test_health_check_keys_present(self):
        """Test health check endpoint has all expected keys"""
        from src.routes.health import health_check

        result = await health_check()

        expected_keys = {"status", "service", "version"}
        assert set(result.keys()) == expected_keys

    @pytest.mark.asyncio
    async def test_health_check_status_value(self):
        """Test health check status is 'healthy'"""
        from src.routes.health import health_check

        result = await health_check()

        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_service_name(self):
        """Test health check service name is correct"""
        from src.routes.health import health_check

        result = await health_check()

        assert "InsureCo" in result["service"]
        assert "Insurance" in result["service"]

    @pytest.mark.asyncio
    async def test_health_check_version_format(self):
        """Test health check version follows semver format"""
        from src.routes.health import health_check

        result = await health_check()

        version = result["version"]
        assert isinstance(version, str)
        parts = version.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)

    @pytest.mark.asyncio
    async def test_health_check_consistency(self):
        """Test health check returns consistent results"""
        from src.routes.health import health_check

        result1 = await health_check()
        result2 = await health_check()

        assert result1 == result2

    @pytest.mark.asyncio
    async def test_health_check_no_side_effects(self):
        """Test health check has no side effects"""
        from src.routes.health import health_check

        result_before = await health_check()
        result_after = await health_check()

        assert result_before == result_after
