"""
Unit tests for src.config.redis_config
Tests Redis client initialization and cache operations.
"""
import pytest
import json
import os
from unittest.mock import patch, MagicMock, call
from src.config.redis_config import (
    get_redis_client,
    cache_get,
    cache_set,
    cache_delete,
)


class TestGetRedisClient:
    """Test Redis client singleton"""

    @patch('src.config.redis_config.redis.from_url')
    def test_get_redis_client_creates_new_client(self, mock_from_url):
        """Test get_redis_client creates new client on first call"""
        import importlib
        import src.config.redis_config
        src.config.redis_config._redis_client = None
        importlib.reload(src.config.redis_config)

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        client = src.config.redis_config.get_redis_client()

        assert client is mock_client
        mock_from_url.assert_called_once_with("redis://localhost:6379/0", decode_responses=True)

    @patch('src.config.redis_config.redis.from_url')
    def test_get_redis_client_reuses_existing_client(self, mock_from_url):
        """Test get_redis_client returns existing client on subsequent calls"""
        import importlib
        import src.config.redis_config
        src.config.redis_config._redis_client = None
        importlib.reload(src.config.redis_config)

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        client1 = src.config.redis_config.get_redis_client()
        client2 = src.config.redis_config.get_redis_client()

        assert client1 is client2
        mock_from_url.assert_called_once()

    @patch('src.config.redis_config.redis.from_url')
    @patch.dict(os.environ, {'REDIS_URL': 'redis://custom-host:6380/1'}, clear=False)
    def test_get_redis_client_custom_url(self, mock_from_url):
        """Test get_redis_client with custom Redis URL"""
        import importlib
        import src.config.redis_config
        src.config.redis_config._redis_client = None
        importlib.reload(src.config.redis_config)

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        client = src.config.redis_config.get_redis_client()

        mock_from_url.assert_called_once_with("redis://custom-host:6380/1", decode_responses=True)


class TestCacheGet:
    """Test cache_get function"""

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_get_hit(self, mock_get_client):
        """Test cache_get returns deserialized value on cache hit"""
        mock_client = MagicMock()
        mock_client.get.return_value = '{"key": "value", "number": 123}'
        mock_get_client.return_value = mock_client

        result = cache_get("test_key")

        assert result == {"key": "value", "number": 123}
        mock_client.get.assert_called_once_with("test_key")

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_get_miss(self, mock_get_client):
        """Test cache_get returns None on cache miss"""
        mock_client = MagicMock()
        mock_client.get.return_value = None
        mock_get_client.return_value = mock_client

        result = cache_get("nonexistent_key")

        assert result is None
        mock_client.get.assert_called_once_with("nonexistent_key")

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_get_simple_string(self, mock_get_client):
        """Test cache_get with simple string value"""
        mock_client = MagicMock()
        mock_client.get.return_value = '"simple_string"'
        mock_get_client.return_value = mock_client

        result = cache_get("string_key")

        assert result == "simple_string"

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_get_number(self, mock_get_client):
        """Test cache_get with number value"""
        mock_client = MagicMock()
        mock_client.get.return_value = '42'
        mock_get_client.return_value = mock_client

        result = cache_get("number_key")

        assert result == 42

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_get_list(self, mock_get_client):
        """Test cache_get with list value"""
        mock_client = MagicMock()
        mock_client.get.return_value = '[1, 2, 3, 4, 5]'
        mock_get_client.return_value = mock_client

        result = cache_get("list_key")

        assert result == [1, 2, 3, 4, 5]

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_get_exception_handling(self, mock_get_client):
        """Test cache_get handles Redis exceptions gracefully"""
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Redis connection error")
        mock_get_client.return_value = mock_client

        result = cache_get("error_key")

        assert result is None

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_get_json_decode_error(self, mock_get_client):
        """Test cache_get handles JSON decode errors"""
        mock_client = MagicMock()
        mock_client.get.return_value = 'invalid json {'
        mock_get_client.return_value = mock_client

        result = cache_get("invalid_json_key")

        assert result is None

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_get_empty_string(self, mock_get_client):
        """Test cache_get with empty string key"""
        mock_client = MagicMock()
        mock_client.get.return_value = '"test"'
        mock_get_client.return_value = mock_client

        result = cache_get("")

        mock_client.get.assert_called_once_with("")


class TestCacheSet:
    """Test cache_set function"""

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_success(self, mock_get_client):
        """Test cache_set successfully stores value"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_set("test_key", {"data": "value"}, ttl=300)

        assert result is True
        mock_client.setex.assert_called_once_with(
            "test_key",
            300,
            '{"data": "value"}'
        )

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_custom_ttl(self, mock_get_client):
        """Test cache_set with custom TTL"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_set("key", "value", ttl=600)

        assert result is True
        call_args = mock_client.setex.call_args[0]
        assert call_args[1] == 600

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_default_ttl(self, mock_get_client):
        """Test cache_set with default TTL"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_set("key", "value")

        assert result is True
        call_args = mock_client.setex.call_args[0]
        assert call_args[1] == 300

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_complex_value(self, mock_get_client):
        """Test cache_set with complex nested value"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        complex_value = {
            "id": "123",
            "nested": {
                "items": [1, 2, 3],
                "metadata": {"key": "value"}
            }
        }

        result = cache_set("complex_key", complex_value, ttl=300)

        assert result is True
        call_args = mock_client.setex.call_args[0]
        stored_value = json.loads(call_args[2])
        assert stored_value == complex_value

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_none_value(self, mock_get_client):
        """Test cache_set with None value"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_set("none_key", None, ttl=300)

        assert result is True
        call_args = mock_client.setex.call_args[0]
        assert call_args[2] == 'null'

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_exception_handling(self, mock_get_client):
        """Test cache_set handles Redis exceptions gracefully"""
        mock_client = MagicMock()
        mock_client.setex.side_effect = Exception("Redis connection error")
        mock_get_client.return_value = mock_client

        result = cache_set("error_key", "value", ttl=300)

        assert result is False

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_zero_ttl(self, mock_get_client):
        """Test cache_set with zero TTL"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_set("key", "value", ttl=0)

        assert result is True
        call_args = mock_client.setex.call_args[0]
        assert call_args[1] == 0

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_very_large_ttl(self, mock_get_client):
        """Test cache_set with very large TTL"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_set("key", "value", ttl=86400 * 7)  # 7 days

        assert result is True
        call_args = mock_client.setex.call_args[0]
        assert call_args[1] == 604800

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_string_value(self, mock_get_client):
        """Test cache_set with string value"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_set("string_key", "simple_string", ttl=300)

        assert result is True
        call_args = mock_client.setex.call_args[0]
        assert call_args[2] == '"simple_string"'


class TestCacheDelete:
    """Test cache_delete function"""

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_delete_success(self, mock_get_client):
        """Test cache_delete successfully deletes key"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_delete("test_key")

        assert result is True
        mock_client.delete.assert_called_once_with("test_key")

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_delete_nonexistent_key(self, mock_get_client):
        """Test cache_delete with non-existent key"""
        mock_client = MagicMock()
        mock_client.delete.return_value = 0
        mock_get_client.return_value = mock_client

        result = cache_delete("nonexistent_key")

        assert result is True
        mock_client.delete.assert_called_once_with("nonexistent_key")

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_delete_exception_handling(self, mock_get_client):
        """Test cache_delete handles Redis exceptions gracefully"""
        mock_client = MagicMock()
        mock_client.delete.side_effect = Exception("Redis connection error")
        mock_get_client.return_value = mock_client

        result = cache_delete("error_key")

        assert result is False

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_delete_empty_key(self, mock_get_client):
        """Test cache_delete with empty string key"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_delete("")

        assert result is True
        mock_client.delete.assert_called_once_with("")

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_delete_multiple_calls(self, mock_get_client):
        """Test cache_delete can be called multiple times"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result1 = cache_delete("key1")
        result2 = cache_delete("key2")
        result3 = cache_delete("key3")

        assert result1 is True
        assert result2 is True
        assert result3 is True
        assert mock_client.delete.call_count == 3


class TestRedisURL:
    """Test Redis URL configuration"""

    @patch.dict(os.environ, {}, clear=True)
    def test_redis_url_default(self):
        """Test REDIS_URL defaults to localhost"""
        import importlib
        import src.config.redis_config
        importlib.reload(src.config.redis_config)

        assert src.config.redis_config.REDIS_URL == "redis://localhost:6379/0"

    @patch.dict(os.environ, {'REDIS_URL': 'redis://production-host:6379/2'}, clear=True)
    def test_redis_url_from_env(self):
        """Test REDIS_URL from environment variable"""
        import importlib
        import src.config.redis_config
        importlib.reload(src.config.redis_config)

        assert src.config.redis_config.REDIS_URL == "redis://production-host:6379/2"
