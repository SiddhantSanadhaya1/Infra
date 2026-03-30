"""
Comprehensive unit tests for redis_config module.
Tests Redis client initialization and cache operations.
"""
import pytest
import json
from unittest.mock import patch, MagicMock

from src.config.redis_config import (
    get_redis_client,
    cache_get,
    cache_set,
    cache_delete,
    REDIS_URL,
)


class TestGetRedisClient:
    """Test Redis client initialization and singleton pattern."""

    @patch("src.config.redis_config.redis.from_url")
    def test_get_redis_client_creates_client(self, mock_from_url):
        """Test that get_redis_client creates a Redis client."""
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        # Reset the global client
        import src.config.redis_config
        src.config.redis_config._redis_client = None

        client = get_redis_client()

        assert client == mock_client
        mock_from_url.assert_called_once_with(REDIS_URL, decode_responses=True)

    @patch("src.config.redis_config.redis.from_url")
    def test_get_redis_client_singleton_pattern(self, mock_from_url):
        """Test that get_redis_client returns same instance on multiple calls."""
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        # Reset the global client
        import src.config.redis_config
        src.config.redis_config._redis_client = None

        client1 = get_redis_client()
        client2 = get_redis_client()

        assert client1 is client2
        # from_url should only be called once due to singleton
        assert mock_from_url.call_count == 1

    @patch("src.config.redis_config.redis.from_url")
    def test_get_redis_client_uses_decode_responses(self, mock_from_url):
        """Test that client is created with decode_responses=True."""
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        import src.config.redis_config
        src.config.redis_config._redis_client = None

        get_redis_client()

        call_args = mock_from_url.call_args
        assert call_args[1]["decode_responses"] is True


class TestCacheGet:
    """Test cache_get functionality."""

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_get_returns_parsed_json(self, mock_get_client):
        """Test that cache_get returns parsed JSON data."""
        mock_client = MagicMock()
        mock_client.get.return_value = '{"key": "value", "number": 42}'
        mock_get_client.return_value = mock_client

        result = cache_get("test-key")

        assert result == {"key": "value", "number": 42}
        mock_client.get.assert_called_once_with("test-key")

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_get_returns_none_when_key_not_found(self, mock_get_client):
        """Test that cache_get returns None when key doesn't exist."""
        mock_client = MagicMock()
        mock_client.get.return_value = None
        mock_get_client.return_value = mock_client

        result = cache_get("nonexistent-key")

        assert result is None

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_get_handles_exception_gracefully(self, mock_get_client):
        """Test that cache_get returns None on Redis exception."""
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Redis connection error")
        mock_get_client.return_value = mock_client

        result = cache_get("test-key")

        assert result is None

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_get_parses_array(self, mock_get_client):
        """Test that cache_get correctly parses JSON arrays."""
        mock_client = MagicMock()
        mock_client.get.return_value = '[1, 2, 3, 4, 5]'
        mock_get_client.return_value = mock_client

        result = cache_get("array-key")

        assert result == [1, 2, 3, 4, 5]

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_get_parses_string(self, mock_get_client):
        """Test that cache_get correctly parses JSON strings."""
        mock_client = MagicMock()
        mock_client.get.return_value = '"simple string"'
        mock_get_client.return_value = mock_client

        result = cache_get("string-key")

        assert result == "simple string"

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_get_parses_boolean(self, mock_get_client):
        """Test that cache_get correctly parses JSON booleans."""
        mock_client = MagicMock()
        mock_client.get.return_value = 'true'
        mock_get_client.return_value = mock_client

        result = cache_get("bool-key")

        assert result is True

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_get_parses_null(self, mock_get_client):
        """Test that cache_get correctly handles JSON null."""
        mock_client = MagicMock()
        mock_client.get.return_value = 'null'
        mock_get_client.return_value = mock_client

        result = cache_get("null-key")

        assert result is None

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_get_handles_invalid_json(self, mock_get_client):
        """Test that cache_get returns None for invalid JSON."""
        mock_client = MagicMock()
        mock_client.get.return_value = 'not valid json {'
        mock_get_client.return_value = mock_client

        result = cache_get("invalid-key")

        assert result is None

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_get_empty_string(self, mock_get_client):
        """Test cache_get with empty string key."""
        mock_client = MagicMock()
        mock_client.get.return_value = None
        mock_get_client.return_value = mock_client

        result = cache_get("")

        assert result is None
        mock_client.get.assert_called_once_with("")


class TestCacheSet:
    """Test cache_set functionality."""

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_set_stores_data(self, mock_get_client):
        """Test that cache_set stores data as JSON."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_set("test-key", {"data": "value"}, ttl=300)

        assert result is True
        mock_client.setex.assert_called_once()
        call_args = mock_client.setex.call_args[0]
        assert call_args[0] == "test-key"
        assert call_args[1] == 300
        assert json.loads(call_args[2]) == {"data": "value"}

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_set_default_ttl(self, mock_get_client):
        """Test that cache_set uses default TTL of 300 seconds."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        cache_set("test-key", {"data": "value"})

        call_args = mock_client.setex.call_args[0]
        assert call_args[1] == 300

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_set_custom_ttl(self, mock_get_client):
        """Test cache_set with custom TTL."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        cache_set("test-key", {"data": "value"}, ttl=600)

        call_args = mock_client.setex.call_args[0]
        assert call_args[1] == 600

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_set_handles_exception(self, mock_get_client):
        """Test that cache_set returns False on exception."""
        mock_client = MagicMock()
        mock_client.setex.side_effect = Exception("Redis error")
        mock_get_client.return_value = mock_client

        result = cache_set("test-key", {"data": "value"})

        assert result is False

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_set_serializes_complex_objects(self, mock_get_client):
        """Test that cache_set serializes complex nested objects."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        data = {
            "nested": {"key": "value"},
            "array": [1, 2, 3],
            "boolean": True,
            "null": None,
        }

        cache_set("complex-key", data)

        call_args = mock_client.setex.call_args[0]
        serialized = json.loads(call_args[2])
        assert serialized == data

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_set_handles_datetime_with_default_str(self, mock_get_client):
        """Test that cache_set uses default=str for non-serializable objects."""
        from datetime import datetime
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        data = {"timestamp": datetime(2026, 3, 30, 12, 0, 0)}

        cache_set("datetime-key", data)

        call_args = mock_client.setex.call_args[0]
        # Should be serialized as string using default=str
        serialized = call_args[2]
        assert "2026-03-30" in serialized

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_set_empty_dict(self, mock_get_client):
        """Test cache_set with empty dictionary."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_set("empty-key", {})

        assert result is True
        call_args = mock_client.setex.call_args[0]
        assert json.loads(call_args[2]) == {}

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_set_none_value(self, mock_get_client):
        """Test cache_set with None value."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_set("null-key", None)

        assert result is True
        call_args = mock_client.setex.call_args[0]
        assert json.loads(call_args[2]) is None

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_set_minimum_ttl(self, mock_get_client):
        """Test cache_set with minimum TTL value."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        cache_set("test-key", {"data": "value"}, ttl=1)

        call_args = mock_client.setex.call_args[0]
        assert call_args[1] == 1

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_set_large_ttl(self, mock_get_client):
        """Test cache_set with large TTL value."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        cache_set("test-key", {"data": "value"}, ttl=86400)  # 1 day

        call_args = mock_client.setex.call_args[0]
        assert call_args[1] == 86400


class TestCacheDelete:
    """Test cache_delete functionality."""

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_delete_success(self, mock_get_client):
        """Test that cache_delete deletes a key."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_delete("test-key")

        assert result is True
        mock_client.delete.assert_called_once_with("test-key")

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_delete_handles_exception(self, mock_get_client):
        """Test that cache_delete returns False on exception."""
        mock_client = MagicMock()
        mock_client.delete.side_effect = Exception("Redis error")
        mock_get_client.return_value = mock_client

        result = cache_delete("test-key")

        assert result is False

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_delete_empty_key(self, mock_get_client):
        """Test cache_delete with empty string key."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_delete("")

        assert result is True
        mock_client.delete.assert_called_once_with("")

    @patch("src.config.redis_config.get_redis_client")
    def test_cache_delete_nonexistent_key(self, mock_get_client):
        """Test deleting a key that doesn't exist."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_delete("nonexistent-key")

        assert result is True
        mock_client.delete.assert_called_once_with("nonexistent-key")


class TestRedisConstants:
    """Test Redis configuration constants."""

    def test_redis_url_defined(self):
        """Test that REDIS_URL is defined."""
        assert REDIS_URL is not None
        assert isinstance(REDIS_URL, str)

    def test_redis_url_format(self):
        """Test that REDIS_URL has expected format."""
        assert REDIS_URL.startswith("redis://")
