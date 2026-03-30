import pytest
from unittest.mock import patch, Mock

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


class TestPolicyCacheFunctions:
    """Test suite for policy cache functions."""

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_policy_hit(self, mock_cache_get):
        """Test retrieving a policy from cache (cache hit)."""
        policy_data = {"id": "policy-123", "status": "ACTIVE"}
        mock_cache_get.return_value = policy_data

        result = get_cached_policy("policy-123")

        assert result == policy_data
        mock_cache_get.assert_called_once_with("policy:policy-123")

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_policy_miss(self, mock_cache_get):
        """Test cache miss returns None."""
        mock_cache_get.return_value = None

        result = get_cached_policy("policy-456")

        assert result is None
        mock_cache_get.assert_called_once_with("policy:policy-456")

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_policy_key_format(self, mock_cache_get):
        """Test that correct cache key format is used."""
        mock_cache_get.return_value = None
        policy_id = "test-policy-789"

        get_cached_policy(policy_id)

        mock_cache_get.assert_called_once_with(f"policy:{policy_id}")

    @patch("src.services.cache_service.cache_set")
    def test_set_cached_policy_success(self, mock_cache_set):
        """Test storing a policy in cache."""
        policy_data = {"id": "policy-123", "status": "ACTIVE"}
        mock_cache_set.return_value = True

        set_cached_policy("policy-123", policy_data)

        mock_cache_set.assert_called_once_with(
            "policy:policy-123",
            policy_data,
            ttl=POLICY_CACHE_TTL
        )

    @patch("src.services.cache_service.cache_set")
    def test_set_cached_policy_ttl(self, mock_cache_set):
        """Test that correct TTL is used for policy cache."""
        policy_data = {"id": "policy-123"}

        set_cached_policy("policy-123", policy_data)

        call_args = mock_cache_set.call_args
        assert call_args[1]["ttl"] == 300  # POLICY_CACHE_TTL

    @patch("src.services.cache_service.cache_set")
    def test_set_cached_policy_various_data(self, mock_cache_set):
        """Test caching various policy data structures."""
        policy_data = {
            "id": "policy-123",
            "status": "ACTIVE",
            "coverage": 100000,
            "holder": {"name": "John Doe"}
        }

        set_cached_policy("policy-123", policy_data)

        mock_cache_set.assert_called_once()
        assert mock_cache_set.call_args[0][1] == policy_data

    @patch("src.services.cache_service.cache_delete")
    def test_invalidate_policy_cache_success(self, mock_cache_delete):
        """Test invalidating policy cache."""
        mock_cache_delete.return_value = True

        invalidate_policy_cache("policy-123")

        mock_cache_delete.assert_called_once_with("policy:policy-123")

    @patch("src.services.cache_service.cache_delete")
    def test_invalidate_policy_cache_key_format(self, mock_cache_delete):
        """Test that correct cache key is used for invalidation."""
        policy_id = "test-policy-xyz"

        invalidate_policy_cache(policy_id)

        mock_cache_delete.assert_called_once_with(f"policy:{policy_id}")

    @pytest.mark.parametrize("policy_id", [
        "policy-123",
        "abc-def-ghi",
        "12345",
        "policy_with_underscores",
    ])
    @patch("src.services.cache_service.cache_get")
    def test_get_cached_policy_various_ids(self, mock_cache_get, policy_id):
        """Test getting cached policy with various ID formats."""
        mock_cache_get.return_value = {"id": policy_id}

        get_cached_policy(policy_id)

        mock_cache_get.assert_called_once_with(f"policy:{policy_id}")


class TestClaimCacheFunctions:
    """Test suite for claim cache functions."""

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_claim_status_hit(self, mock_cache_get):
        """Test retrieving claim status from cache (cache hit)."""
        mock_cache_get.return_value = "APPROVED"

        result = get_cached_claim_status("claim-123")

        assert result == "APPROVED"
        mock_cache_get.assert_called_once_with("claim_status:claim-123")

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_claim_status_miss(self, mock_cache_get):
        """Test cache miss returns None."""
        mock_cache_get.return_value = None

        result = get_cached_claim_status("claim-456")

        assert result is None
        mock_cache_get.assert_called_once_with("claim_status:claim-456")

    @patch("src.services.cache_service.cache_get")
    def test_get_cached_claim_status_key_format(self, mock_cache_get):
        """Test that correct cache key format is used."""
        mock_cache_get.return_value = None
        claim_id = "test-claim-789"

        get_cached_claim_status(claim_id)

        mock_cache_get.assert_called_once_with(f"claim_status:{claim_id}")

    @patch("src.services.cache_service.cache_set")
    def test_set_cached_claim_status_success(self, mock_cache_set):
        """Test storing claim status in cache."""
        mock_cache_set.return_value = True

        set_cached_claim_status("claim-123", "UNDER_REVIEW")

        mock_cache_set.assert_called_once_with(
            "claim_status:claim-123",
            "UNDER_REVIEW",
            ttl=CLAIM_CACHE_TTL
        )

    @patch("src.services.cache_service.cache_set")
    def test_set_cached_claim_status_ttl(self, mock_cache_set):
        """Test that correct TTL is used for claim status cache."""
        set_cached_claim_status("claim-123", "APPROVED")

        call_args = mock_cache_set.call_args
        assert call_args[1]["ttl"] == 300  # CLAIM_CACHE_TTL

    @patch("src.services.cache_service.cache_set")
    @pytest.mark.parametrize("status", [
        "SUBMITTED",
        "UNDER_REVIEW",
        "APPROVED",
        "REJECTED",
        "PAID",
    ])
    def test_set_cached_claim_status_various_statuses(
        self, mock_cache_set, status
    ):
        """Test caching various claim statuses."""
        set_cached_claim_status("claim-123", status)

        mock_cache_set.assert_called_once()
        assert mock_cache_set.call_args[0][1] == status

    @patch("src.services.cache_service.cache_delete")
    def test_invalidate_claim_cache_success(self, mock_cache_delete):
        """Test invalidating claim cache."""
        mock_cache_delete.return_value = True

        invalidate_claim_cache("claim-123")

        mock_cache_delete.assert_called_once_with("claim_status:claim-123")

    @patch("src.services.cache_service.cache_delete")
    def test_invalidate_claim_cache_key_format(self, mock_cache_delete):
        """Test that correct cache key is used for invalidation."""
        claim_id = "test-claim-xyz"

        invalidate_claim_cache(claim_id)

        mock_cache_delete.assert_called_once_with(f"claim_status:{claim_id}")

    @pytest.mark.parametrize("claim_id", [
        "claim-123",
        "xyz-abc-def",
        "99999",
        "claim_with_underscores",
    ])
    @patch("src.services.cache_service.cache_get")
    def test_get_cached_claim_status_various_ids(
        self, mock_cache_get, claim_id
    ):
        """Test getting cached claim status with various ID formats."""
        mock_cache_get.return_value = "SUBMITTED"

        get_cached_claim_status(claim_id)

        mock_cache_get.assert_called_once_with(f"claim_status:{claim_id}")


class TestCacheTTLConstants:
    """Test suite for cache TTL constants."""

    def test_policy_cache_ttl_value(self):
        """Test that POLICY_CACHE_TTL has expected value."""
        assert POLICY_CACHE_TTL == 300

    def test_claim_cache_ttl_value(self):
        """Test that CLAIM_CACHE_TTL has expected value."""
        assert CLAIM_CACHE_TTL == 300

    def test_ttl_values_are_integers(self):
        """Test that TTL values are integers."""
        assert isinstance(POLICY_CACHE_TTL, int)
        assert isinstance(CLAIM_CACHE_TTL, int)

    def test_ttl_values_are_positive(self):
        """Test that TTL values are positive."""
        assert POLICY_CACHE_TTL > 0
        assert CLAIM_CACHE_TTL > 0
