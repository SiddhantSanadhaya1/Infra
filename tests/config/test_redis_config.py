"""Unit tests for Redis configuration module"""
import pytest
from unittest.mock import patch, MagicMock
import json
import redis


class TestGetRedisClient:
    """Test Redis client initialization"""

    @patch('redis.from_url')
    def test_get_redis_client_creates_new_client(self, mock_from_url):
        """Test that get_redis_client creates a new client on first call"""
        import sys
        if 'src.config.redis_config' in sys.modules:
            del sys.modules['src.config.redis_config']

        from src.config.redis_config import get_redis_client

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        client = get_redis_client()

        mock_from_url.assert_called_once_with("redis://localhost:6379/0", decode_responses=True)
        assert client == mock_client

    @patch('redis.from_url')
    def test_get_redis_client_returns_singleton(self, mock_from_url):
        """Test that get_redis_client returns the same instance on subsequent calls"""
        import sys
        if 'src.config.redis_config' in sys.modules:
            del sys.modules['src.config.redis_config']

        from src.config.redis_config import get_redis_client

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        client1 = get_redis_client()
        client2 = get_redis_client()

        # Should only create client once
        mock_from_url.assert_called_once()
        assert client1 == client2

    @patch.dict('os.environ', {"REDIS_URL": "redis://custom:6380/1"})
    @patch('redis.from_url')
    def test_get_redis_client_custom_url(self, mock_from_url):
        """Test Redis client with custom URL from environment"""
        import sys
        if 'src.config.redis_config' in sys.modules:
            del sys.modules['src.config.redis_config']

        from src.config.redis_config import get_redis_client

        get_redis_client()

        mock_from_url.assert_called_once_with("redis://custom:6380/1", decode_responses=True)


class TestCacheGet:
    """Test cache_get function"""

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_get_returns_value_when_exists(self, mock_get_client):
        """Test cache_get returns deserialized value when key exists"""
        from src.config.redis_config import cache_get

        mock_client = MagicMock()
        mock_client.get.return_value = json.dumps({"name": "test", "value": 123})
        mock_get_client.return_value = mock_client

        result = cache_get("test:key")

        mock_client.get.assert_called_once_with("test:key")
        assert result == {"name": "test", "value": 123}

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_get_returns_none_when_key_not_found(self, mock_get_client):
        """Test cache_get returns None when key doesn't exist"""
        from src.config.redis_config import cache_get

        mock_client = MagicMock()
        mock_client.get.return_value = None
        mock_get_client.return_value = mock_client

        result = cache_get("nonexistent:key")

        assert result is None

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_get_handles_json_string(self, mock_get_client):
        """Test cache_get handles simple string values"""
        from src.config.redis_config import cache_get

        mock_client = MagicMock()
        mock_client.get.return_value = '"simple_string"'
        mock_get_client.return_value = mock_client

        result = cache_get("string:key")

        assert result == "simple_string"

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_get_handles_json_number(self, mock_get_client):
        """Test cache_get handles numeric values"""
        from src.config.redis_config import cache_get

        mock_client = MagicMock()
        mock_client.get.return_value = "42"
        mock_get_client.return_value = mock_client

        result = cache_get("number:key")

        assert result == 42

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_get_handles_json_array(self, mock_get_client):
        """Test cache_get handles array values"""
        from src.config.redis_config import cache_get

        mock_client = MagicMock()
        mock_client.get.return_value = json.dumps([1, 2, 3])
        mock_get_client.return_value = mock_client

        result = cache_get("array:key")

        assert result == [1, 2, 3]

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_get_returns_none_on_redis_error(self, mock_get_client):
        """Test cache_get returns None and logs warning on Redis error"""
        from src.config.redis_config import cache_get

        mock_client = MagicMock()
        mock_client.get.side_effect = redis.ConnectionError("Connection failed")
        mock_get_client.return_value = mock_client

        result = cache_get("error:key")

        assert result is None

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_get_returns_none_on_json_decode_error(self, mock_get_client):
        """Test cache_get returns None on invalid JSON"""
        from src.config.redis_config import cache_get

        mock_client = MagicMock()
        mock_client.get.return_value = "invalid{json"
        mock_get_client.return_value = mock_client

        result = cache_get("invalid:key")

        assert result is None


class TestCacheSet:
    """Test cache_set function"""

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_stores_value_with_default_ttl(self, mock_get_client):
        """Test cache_set stores serialized value with default TTL"""
        from src.config.redis_config import cache_set

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_set("test:key", {"data": "value"})

        mock_client.setex.assert_called_once_with(
            "test:key",
            300,
            json.dumps({"data": "value"}, default=str)
        )
        assert result is True

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_stores_value_with_custom_ttl(self, mock_get_client):
        """Test cache_set stores value with custom TTL"""
        from src.config.redis_config import cache_set

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_set("test:key", {"data": "value"}, ttl=600)

        mock_client.setex.assert_called_once_with(
            "test:key",
            600,
            json.dumps({"data": "value"}, default=str)
        )
        assert result is True

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_with_zero_ttl(self, mock_get_client):
        """Test cache_set with TTL of zero"""
        from src.config.redis_config import cache_set

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_set("test:key", "value", ttl=0)

        mock_client.setex.assert_called_once()
        assert result is True

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_with_very_large_ttl(self, mock_get_client):
        """Test cache_set with very large TTL"""
        from src.config.redis_config import cache_set

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cache_set("test:key", "value", ttl=86400 * 30)  # 30 days

        mock_client.setex.assert_called_once_with(
            "test:key",
            86400 * 30,
            json.dumps("value", default=str)
        )
        assert result is True

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_serializes_complex_types(self, mock_get_client):
        """Test cache_set handles complex nested structures"""
        from src.config.redis_config import cache_set
        from datetime import datetime

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        complex_data = {
            "string": "value",
            "number": 123,
            "nested": {"key": "val"},
            "list": [1, 2, 3],
            "timestamp": datetime(2026, 4, 1, 12, 0, 0)
        }

        result = cache_set("complex:key", complex_data)

        assert result is True
        # Verify JSON serialization was called with default=str for datetime
        mock_client.setex.assert_called_once()

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_set_returns_false_on_redis_error(self, mock_get_client):
        """Test cache_set returns False and logs warning on Redis error"""
        from src.config.redis_config import cache_set

        mock_client = MagicMock()
        mock_client.setex.side_effect = redis.ConnectionError("Connection failed")
        mock_get_client.return_value = mock_client

        result = cache_set("error:key", "value")

        assert result is False


class TestCacheDelete:
    """Test cache_delete function"""

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_delete_removes_existing_key(self, mock_get_client):
        """Test cache_delete removes an existing key"""
        from src.config.redis_config import cache_delete

        mock_client = MagicMock()
        mock_client.delete.return_value = 1
        mock_get_client.return_value = mock_client

        result = cache_delete("test:key")

        mock_client.delete.assert_called_once_with("test:key")
        assert result is True

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_delete_nonexistent_key(self, mock_get_client):
        """Test cache_delete on non-existent key still returns True"""
        from src.config.redis_config import cache_delete

        mock_client = MagicMock()
        mock_client.delete.return_value = 0
        mock_get_client.return_value = mock_client

        result = cache_delete("nonexistent:key")

        assert result is True

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_delete_returns_false_on_redis_error(self, mock_get_client):
        """Test cache_delete returns False and logs warning on Redis error"""
        from src.config.redis_config import cache_delete

        mock_client = MagicMock()
        mock_client.delete.side_effect = redis.ConnectionError("Connection failed")
        mock_get_client.return_value = mock_client

        result = cache_delete("error:key")

        assert result is False

    @patch('src.config.redis_config.get_redis_client')
    def test_cache_delete_with_empty_key(self, mock_get_client):
        """Test cache_delete with empty string key"""
        from src.config.redis_config import cache_delete

        mock_client = MagicMock()
        mock_client.delete.return_value = 0
        mock_get_client.return_value = mock_client

        result = cache_delete("")

        mock_client.delete.assert_called_once_with("")
        assert result is True
