"""Unit tests for cache service module"""
import pytest
from unittest.mock import patch, MagicMock


class TestGetCachedPolicy:
    """Test get cached policy"""

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_policy_exists(self, mock_cache_get):
        """Test retrieving existing policy from cache"""
        from src.services.cache_service import get_cached_policy

        mock_cache_get.return_value = {"id": "123", "policy_number": "POL-001"}

        result = get_cached_policy("policy-123")

        mock_cache_get.assert_called_once_with("policy:policy-123")
        assert result == {"id": "123", "policy_number": "POL-001"}

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_policy_not_exists(self, mock_cache_get):
        """Test retrieving non-existent policy from cache"""
        from src.services.cache_service import get_cached_policy

        mock_cache_get.return_value = None

        result = get_cached_policy("policy-999")

        mock_cache_get.assert_called_once_with("policy:policy-999")
        assert result is None

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_policy_key_format(self, mock_cache_get):
        """Test correct key format is used"""
        from src.services.cache_service import get_cached_policy

        get_cached_policy("abc-123")

        mock_cache_get.assert_called_once_with("policy:abc-123")


class TestSetCachedPolicy:
    """Test set cached policy"""

    @patch('src.services.cache_service.cache_set')
    def test_set_cached_policy(self, mock_cache_set):
        """Test storing policy in cache"""
        from src.services.cache_service import set_cached_policy, POLICY_CACHE_TTL

        policy_data = {"id": "123", "policy_number": "POL-001"}

        set_cached_policy("policy-123", policy_data)

        mock_cache_set.assert_called_once_with(
            "policy:policy-123",
            policy_data,
            ttl=POLICY_CACHE_TTL
        )

    @patch('src.services.cache_service.cache_set')
    def test_set_cached_policy_uses_ttl_constant(self, mock_cache_set):
        """Test that default TTL constant is used"""
        from src.services.cache_service import set_cached_policy

        set_cached_policy("policy-123", {"data": "test"})

        call_args = mock_cache_set.call_args
        assert call_args[1]["ttl"] == 300  # POLICY_CACHE_TTL


class TestInvalidatePolicyCache:
    """Test invalidate policy cache"""

    @patch('src.services.cache_service.cache_delete')
    def test_invalidate_policy_cache(self, mock_cache_delete):
        """Test invalidating policy cache"""
        from src.services.cache_service import invalidate_policy_cache

        invalidate_policy_cache("policy-123")

        mock_cache_delete.assert_called_once_with("policy:policy-123")

    @patch('src.services.cache_service.cache_delete')
    def test_invalidate_policy_cache_key_format(self, mock_cache_delete):
        """Test correct key format for invalidation"""
        from src.services.cache_service import invalidate_policy_cache

        invalidate_policy_cache("abc-456")

        mock_cache_delete.assert_called_once_with("policy:abc-456")


class TestGetCachedClaimStatus:
    """Test get cached claim status"""

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_claim_status_exists(self, mock_cache_get):
        """Test retrieving existing claim status from cache"""
        from src.services.cache_service import get_cached_claim_status

        mock_cache_get.return_value = "APPROVED"

        result = get_cached_claim_status("claim-123")

        mock_cache_get.assert_called_once_with("claim_status:claim-123")
        assert result == "APPROVED"

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_claim_status_not_exists(self, mock_cache_get):
        """Test retrieving non-existent claim status"""
        from src.services.cache_service import get_cached_claim_status

        mock_cache_get.return_value = None

        result = get_cached_claim_status("claim-999")

        assert result is None

    @patch('src.services.cache_service.cache_get')
    def test_get_cached_claim_status_key_format(self, mock_cache_get):
        """Test correct key format for claim status"""
        from src.services.cache_service import get_cached_claim_status

        get_cached_claim_status("xyz-789")

        mock_cache_get.assert_called_once_with("claim_status:xyz-789")


class TestSetCachedClaimStatus:
    """Test set cached claim status"""

    @patch('src.services.cache_service.cache_set')
    def test_set_cached_claim_status(self, mock_cache_set):
        """Test storing claim status in cache"""
        from src.services.cache_service import set_cached_claim_status, CLAIM_CACHE_TTL

        set_cached_claim_status("claim-123", "UNDER_REVIEW")

        mock_cache_set.assert_called_once_with(
            "claim_status:claim-123",
            "UNDER_REVIEW",
            ttl=CLAIM_CACHE_TTL
        )

    @patch('src.services.cache_service.cache_set')
    def test_set_cached_claim_status_uses_ttl_constant(self, mock_cache_set):
        """Test that default TTL constant is used"""
        from src.services.cache_service import set_cached_claim_status

        set_cached_claim_status("claim-123", "APPROVED")

        call_args = mock_cache_set.call_args
        assert call_args[1]["ttl"] == 300  # CLAIM_CACHE_TTL

    @patch('src.services.cache_service.cache_set')
    def test_set_cached_claim_status_different_statuses(self, mock_cache_set):
        """Test setting different claim statuses"""
        from src.services.cache_service import set_cached_claim_status

        statuses = ["SUBMITTED", "UNDER_REVIEW", "APPROVED", "REJECTED", "PAID"]

        for status in statuses:
            set_cached_claim_status("claim-123", status)

        assert mock_cache_set.call_count == len(statuses)


class TestInvalidateClaimCache:
    """Test invalidate claim cache"""

    @patch('src.services.cache_service.cache_delete')
    def test_invalidate_claim_cache(self, mock_cache_delete):
        """Test invalidating claim status cache"""
        from src.services.cache_service import invalidate_claim_cache

        invalidate_claim_cache("claim-123")

        mock_cache_delete.assert_called_once_with("claim_status:claim-123")

    @patch('src.services.cache_service.cache_delete')
    def test_invalidate_claim_cache_key_format(self, mock_cache_delete):
        """Test correct key format for claim invalidation"""
        from src.services.cache_service import invalidate_claim_cache

        invalidate_claim_cache("abc-789")

        mock_cache_delete.assert_called_once_with("claim_status:abc-789")


class TestCacheTTLConstants:
    """Test cache TTL constants"""

    def test_policy_cache_ttl_value(self):
        """Test POLICY_CACHE_TTL has expected value"""
        from src.services.cache_service import POLICY_CACHE_TTL

        assert POLICY_CACHE_TTL == 300

    def test_claim_cache_ttl_value(self):
        """Test CLAIM_CACHE_TTL has expected value"""
        from src.services.cache_service import CLAIM_CACHE_TTL

        assert CLAIM_CACHE_TTL == 300
