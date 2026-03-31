"""Tests for src/middleware/auth.py"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials

from src.middleware.auth import decode_jwt, get_current_user, optional_auth, DEV_TOKEN


class TestDecodeJWT:
    """Test decode_jwt function with various tokens."""

    @patch('src.middleware.auth.jwt.decode')
    def test_decode_jwt_with_valid_token(self, mock_jwt_decode):
        """Test decoding a valid JWT token."""
        mock_payload = {"sub": "user123", "email": "test@example.com"}
        mock_jwt_decode.return_value = mock_payload

        result = decode_jwt("valid.jwt.token")

        assert result == mock_payload
        mock_jwt_decode.assert_called_once()

    @patch('src.middleware.auth.jwt.decode')
    def test_decode_jwt_with_invalid_token(self, mock_jwt_decode):
        """Test decoding an invalid JWT token returns None."""
        from jose import JWTError
        mock_jwt_decode.side_effect = JWTError("Invalid token")

        result = decode_jwt("invalid.token")

        assert result is None

    @patch('src.middleware.auth.jwt.decode')
    def test_decode_jwt_with_expired_token(self, mock_jwt_decode):
        """Test decoding an expired JWT token returns None."""
        from jose import JWTError
        mock_jwt_decode.side_effect = JWTError("Token has expired")

        result = decode_jwt("expired.token")

        assert result is None

    @patch('src.middleware.auth.jwt.decode')
    def test_decode_jwt_with_empty_payload(self, mock_jwt_decode):
        """Test decoding token with empty payload."""
        mock_jwt_decode.return_value = {}

        result = decode_jwt("token.with.empty.payload")

        assert result == {}


@pytest.mark.asyncio
class TestGetCurrentUser:
    """Test get_current_user authentication dependency."""

    async def test_get_current_user_with_missing_credentials(self):
        """Test that missing credentials raises 401."""
        mock_request = MagicMock(spec=Request)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, None)

        assert exc_info.value.status_code == 401
        assert "Authorization header missing" in exc_info.value.detail

    async def test_get_current_user_with_dev_token(self):
        """Test that dev token bypasses JWT validation."""
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=DEV_TOKEN
        )

        user = await get_current_user(mock_request, credentials)

        assert user["policyholder_id"] == "00000000-0000-0000-0000-000000000001"
        assert user["email"] == "demo@insureco.com"
        assert user["role"] == "demo"
        assert mock_request.state.policyholder_id == user["policyholder_id"]

    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_with_valid_jwt(self, mock_decode):
        """Test authentication with valid JWT token."""
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_decode.return_value = {
            "sub": "test-user-id",
            "email": "user@example.com",
            "role": "admin"
        }
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid.jwt.token"
        )

        user = await get_current_user(mock_request, credentials)

        assert user["policyholder_id"] == "test-user-id"
        assert user["email"] == "user@example.com"
        assert user["role"] == "admin"

    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_with_invalid_jwt(self, mock_decode):
        """Test that invalid JWT raises 401."""
        mock_request = MagicMock(spec=Request)
        mock_decode.return_value = None
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.token"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, credentials)

        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail

    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_with_missing_subject(self, mock_decode):
        """Test that JWT without 'sub' claim raises 401."""
        mock_request = MagicMock(spec=Request)
        mock_decode.return_value = {"email": "user@example.com"}
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="token.without.sub"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, credentials)

        assert exc_info.value.status_code == 401
        assert "Token missing subject claim" in exc_info.value.detail

    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_with_empty_subject(self, mock_decode):
        """Test that JWT with empty 'sub' claim raises 401."""
        mock_request = MagicMock(spec=Request)
        mock_decode.return_value = {"sub": ""}
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="token.with.empty.sub"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, credentials)

        assert exc_info.value.status_code == 401
        assert "Token missing subject claim" in exc_info.value.detail

    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_default_role(self, mock_decode):
        """Test that missing role defaults to 'policyholder'."""
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_decode.return_value = {
            "sub": "user-123",
            "email": "user@example.com"
            # No role specified
        }
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="token.without.role"
        )

        user = await get_current_user(mock_request, credentials)

        assert user["role"] == "policyholder"


@pytest.mark.asyncio
class TestOptionalAuth:
    """Test optional_auth dependency."""

    async def test_optional_auth_with_no_credentials(self):
        """Test that optional_auth returns None when no credentials provided."""
        mock_request = MagicMock(spec=Request)

        result = await optional_auth(mock_request, None)

        assert result is None

    @patch('src.middleware.auth.get_current_user')
    async def test_optional_auth_with_valid_credentials(self, mock_get_user):
        """Test that optional_auth returns user when credentials are valid."""
        mock_request = MagicMock(spec=Request)
        mock_user = {"policyholder_id": "123", "email": "test@example.com"}
        mock_get_user.return_value = mock_user
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid.token"
        )

        result = await optional_auth(mock_request, credentials)

        assert result == mock_user

    @patch('src.middleware.auth.get_current_user')
    async def test_optional_auth_with_invalid_credentials(self, mock_get_user):
        """Test that optional_auth returns None when credentials are invalid."""
        mock_request = MagicMock(spec=Request)
        mock_get_user.side_effect = HTTPException(status_code=401, detail="Invalid token")
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.token"
        )

        result = await optional_auth(mock_request, credentials)

        assert result is None

    async def test_optional_auth_with_dev_token(self):
        """Test optional_auth with dev token."""
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=DEV_TOKEN
        )

        result = await optional_auth(mock_request, credentials)

        assert result is not None
        assert result["role"] == "demo"
