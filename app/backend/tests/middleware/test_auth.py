"""
Unit tests for src.middleware.auth
Tests JWT authentication and authorization.
"""
import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException
from src.middleware.auth import (
    decode_jwt,
    get_current_user,
    optional_auth,
    DEV_TOKEN,
)


class TestDecodeJWT:
    """Test JWT decoding"""

    @patch('src.middleware.auth.jwt.decode')
    def test_decode_jwt_valid_token(self, mock_decode):
        """Test decoding valid JWT token"""
        mock_decode.return_value = {
            "sub": "user-123",
            "email": "user@example.com",
            "role": "policyholder"
        }

        result = decode_jwt("valid.jwt.token")

        assert result == {
            "sub": "user-123",
            "email": "user@example.com",
            "role": "policyholder"
        }
        mock_decode.assert_called_once()

    @patch('src.middleware.auth.jwt.decode')
    def test_decode_jwt_invalid_token(self, mock_decode):
        """Test decoding invalid JWT token"""
        from jose import JWTError
        mock_decode.side_effect = JWTError("Invalid token")

        result = decode_jwt("invalid.jwt.token")

        assert result is None

    @patch('src.middleware.auth.jwt.decode')
    def test_decode_jwt_expired_token(self, mock_decode):
        """Test decoding expired JWT token"""
        from jose import JWTError
        mock_decode.side_effect = JWTError("Token expired")

        result = decode_jwt("expired.jwt.token")

        assert result is None

    @patch('src.middleware.auth.jwt.decode')
    def test_decode_jwt_malformed_token(self, mock_decode):
        """Test decoding malformed JWT token"""
        from jose import JWTError
        mock_decode.side_effect = JWTError("Malformed token")

        result = decode_jwt("malformed")

        assert result is None

    @patch('src.middleware.auth.jwt.decode')
    def test_decode_jwt_with_all_claims(self, mock_decode):
        """Test decoding JWT with all standard claims"""
        mock_decode.return_value = {
            "sub": "user-456",
            "email": "admin@example.com",
            "role": "admin",
            "iat": 1234567890,
            "exp": 1234571490
        }

        result = decode_jwt("token.with.claims")

        assert result["sub"] == "user-456"
        assert result["role"] == "admin"

    @patch('src.middleware.auth.jwt.decode')
    def test_decode_jwt_empty_string(self, mock_decode):
        """Test decoding empty string token"""
        from jose import JWTError
        mock_decode.side_effect = JWTError("Invalid token")

        result = decode_jwt("")

        assert result is None


class TestGetCurrentUser:
    """Test get_current_user dependency"""

    @pytest.mark.asyncio
    async def test_get_current_user_no_credentials(self):
        """Test get_current_user raises 401 when no credentials provided"""
        mock_request = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, None)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authorization header missing"

    @pytest.mark.asyncio
    async def test_get_current_user_demo_token(self):
        """Test get_current_user with demo token"""
        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = DEV_TOKEN

        result = await get_current_user(mock_request, mock_credentials)

        assert result["policyholder_id"] == "00000000-0000-0000-0000-000000000001"
        assert result["email"] == "demo@insureco.com"
        assert result["role"] == "demo"
        assert mock_request.state.policyholder_id == "00000000-0000-0000-0000-000000000001"

    @pytest.mark.asyncio
    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_valid_jwt(self, mock_decode):
        """Test get_current_user with valid JWT token"""
        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid.jwt.token"

        mock_decode.return_value = {
            "sub": "user-789",
            "email": "customer@example.com",
            "role": "policyholder"
        }

        result = await get_current_user(mock_request, mock_credentials)

        assert result["policyholder_id"] == "user-789"
        assert result["email"] == "customer@example.com"
        assert result["role"] == "policyholder"
        assert mock_request.state.policyholder_id == "user-789"

    @pytest.mark.asyncio
    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_invalid_jwt(self, mock_decode):
        """Test get_current_user raises 401 for invalid JWT"""
        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid.jwt.token"

        mock_decode.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid or expired token"

    @pytest.mark.asyncio
    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_missing_sub_claim(self, mock_decode):
        """Test get_current_user raises 401 when sub claim is missing"""
        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "token.without.sub"

        mock_decode.return_value = {
            "email": "user@example.com",
            "role": "policyholder"
        }

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token missing subject claim"

    @pytest.mark.asyncio
    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_empty_sub_claim(self, mock_decode):
        """Test get_current_user raises 401 when sub claim is empty"""
        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "token.with.empty.sub"

        mock_decode.return_value = {
            "sub": "",
            "email": "user@example.com"
        }

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token missing subject claim"

    @pytest.mark.asyncio
    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_none_sub_claim(self, mock_decode):
        """Test get_current_user raises 401 when sub claim is None"""
        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "token"

        mock_decode.return_value = {
            "sub": None,
            "email": "user@example.com"
        }

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_credentials)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_without_email(self, mock_decode):
        """Test get_current_user with token missing email claim"""
        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "token"

        mock_decode.return_value = {
            "sub": "user-001",
            "role": "policyholder"
        }

        result = await get_current_user(mock_request, mock_credentials)

        assert result["policyholder_id"] == "user-001"
        assert result["email"] is None
        assert result["role"] == "policyholder"

    @pytest.mark.asyncio
    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_without_role(self, mock_decode):
        """Test get_current_user defaults to policyholder role when missing"""
        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "token"

        mock_decode.return_value = {
            "sub": "user-002",
            "email": "user@example.com"
        }

        result = await get_current_user(mock_request, mock_credentials)

        assert result["role"] == "policyholder"

    @pytest.mark.asyncio
    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_admin_role(self, mock_decode):
        """Test get_current_user with admin role"""
        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "admin.token"

        mock_decode.return_value = {
            "sub": "admin-123",
            "email": "admin@insureco.com",
            "role": "admin"
        }

        result = await get_current_user(mock_request, mock_credentials)

        assert result["role"] == "admin"


class TestOptionalAuth:
    """Test optional_auth dependency"""

    @pytest.mark.asyncio
    async def test_optional_auth_no_credentials(self):
        """Test optional_auth returns None when no credentials provided"""
        mock_request = MagicMock()

        result = await optional_auth(mock_request, None)

        assert result is None

    @pytest.mark.asyncio
    async def test_optional_auth_with_demo_token(self):
        """Test optional_auth with valid demo token"""
        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = DEV_TOKEN

        result = await optional_auth(mock_request, mock_credentials)

        assert result is not None
        assert result["policyholder_id"] == "00000000-0000-0000-0000-000000000001"

    @pytest.mark.asyncio
    @patch('src.middleware.auth.decode_jwt')
    async def test_optional_auth_with_valid_jwt(self, mock_decode):
        """Test optional_auth with valid JWT token"""
        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid.jwt.token"

        mock_decode.return_value = {
            "sub": "user-123",
            "email": "user@example.com",
            "role": "policyholder"
        }

        result = await optional_auth(mock_request, mock_credentials)

        assert result is not None
        assert result["policyholder_id"] == "user-123"

    @pytest.mark.asyncio
    @patch('src.middleware.auth.decode_jwt')
    async def test_optional_auth_with_invalid_jwt(self, mock_decode):
        """Test optional_auth returns None for invalid JWT"""
        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid.jwt.token"

        mock_decode.return_value = None

        result = await optional_auth(mock_request, mock_credentials)

        assert result is None

    @pytest.mark.asyncio
    @patch('src.middleware.auth.decode_jwt')
    async def test_optional_auth_catches_http_exception(self, mock_decode):
        """Test optional_auth catches HTTPException and returns None"""
        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "token"

        mock_decode.return_value = {"sub": ""}  # Will cause HTTPException

        result = await optional_auth(mock_request, mock_credentials)

        assert result is None


class TestAuthConstants:
    """Test auth configuration constants"""

    @patch.dict(os.environ, {}, clear=True)
    def test_secret_key_default(self):
        """Test SECRET_KEY has default value"""
        import importlib
        import src.middleware.auth
        importlib.reload(src.middleware.auth)

        assert src.middleware.auth.SECRET_KEY == "insureco-secret-key-for-dev-only"

    @patch.dict(os.environ, {'JWT_SECRET_KEY': 'custom-secret-key-123'}, clear=True)
    def test_secret_key_from_env(self):
        """Test SECRET_KEY from environment variable"""
        import importlib
        import src.middleware.auth
        importlib.reload(src.middleware.auth)

        assert src.middleware.auth.SECRET_KEY == "custom-secret-key-123"

    @patch.dict(os.environ, {}, clear=True)
    def test_algorithm_default(self):
        """Test ALGORITHM has default value"""
        import importlib
        import src.middleware.auth
        importlib.reload(src.middleware.auth)

        assert src.middleware.auth.ALGORITHM == "HS256"

    @patch.dict(os.environ, {'JWT_ALGORITHM': 'RS256'}, clear=True)
    def test_algorithm_from_env(self):
        """Test ALGORITHM from environment variable"""
        import importlib
        import src.middleware.auth
        importlib.reload(src.middleware.auth)

        assert src.middleware.auth.ALGORITHM == "RS256"

    def test_dev_token_constant(self):
        """Test DEV_TOKEN constant value"""
        assert DEV_TOKEN == "insureco-demo-token"
