"""
Comprehensive unit tests for cache_service module.
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
    """Test policy caching operations."""

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_policy_hit(self, mock_get):
        """Test retrieving a cached policy (cache hit)."""
        policy_data = {"id": "123", "policy_number": "POL-001"}
        mock_get.return_value = policy_data

        result = get_cached_policy("policy-123")

        assert result == policy_data
        mock_get.assert_called_once_with("policy:policy-123")

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_policy_miss(self, mock_get):
        """Test retrieving a non-existent policy (cache miss)."""
        mock_get.return_value = None

        result = get_cached_policy("policy-123")

        assert result is None
        mock_get.assert_called_once_with("policy:policy-123")

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_policy_empty_id(self, mock_get):
        """Test getting cached policy with empty ID."""
        mock_get.return_value = None

        result = get_cached_policy("")

        assert result is None
        mock_get.assert_called_once_with("policy:")

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_policy_with_special_characters(self, mock_get):
        """Test policy ID with special characters."""
        mock_get.return_value = {"id": "special-123"}

        result = get_cached_policy("policy-abc-123-def")

        mock_get.assert_called_once_with("policy:policy-abc-123-def")

    @patch("src.services.cache_service.cache_set")
    def test_set_cached_policy_success(self, mock_set):
        """Test storing a policy in cache."""
        policy_data = {"id": "123", "policy_number": "POL-001"}

        set_cached_policy("policy-123", policy_data)

        mock_set.assert_called_once_with("policy:policy-123", policy_data, ttl=POLICY_CACHE_TTL)

    @patch("src.services.cache_service.cache_set")
    def test_set_cached_policy_uses_correct_ttl(self, mock_set):
        """Test that policy cache uses POLICY_CACHE_TTL."""
        policy_data = {"id": "123"}

        set_cached_policy("policy-123", policy_data)

        call_args = mock_set.call_args
        assert call_args[1]["ttl"] == 300  # POLICY_CACHE_TTL

    @patch("src.services.cache_service.cache_set")
    def test_set_cached_policy_empty_data(self, mock_set):
        """Test storing empty policy data."""
        set_cached_policy("policy-123", {})

        mock_set.assert_called_once_with("policy:policy-123", {}, ttl=POLICY_CACHE_TTL)

    @patch("src.services.cache_service.cache_set")
    def test_set_cached_policy_none_value(self, mock_set):
        """Test storing None as policy data."""
        set_cached_policy("policy-123", None)

        mock_set.assert_called_once_with("policy:policy-123", None, ttl=POLICY_CACHE_TTL)

    @patch("src.services.cache_service.cache_set")
    def test_set_cached_policy_complex_data(self, mock_set):
        """Test storing complex nested policy data."""
        policy_data = {
            "id": "123",
            "policyholder": {"name": "John", "email": "john@example.com"},
            "claims": [{"id": "1"}, {"id": "2"}],
        }

        set_cached_policy("policy-123", policy_data)

        mock_set.assert_called_once_with("policy:policy-123", policy_data, ttl=POLICY_CACHE_TTL)

    @patch("src.services.cache_service.cache_delete")
    def test_invalidate_policy_cache_success(self, mock_delete):
        """Test invalidating a policy from cache."""
        invalidate_policy_cache("policy-123")

        mock_delete.assert_called_once_with("policy:policy-123")

    @patch("src.services.cache_service.cache_delete")
    def test_invalidate_policy_cache_empty_id(self, mock_delete):
        """Test invalidating cache with empty policy ID."""
        invalidate_policy_cache("")

        mock_delete.assert_called_once_with("policy:")

    @patch("src.services.cache_service.cache_delete")
    def test_invalidate_policy_cache_multiple_calls(self, mock_delete):
        """Test multiple cache invalidation calls."""
        invalidate_policy_cache("policy-1")
        invalidate_policy_cache("policy-2")

        assert mock_delete.call_count == 2


class TestClaimStatusCaching:
    """Test claim status caching operations."""

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_claim_status_hit(self, mock_get):
        """Test retrieving cached claim status (cache hit)."""
        mock_get.return_value = "APPROVED"

        result = get_cached_claim_status("claim-123")

        assert result == "APPROVED"
        mock_get.assert_called_once_with("claim_status:claim-123")

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_claim_status_miss(self, mock_get):
        """Test retrieving non-existent claim status (cache miss)."""
        mock_get.return_value = None

        result = get_cached_claim_status("claim-123")

        assert result is None
        mock_get.assert_called_once_with("claim_status:claim-123")

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_claim_status_empty_id(self, mock_get):
        """Test getting claim status with empty ID."""
        mock_get.return_value = None

        result = get_cached_claim_status("")

        assert result is None
        mock_get.assert_called_once_with("claim_status:")

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_claim_status_different_statuses(self, mock_get):
        """Test retrieving different claim status values."""
        statuses = ["SUBMITTED", "UNDER_REVIEW", "APPROVED", "REJECTED", "PAID"]
        for status in statuses:
            mock_get.return_value = status
            result = get_cached_claim_status("claim-123")
            assert result == status

    @patch("src.services.cache_service.cache_set")
    def test_set_cached_claim_status_success(self, mock_set):
        """Test storing claim status in cache."""
        set_cached_claim_status("claim-123", "APPROVED")

        mock_set.assert_called_once_with("claim_status:claim-123", "APPROVED", ttl=CLAIM_CACHE_TTL)

    @patch("src.services.cache_service.cache_set")
    def test_set_cached_claim_status_uses_correct_ttl(self, mock_set):
        """Test that claim status cache uses CLAIM_CACHE_TTL."""
        set_cached_claim_status("claim-123", "SUBMITTED")

        call_args = mock_set.call_args
        assert call_args[1]["ttl"] == 300  # CLAIM_CACHE_TTL

    @patch("src.services.cache_service.cache_set")
    def test_set_cached_claim_status_empty_status(self, mock_set):
        """Test storing empty string as status."""
        set_cached_claim_status("claim-123", "")

        mock_set.assert_called_once_with("claim_status:claim-123", "", ttl=CLAIM_CACHE_TTL)

    @patch("src.services.cache_service.cache_set")
    def test_set_cached_claim_status_all_valid_statuses(self, mock_set):
        """Test storing all valid claim statuses."""
        statuses = ["SUBMITTED", "UNDER_REVIEW", "APPROVED", "REJECTED", "PAID"]
        for status in statuses:
            set_cached_claim_status("claim-123", status)

        assert mock_set.call_count == len(statuses)

    @patch("src.services.cache_service.cache_delete")
    def test_invalidate_claim_cache_success(self, mock_delete):
        """Test invalidating claim status from cache."""
        invalidate_claim_cache("claim-123")

        mock_delete.assert_called_once_with("claim_status:claim-123")

    @patch("src.services.cache_service.cache_delete")
    def test_invalidate_claim_cache_empty_id(self, mock_delete):
        """Test invalidating cache with empty claim ID."""
        invalidate_claim_cache("")

        mock_delete.assert_called_once_with("claim_status:")

    @patch("src.services.cache_service.cache_delete")
    def test_invalidate_claim_cache_multiple_calls(self, mock_delete):
        """Test multiple cache invalidation calls for claims."""
        invalidate_claim_cache("claim-1")
        invalidate_claim_cache("claim-2")
        invalidate_claim_cache("claim-3")

        assert mock_delete.call_count == 3


class TestCacheTTLValues:
    """Test that TTL constants are correctly defined."""

    def test_policy_cache_ttl_is_300(self):
        """Test that POLICY_CACHE_TTL is 300 seconds (5 minutes)."""
        assert POLICY_CACHE_TTL == 300

    def test_claim_cache_ttl_is_300(self):
        """Test that CLAIM_CACHE_TTL is 300 seconds (5 minutes)."""
        assert CLAIM_CACHE_TTL == 300

    def test_ttl_values_are_positive(self):
        """Test that all TTL values are positive."""
        assert POLICY_CACHE_TTL > 0
        assert CLAIM_CACHE_TTL > 0


class TestCacheKeyFormatting:
    """Test cache key formatting patterns."""

    @patch("src.services.cache_service.cache_get")
    def test_policy_key_format(self, mock_get):
        """Test that policy keys follow 'policy:' prefix pattern."""
        mock_get.return_value = None

        get_cached_policy("test-id")

        call_key = mock_get.call_args[0][0]
        assert call_key.startswith("policy:")

    @patch("src.services.cache_service.cache_get")
    def test_claim_status_key_format(self, mock_get):
        """Test that claim status keys follow 'claim_status:' prefix pattern."""
        mock_get.return_value = None

        get_cached_claim_status("test-id")

        call_key = mock_get.call_args[0][0]
        assert call_key.startswith("claim_status:")

    @patch("src.services.cache_service.cache_set")
    def test_policy_and_claim_keys_are_distinct(self, mock_set):
        """Test that policy and claim keys use different prefixes."""
        set_cached_policy("123", {})
        policy_key = mock_set.call_args[0][0]

        set_cached_claim_status("123", "APPROVED")
        claim_key = mock_set.call_args[0][0]

        assert policy_key != claim_key
        assert "policy:" in policy_key
        assert "claim_status:" in claim_key
