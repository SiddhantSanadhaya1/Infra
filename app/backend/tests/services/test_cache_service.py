"""
Unit tests for src.services.cache_service
Tests Redis caching operations for policies and claims.
"""
import pytest
from unittest.mock import patch, MagicMock
from src.services.cache_service import (
    get_cached_policy,
    set_cached_policy,
    invalidate_policy_cache,
    get_cached_claim_status,
    set_cached_claim_status,
    invalidate_claim_cache,
    POLICY_CACHE_TTL,
    CLAIM_CACHE_TTL,
)


class TestPolicyCaching:
    """Test policy caching operations"""

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_policy_hit(self, mock_cache_get):
        """Test getting a cached policy (cache hit)"""
        mock_policy_data = {
            "id": "policy-123",
            "policy_number": "POL-AUTO-20260330-1234",
            "status": "ACTIVE"
        }
        mock_cache_get.return_value = mock_policy_data

        result = get_cached_policy("policy-123")

        assert result == mock_policy_data
        mock_cache_get.assert_called_once_with("policy:policy-123")

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_policy_miss(self, mock_cache_get):
        """Test getting a cached policy (cache miss)"""
        mock_cache_get.return_value = None

        result = get_cached_policy("policy-456")

        assert result is None
        mock_cache_get.assert_called_once_with("policy:policy-456")

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_policy_empty_id(self, mock_cache_get):
        """Test getting cached policy with empty ID"""
        mock_cache_get.return_value = None

        result = get_cached_policy("")

        assert result is None
        mock_cache_get.assert_called_once_with("policy:")

    @patch('src.services.cache_service.cache_set')
    def test_set_cached_policy(self, mock_cache_set):
        """Test setting a policy in cache"""
        policy_data = {
            "id": "policy-789",
            "policy_number": "POL-HOME-20260330-5678",
            "status": "ACTIVE",
            "premium_amount": "1200.00"
        }

        set_cached_policy("policy-789", policy_data)

        mock_cache_set.assert_called_once_with(
            "policy:policy-789",
            policy_data,
            ttl=POLICY_CACHE_TTL
        )

    @patch('src.services.cache_service.cache_set')
    def test_set_cached_policy_none_data(self, mock_cache_set):
        """Test setting None as policy data"""
        set_cached_policy("policy-001", None)

        mock_cache_set.assert_called_once_with(
            "policy:policy-001",
            None,
            ttl=POLICY_CACHE_TTL
        )

    @patch('src.services.cache_service.cache_set')
    def test_set_cached_policy_empty_dict(self, mock_cache_set):
        """Test setting empty dict as policy data"""
        set_cached_policy("policy-002", {})

        mock_cache_set.assert_called_once_with(
            "policy:policy-002",
            {},
            ttl=POLICY_CACHE_TTL
        )

    @patch('src.services.cache_service.cache_delete')
    def test_invalidate_policy_cache(self, mock_cache_delete):
        """Test invalidating a policy from cache"""
        invalidate_policy_cache("policy-123")

        mock_cache_delete.assert_called_once_with("policy:policy-123")

    @patch('src.services.cache_service.cache_delete')
    def test_invalidate_policy_cache_nonexistent(self, mock_cache_delete):
        """Test invalidating non-existent policy from cache"""
        invalidate_policy_cache("policy-nonexistent")

        mock_cache_delete.assert_called_once_with("policy:policy-nonexistent")

    @patch('src.services.cache_service.cache_delete')
    def test_invalidate_policy_cache_empty_id(self, mock_cache_delete):
        """Test invalidating policy with empty ID"""
        invalidate_policy_cache("")

        mock_cache_delete.assert_called_once_with("policy:")


class TestClaimCaching:
    """Test claim caching operations"""

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_claim_status_hit(self, mock_cache_get):
        """Test getting cached claim status (cache hit)"""
        mock_cache_get.return_value = "UNDER_REVIEW"

        result = get_cached_claim_status("claim-123")

        assert result == "UNDER_REVIEW"
        mock_cache_get.assert_called_once_with("claim_status:claim-123")

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_claim_status_miss(self, mock_cache_get):
        """Test getting cached claim status (cache miss)"""
        mock_cache_get.return_value = None

        result = get_cached_claim_status("claim-456")

        assert result is None
        mock_cache_get.assert_called_once_with("claim_status:claim-456")

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_claim_status_submitted(self, mock_cache_get):
        """Test getting cached claim with SUBMITTED status"""
        mock_cache_get.return_value = "SUBMITTED"

        result = get_cached_claim_status("claim-789")

        assert result == "SUBMITTED"
        mock_cache_get.assert_called_once_with("claim_status:claim-789")

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_claim_status_approved(self, mock_cache_get):
        """Test getting cached claim with APPROVED status"""
        mock_cache_get.return_value = "APPROVED"

        result = get_cached_claim_status("claim-001")

        assert result == "APPROVED"

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_claim_status_rejected(self, mock_cache_get):
        """Test getting cached claim with REJECTED status"""
        mock_cache_get.return_value = "REJECTED"

        result = get_cached_claim_status("claim-002")

        assert result == "REJECTED"

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_claim_status_paid(self, mock_cache_get):
        """Test getting cached claim with PAID status"""
        mock_cache_get.return_value = "PAID"

        result = get_cached_claim_status("claim-003")

        assert result == "PAID"

    @patch('src.services.cache_service.cache_set')
    def test_set_cached_claim_status(self, mock_cache_set):
        """Test setting claim status in cache"""
        set_cached_claim_status("claim-123", "UNDER_REVIEW")

        mock_cache_set.assert_called_once_with(
            "claim_status:claim-123",
            "UNDER_REVIEW",
            ttl=CLAIM_CACHE_TTL
        )

    @patch('src.services.cache_service.cache_set')
    def test_set_cached_claim_status_submitted(self, mock_cache_set):
        """Test setting SUBMITTED claim status"""
        set_cached_claim_status("claim-456", "SUBMITTED")

        mock_cache_set.assert_called_once_with(
            "claim_status:claim-456",
            "SUBMITTED",
            ttl=CLAIM_CACHE_TTL
        )

    @patch('src.services.cache_service.cache_set')
    def test_set_cached_claim_status_approved(self, mock_cache_set):
        """Test setting APPROVED claim status"""
        set_cached_claim_status("claim-789", "APPROVED")

        mock_cache_set.assert_called_once_with(
            "claim_status:claim-789",
            "APPROVED",
            ttl=CLAIM_CACHE_TTL
        )

    @patch('src.services.cache_service.cache_set')
    def test_set_cached_claim_status_empty_status(self, mock_cache_set):
        """Test setting empty string as claim status"""
        set_cached_claim_status("claim-001", "")

        mock_cache_set.assert_called_once_with(
            "claim_status:claim-001",
            "",
            ttl=CLAIM_CACHE_TTL
        )

    @patch('src.services.cache_service.cache_delete')
    def test_invalidate_claim_cache(self, mock_cache_delete):
        """Test invalidating a claim from cache"""
        invalidate_claim_cache("claim-123")

        mock_cache_delete.assert_called_once_with("claim_status:claim-123")

    @patch('src.services.cache_service.cache_delete')
    def test_invalidate_claim_cache_nonexistent(self, mock_cache_delete):
        """Test invalidating non-existent claim from cache"""
        invalidate_claim_cache("claim-nonexistent")

        mock_cache_delete.assert_called_once_with("claim_status:claim-nonexistent")

    @patch('src.services.cache_service.cache_delete')
    def test_invalidate_claim_cache_empty_id(self, mock_cache_delete):
        """Test invalidating claim with empty ID"""
        invalidate_claim_cache("")

        mock_cache_delete.assert_called_once_with("claim_status:")


class TestCacheConstants:
    """Test cache TTL constants"""

    def test_policy_cache_ttl_value(self):
        """Test POLICY_CACHE_TTL has expected value"""
        assert POLICY_CACHE_TTL == 300

    def test_claim_cache_ttl_value(self):
        """Test CLAIM_CACHE_TTL has expected value"""
        assert CLAIM_CACHE_TTL == 300

    def test_ttl_values_are_positive(self):
        """Test TTL values are positive integers"""
        assert POLICY_CACHE_TTL > 0
        assert CLAIM_CACHE_TTL > 0
        assert isinstance(POLICY_CACHE_TTL, int)
        assert isinstance(CLAIM_CACHE_TTL, int)
