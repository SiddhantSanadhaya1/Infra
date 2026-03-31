"""Tests for src/services/cache_service.py"""
import pytest
from unittest.mock import patch

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
    """Test policy caching functions."""

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_policy_hit(self, mock_cache_get):
        """Test successful policy cache retrieval."""
        mock_policy = {"policy_id": "123", "status": "ACTIVE"}
        mock_cache_get.return_value = mock_policy

        result = get_cached_policy("123")

        assert result == mock_policy
        mock_cache_get.assert_called_once_with("policy:123")

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_policy_miss(self, mock_cache_get):
        """Test cache miss returns None."""
        mock_cache_get.return_value = None

        result = get_cached_policy("nonexistent")

        assert result is None
        mock_cache_get.assert_called_once_with("policy:nonexistent")

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_policy_with_uuid(self, mock_cache_get):
        """Test with UUID-format policy ID."""
        policy_id = "550e8400-e29b-41d4-a716-446655440000"
        mock_cache_get.return_value = {"id": policy_id}

        result = get_cached_policy(policy_id)

        mock_cache_get.assert_called_once_with(f"policy:{policy_id}")

    @patch('src.services.cache_service.cache_set')
    def test_set_cached_policy(self, mock_cache_set):
        """Test setting policy in cache."""
        policy_data = {"policy_id": "123", "premium": "1000.00"}
        mock_cache_set.return_value = True

        set_cached_policy("123", policy_data)

        mock_cache_set.assert_called_once_with(
            "policy:123",
            policy_data,
            ttl=POLICY_CACHE_TTL
        )

    @patch('src.services.cache_service.cache_set')
    def test_set_cached_policy_with_none(self, mock_cache_set):
        """Test setting None as policy data."""
        mock_cache_set.return_value = True

        set_cached_policy("123", None)

        mock_cache_set.assert_called_once_with("policy:123", None, ttl=POLICY_CACHE_TTL)

    @patch('src.services.cache_service.cache_set')
    def test_set_cached_policy_with_empty_dict(self, mock_cache_set):
        """Test setting empty dict as policy data."""
        mock_cache_set.return_value = True

        set_cached_policy("123", {})

        mock_cache_set.assert_called_once()

    @patch('src.services.cache_service.cache_delete')
    def test_invalidate_policy_cache(self, mock_cache_delete):
        """Test invalidating policy cache."""
        mock_cache_delete.return_value = True

        invalidate_policy_cache("123")

        mock_cache_delete.assert_called_once_with("policy:123")

    @patch('src.services.cache_service.cache_delete')
    def test_invalidate_policy_cache_nonexistent(self, mock_cache_delete):
        """Test invalidating non-existent policy cache."""
        mock_cache_delete.return_value = False

        invalidate_policy_cache("nonexistent")

        mock_cache_delete.assert_called_once_with("policy:nonexistent")


class TestClaimCaching:
    """Test claim caching functions."""

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_claim_status_hit(self, mock_cache_get):
        """Test successful claim status retrieval."""
        mock_cache_get.return_value = "APPROVED"

        result = get_cached_claim_status("claim-123")

        assert result == "APPROVED"
        mock_cache_get.assert_called_once_with("claim_status:claim-123")

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_claim_status_miss(self, mock_cache_get):
        """Test cache miss returns None."""
        mock_cache_get.return_value = None

        result = get_cached_claim_status("claim-999")

        assert result is None

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_claim_status_various_statuses(self, mock_cache_get):
        """Test retrieving different claim statuses."""
        statuses = ["SUBMITTED", "UNDER_REVIEW", "APPROVED", "REJECTED", "PAID"]

        for status in statuses:
            mock_cache_get.return_value = status
            result = get_cached_claim_status("claim-test")
            assert result == status

    @patch('src.services.cache_service.cache_set')
    def test_set_cached_claim_status(self, mock_cache_set):
        """Test setting claim status in cache."""
        mock_cache_set.return_value = True

        set_cached_claim_status("claim-123", "UNDER_REVIEW")

        mock_cache_set.assert_called_once_with(
            "claim_status:claim-123",
            "UNDER_REVIEW",
            ttl=CLAIM_CACHE_TTL
        )

    @patch('src.services.cache_service.cache_set')
    def test_set_cached_claim_status_all_statuses(self, mock_cache_set):
        """Test setting all possible claim statuses."""
        statuses = ["SUBMITTED", "UNDER_REVIEW", "APPROVED", "REJECTED", "PAID"]
        mock_cache_set.return_value = True

        for status in statuses:
            set_cached_claim_status("claim-test", status)

        assert mock_cache_set.call_count == len(statuses)

    @patch('src.services.cache_service.cache_set')
    def test_set_cached_claim_status_empty_string(self, mock_cache_set):
        """Test setting empty string status."""
        mock_cache_set.return_value = True

        set_cached_claim_status("claim-123", "")

        mock_cache_set.assert_called_once()

    @patch('src.services.cache_service.cache_delete')
    def test_invalidate_claim_cache(self, mock_cache_delete):
        """Test invalidating claim cache."""
        mock_cache_delete.return_value = True

        invalidate_claim_cache("claim-123")

        mock_cache_delete.assert_called_once_with("claim_status:claim-123")

    @patch('src.services.cache_service.cache_delete')
    def test_invalidate_claim_cache_multiple_times(self, mock_cache_delete):
        """Test invalidating same claim multiple times."""
        mock_cache_delete.return_value = True

        invalidate_claim_cache("claim-123")
        invalidate_claim_cache("claim-123")

        assert mock_cache_delete.call_count == 2


class TestCacheTTLConfiguration:
    """Test cache TTL configuration."""

    def test_policy_cache_ttl_value(self):
        """Test that POLICY_CACHE_TTL has expected value."""
        assert POLICY_CACHE_TTL == 300

    def test_claim_cache_ttl_value(self):
        """Test that CLAIM_CACHE_TTL has expected value."""
        assert CLAIM_CACHE_TTL == 300

    @patch('src.services.cache_service.cache_set')
    def test_policy_cache_uses_correct_ttl(self, mock_cache_set):
        """Test that policy caching uses POLICY_CACHE_TTL."""
        mock_cache_set.return_value = True

        set_cached_policy("test", {"data": "test"})

        call_kwargs = mock_cache_set.call_args[1]
        assert call_kwargs['ttl'] == POLICY_CACHE_TTL

    @patch('src.services.cache_service.cache_set')
    def test_claim_cache_uses_correct_ttl(self, mock_cache_set):
        """Test that claim caching uses CLAIM_CACHE_TTL."""
        mock_cache_set.return_value = True

        set_cached_claim_status("test", "APPROVED")

        call_kwargs = mock_cache_set.call_args[1]
        assert call_kwargs['ttl'] == CLAIM_CACHE_TTL
