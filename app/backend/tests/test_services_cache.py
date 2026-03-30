"""Unit tests for src.services.cache_service module."""
from unittest.mock import patch, MagicMock

import pytest

from src.services.cache_service import (
    get_cached_policy,
    set_cached_policy,
    invalidate_policy_cache,
    get_cached_claim_status,
    set_cached_claim_status,
    invalidate_claim_cache,
)


class TestPolicyCaching:
    """Test policy caching operations."""

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_policy_hit(self, mock_cache_get):
        """Test retrieving a policy from cache (cache hit)."""
        mock_cache_get.return_value = {
            "id": "policy-123",
            "status": "ACTIVE",
            "premium": "1000.00",
        }

        result = get_cached_policy("policy-123")

        mock_cache_get.assert_called_once_with("policy:policy-123")
        assert result == {"id": "policy-123", "status": "ACTIVE", "premium": "1000.00"}

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_policy_miss(self, mock_cache_get):
        """Test cache miss returns None."""
        mock_cache_get.return_value = None

        result = get_cached_policy("nonexistent-policy")

        mock_cache_get.assert_called_once_with("policy:nonexistent-policy")
        assert result is None

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_policy_empty_string_id(self, mock_cache_get):
        """Test caching with empty string policy ID."""
        mock_cache_get.return_value = None

        result = get_cached_policy("")

        mock_cache_get.assert_called_once_with("policy:")
        assert result is None

    @patch("src.services.cache_service.cache_set")
    def test_set_cached_policy(self, mock_cache_set):
        """Test storing a policy in cache."""
        mock_cache_set.return_value = True

        policy_data = {"id": "policy-456", "status": "ACTIVE"}
        set_cached_policy("policy-456", policy_data)

        mock_cache_set.assert_called_once_with(
            "policy:policy-456", policy_data, ttl=300
        )

    @patch("src.services.cache_service.cache_set")
    def test_set_cached_policy_with_complex_data(self, mock_cache_set):
        """Test storing complex policy data in cache."""
        mock_cache_set.return_value = True

        policy_data = {
            "id": "policy-789",
            "status": "EXPIRED",
            "premium": 2500.50,
            "claims": [{"id": "claim-1"}, {"id": "claim-2"}],
        }
        set_cached_policy("policy-789", policy_data)

        mock_cache_set.assert_called_once_with(
            "policy:policy-789", policy_data, ttl=300
        )

    @patch("src.services.cache_service.cache_delete")
    def test_invalidate_policy_cache(self, mock_cache_delete):
        """Test invalidating policy cache."""
        mock_cache_delete.return_value = True

        invalidate_policy_cache("policy-123")

        mock_cache_delete.assert_called_once_with("policy:policy-123")

    @patch("src.services.cache_service.cache_delete")
    def test_invalidate_policy_cache_nonexistent(self, mock_cache_delete):
        """Test invalidating cache for nonexistent policy."""
        mock_cache_delete.return_value = True

        invalidate_policy_cache("nonexistent-policy")

        mock_cache_delete.assert_called_once_with("policy:nonexistent-policy")


class TestClaimCaching:
    """Test claim caching operations."""

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_claim_status_hit(self, mock_cache_get):
        """Test retrieving claim status from cache (cache hit)."""
        mock_cache_get.return_value = "APPROVED"

        result = get_cached_claim_status("claim-123")

        mock_cache_get.assert_called_once_with("claim_status:claim-123")
        assert result == "APPROVED"

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_claim_status_miss(self, mock_cache_get):
        """Test cache miss for claim status returns None."""
        mock_cache_get.return_value = None

        result = get_cached_claim_status("nonexistent-claim")

        mock_cache_get.assert_called_once_with("claim_status:nonexistent-claim")
        assert result is None

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_claim_status_submitted(self, mock_cache_get):
        """Test retrieving SUBMITTED claim status."""
        mock_cache_get.return_value = "SUBMITTED"

        result = get_cached_claim_status("claim-456")

        assert result == "SUBMITTED"

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_claim_status_under_review(self, mock_cache_get):
        """Test retrieving UNDER_REVIEW claim status."""
        mock_cache_get.return_value = "UNDER_REVIEW"

        result = get_cached_claim_status("claim-789")

        assert result == "UNDER_REVIEW"

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_claim_status_rejected(self, mock_cache_get):
        """Test retrieving REJECTED claim status."""
        mock_cache_get.return_value = "REJECTED"

        result = get_cached_claim_status("claim-999")

        assert result == "REJECTED"

    @patch("src.services.cache_service.cache_set")
    def test_set_cached_claim_status(self, mock_cache_set):
        """Test storing claim status in cache."""
        mock_cache_set.return_value = True

        set_cached_claim_status("claim-123", "PAID")

        mock_cache_set.assert_called_once_with(
            "claim_status:claim-123", "PAID", ttl=300
        )

    @patch("src.services.cache_service.cache_set")
    def test_set_cached_claim_status_various_statuses(self, mock_cache_set):
        """Test storing different claim statuses."""
        mock_cache_set.return_value = True

        statuses = ["SUBMITTED", "UNDER_REVIEW", "APPROVED", "REJECTED", "PAID"]

        for status in statuses:
            set_cached_claim_status(f"claim-{status}", status)

        assert mock_cache_set.call_count == len(statuses)

    @patch("src.services.cache_service.cache_delete")
    def test_invalidate_claim_cache(self, mock_cache_delete):
        """Test invalidating claim cache."""
        mock_cache_delete.return_value = True

        invalidate_claim_cache("claim-123")

        mock_cache_delete.assert_called_once_with("claim_status:claim-123")

    @patch("src.services.cache_service.cache_delete")
    def test_invalidate_claim_cache_nonexistent(self, mock_cache_delete):
        """Test invalidating cache for nonexistent claim."""
        mock_cache_delete.return_value = True

        invalidate_claim_cache("nonexistent-claim")

        mock_cache_delete.assert_called_once_with("claim_status:nonexistent-claim")


class TestCacheTTL:
    """Test cache TTL configuration."""

    @patch("src.services.cache_service.cache_set")
    def test_policy_cache_ttl_is_300_seconds(self, mock_cache_set):
        """Test policy cache uses 300 second TTL."""
        mock_cache_set.return_value = True

        set_cached_policy("policy-123", {"data": "test"})

        call_args = mock_cache_set.call_args
        assert call_args[1]["ttl"] == 300

    @patch("src.services.cache_service.cache_set")
    def test_claim_cache_ttl_is_300_seconds(self, mock_cache_set):
        """Test claim cache uses 300 second TTL."""
        mock_cache_set.return_value = True

        set_cached_claim_status("claim-123", "APPROVED")

        call_args = mock_cache_set.call_args
        assert call_args[1]["ttl"] == 300


class TestCacheKeyFormat:
    """Test cache key formatting."""

    @patch("src.services.cache_service.cache_get")
    def test_policy_cache_key_format(self, mock_cache_get):
        """Test policy cache key format is 'policy:{id}'."""
        mock_cache_get.return_value = None

        get_cached_policy("test-policy-id")

        mock_cache_get.assert_called_once_with("policy:test-policy-id")

    @patch("src.services.cache_service.cache_get")
    def test_claim_cache_key_format(self, mock_cache_get):
        """Test claim cache key format is 'claim_status:{id}'."""
        mock_cache_get.return_value = None

        get_cached_claim_status("test-claim-id")

        mock_cache_get.assert_called_once_with("claim_status:test-claim-id")

    @patch("src.services.cache_service.cache_delete")
    def test_policy_invalidation_key_format(self, mock_cache_delete):
        """Test policy invalidation uses correct key format."""
        mock_cache_delete.return_value = True

        invalidate_policy_cache("test-policy-id")

        mock_cache_delete.assert_called_once_with("policy:test-policy-id")

    @patch("src.services.cache_service.cache_delete")
    def test_claim_invalidation_key_format(self, mock_cache_delete):
        """Test claim invalidation uses correct key format."""
        mock_cache_delete.return_value = True

        invalidate_claim_cache("test-claim-id")

        mock_cache_delete.assert_called_once_with("claim_status:test-claim-id")
