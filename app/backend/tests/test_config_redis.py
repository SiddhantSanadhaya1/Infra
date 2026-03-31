"""Tests for src/config/redis_config.py"""
import pytest
import json
from unittest.mock import MagicMock, patch
from src.config.redis_config import (
    get_redis_client,
    cache_get,
    cache_set,
    cache_delete,
)


class TestGetRedisClient:
    """Test get_redis_client function."""

    @patch('src.config.redis_config.redis.from_url')
    def test_get_redis_client_creates_new_client(self, mock_from_url):
        """Test that a new Redis client is created on first call."""
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        # Reset the global client
        import src.config.redis_config as redis_module
        redis_module._redis_client = None

        client = get_redis_client()

        assert client == mock_client
        mock_from_url.assert_called_once()

    @patch('src.config.redis_config.redis.from_url')
    def test_get_redis_client_returns_cached_client(self, mock_from_url):
        """Test that subsequent calls return the cached client."""
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        client1 = get_redis_client()
        client2 = get_redis_client()

        assert client1 == client2
        # Should only be called once due to caching
        assert mock_from_url.call_count >= 1


class TestCacheGet:
    """Test cache_get function with boundary values."""

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_get_with_valid_json(self, mock_get_client):
        """Test retrieving valid JSON from cache."""
        mock_client = MagicMock()
        test_data = {"key": "value", "number": 42}
        mock_client.get.return_value = json.dumps(test_data)
        mock_get_client.return_value = mock_client

        result = cache_get("test_key")

        assert result == test_data
        mock_client.get.assert_called_once_with("test_key")

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_get_with_none_value(self, mock_get_client):
        """Test retrieving None from cache (cache miss)."""
        mock_client = MagicMock()
        mock_client.get.return_value = None
        mock_get_client.return_value = mock_client

        result = cache_get("missing_key")

        assert result is None

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_get_with_empty_string(self, mock_get_client):
        """Test retrieving empty string from cache."""
        mock_client = MagicMock()
        mock_client.get.return_value = '""'
        mock_get_client.return_value = mock_client

        result = cache_get("empty_key")

        assert result == ""

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_get_with_redis_exception(self, mock_get_client):
        """Test cache_get returns None when Redis raises exception."""
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Redis connection error")
        mock_get_client.return_value = mock_client

        result = cache_get("error_key")

        assert result is None

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_get_with_complex_nested_data(self, mock_get_client):
        """Test retrieving complex nested JSON data."""
        mock_client = MagicMock()
        complex_data = {
            "list": [1, 2, 3],
            "nested": {"a": {"b": {"c": "deep"}}},
            "null": None,
            "bool": True
        }
        mock_client.get.return_value = json.dumps(complex_data)
        mock_get_client.return_value = mock_client

        result = cache_get("complex_key")

        assert result == complex_data


class TestCacheSet:
    """Test cache_set function with boundary values."""

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_with_valid_data(self, mock_get_client):
        """Test setting valid data in cache."""
        mock_client = MagicMock()
        mock_client.setex.return_value = True
        mock_get_client.return_value = mock_client

        test_data = {"key": "value"}
        result = cache_set("test_key", test_data, ttl=300)

        assert result is True
        mock_client.setex.assert_called_once()
        args = mock_client.setex.call_args[0]
        assert args[0] == "test_key"
        assert args[1] == 300
        assert json.loads(args[2]) == test_data

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_with_custom_ttl(self, mock_get_client):
        """Test setting data with custom TTL."""
        mock_client = MagicMock()
        mock_client.setex.return_value = True
        mock_get_client.return_value = mock_client

        cache_set("key", "value", ttl=600)

        args = mock_client.setex.call_args[0]
        assert args[1] == 600

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_with_zero_ttl(self, mock_get_client):
        """Test setting data with minimum TTL value."""
        mock_client = MagicMock()
        mock_client.setex.return_value = True
        mock_get_client.return_value = mock_client

        result = cache_set("key", "value", ttl=0)

        assert result is True
        args = mock_client.setex.call_args[0]
        assert args[1] == 0

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_with_large_ttl(self, mock_get_client):
        """Test setting data with large TTL value."""
        mock_client = MagicMock()
        mock_client.setex.return_value = True
        mock_get_client.return_value = mock_client

        result = cache_set("key", "value", ttl=86400)  # 1 day

        assert result is True

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_with_redis_exception(self, mock_get_client):
        """Test cache_set returns False when Redis raises exception."""
        mock_client = MagicMock()
        mock_client.setex.side_effect = Exception("Redis write error")
        mock_get_client.return_value = mock_client

        result = cache_set("key", "value")

        assert result is False

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_with_none_value(self, mock_get_client):
        """Test setting None value in cache."""
        mock_client = MagicMock()
        mock_client.setex.return_value = True
        mock_get_client.return_value = mock_client

        result = cache_set("key", None)

        assert result is True
        args = mock_client.setex.call_args[0]
        assert args[2] == "null"


class TestCacheDelete:
    """Test cache_delete function."""

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_delete_existing_key(self, mock_get_client):
        """Test deleting an existing key."""
        mock_client = MagicMock()
        mock_client.delete.return_value = 1
        mock_get_client.return_value = mock_client

        result = cache_delete("test_key")

        assert result is True
        mock_client.delete.assert_called_once_with("test_key")

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_delete_nonexistent_key(self, mock_get_client):
        """Test deleting a non-existent key."""
        mock_client = MagicMock()
        mock_client.delete.return_value = 0
        mock_get_client.return_value = mock_client

        result = cache_delete("missing_key")

        # Function returns True regardless
        assert result is True

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_delete_with_redis_exception(self, mock_get_client):
        """Test cache_delete returns False when Redis raises exception."""
        mock_client = MagicMock()
        mock_client.delete.side_effect = Exception("Redis delete error")
        mock_get_client.return_value = mock_client

        result = cache_delete("key")

        assert result is False

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_delete_with_empty_string_key(self, mock_get_client):
        """Test deleting with empty string key."""
        mock_client = MagicMock()
        mock_client.delete.return_value = 0
        mock_get_client.return_value = mock_client

        result = cache_delete("")

        assert result is True
        mock_client.delete.assert_called_once_with("")
