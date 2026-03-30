"""Unit tests for src.config.redis_config module."""
import json
from unittest.mock import MagicMock, patch

import pytest

from src.config.redis_config import (
    get_redis_client,
    cache_get,
    cache_set,
    cache_delete,
)


class TestRedisConfig:
    """Test Redis configuration and operations."""

    @patch("src.config.redis_config.redis")
    def test_get_redis_client_creates_new_client(self, mock_redis):
        """Test Redis client is created on first call."""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client

        # Reset the global client
        import src.config.redis_config as redis_config

        redis_config._redis_client = None

        client = get_redis_client()

        mock_redis.from_url.assert_called_once_with(
            "redis://localhost:6379/0", decode_responses=True
        )
        assert client == mock_client

    @patch("src.config.redis_config.redis")
    def test_get_redis_client_reuses_existing_client(self, mock_redis):
        """Test Redis client is reused on subsequent calls."""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client

        import src.config.redis_config as redis_config

        redis_config._redis_client = mock_client

        client = get_redis_client()

        # Should not create a new client
        mock_redis.from_url.assert_not_called()
        assert client == mock_client

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_get_returns_json_decoded_value(self, mock_get_client):
        """Test cache_get returns JSON-decoded value."""
        mock_client = MagicMock()
        mock_client.get.return_value = '{"key": "value", "number": 42}'
        mock_get_client.return_value = mock_client

        result = cache_get("test_key")

        mock_client.get.assert_called_once_with("test_key")
        assert result == {"key": "value", "number": 42}

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_get_returns_none_when_key_not_found(self, mock_get_client):
        """Test cache_get returns None when key doesn't exist."""
        mock_client = MagicMock()
        mock_client.get.return_value = None
        mock_get_client.return_value = mock_client

        result = cache_get("nonexistent_key")

        mock_client.get.assert_called_once_with("nonexistent_key")
        assert result is None

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_get_handles_exception(self, mock_get_client):
        """Test cache_get returns None on exception."""
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Redis connection error")
        mock_get_client.return_value = mock_client

        result = cache_get("test_key")

        assert result is None

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_get_handles_invalid_json(self, mock_get_client):
        """Test cache_get handles invalid JSON gracefully."""
        mock_client = MagicMock()
        mock_client.get.return_value = "invalid json {"
        mock_get_client.return_value = mock_client

        result = cache_get("test_key")

        # Should catch json.JSONDecodeError and return None
        assert result is None

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_set_stores_json_encoded_value(self, mock_get_client):
        """Test cache_set stores JSON-encoded value with TTL."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        test_data = {"policy_id": "123", "status": "ACTIVE"}
        result = cache_set("policy:123", test_data, ttl=600)

        mock_client.setex.assert_called_once_with(
            "policy:123", 600, json.dumps(test_data, default=str)
        )
        assert result is True

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_set_uses_default_ttl(self, mock_get_client):
        """Test cache_set uses default TTL of 300 seconds."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_set("test_key", {"data": "value"})

        mock_client.setex.assert_called_once()
        call_args = mock_client.setex.call_args
        assert call_args[0][1] == 300  # Default TTL

        assert result is True

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_set_handles_exception(self, mock_get_client):
        """Test cache_set returns False on exception."""
        mock_client = MagicMock()
        mock_client.setex.side_effect = Exception("Redis write error")
        mock_get_client.return_value = mock_client

        result = cache_set("test_key", {"data": "value"})

        assert result is False

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_set_serializes_datetime(self, mock_get_client):
        """Test cache_set handles datetime objects with default=str."""
        from datetime import datetime

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        test_data = {"timestamp": datetime(2026, 3, 30, 12, 0, 0)}
        result = cache_set("test_key", test_data)

        # Should serialize datetime to string
        mock_client.setex.assert_called_once()
        call_args = mock_client.setex.call_args
        stored_value = call_args[0][2]
        assert "2026-03-30" in stored_value
        assert result is True

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_delete_removes_key(self, mock_get_client):
        """Test cache_delete removes key from Redis."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_delete("test_key")

        mock_client.delete.assert_called_once_with("test_key")
        assert result is True

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_delete_handles_exception(self, mock_get_client):
        """Test cache_delete returns False on exception."""
        mock_client = MagicMock()
        mock_client.delete.side_effect = Exception("Redis delete error")
        mock_get_client.return_value = mock_client

        result = cache_delete("test_key")

        assert result is False

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_operations_with_empty_string_key(self, mock_get_client):
        """Test cache operations handle empty string key."""
        mock_client = MagicMock()
        mock_client.get.return_value = None
        mock_get_client.return_value = mock_client

        # Empty key should still work
        result = cache_get("")
        assert result is None

        result = cache_set("", {"data": "value"})
        assert result is True

        result = cache_delete("")
        assert result is True
