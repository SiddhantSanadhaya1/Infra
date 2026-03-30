"""Unit tests for src.middleware.auth module."""
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from src.middleware.auth import decode_jwt, get_current_user, optional_auth


class TestDecodeJWT:
    """Test JWT decoding functionality."""

    @patch("src.middleware.auth.jwt.decode")
    def test_decode_jwt_with_valid_token(self, mock_decode):
        """Test decoding a valid JWT token."""
        expected_payload = {
            "sub": "user123",
            "email": "user@example.com",
            "role": "policyholder",
        }
        mock_decode.return_value = expected_payload

        result = decode_jwt("valid.jwt.token")

        mock_decode.assert_called_once_with(
            "valid.jwt.token", "insureco-secret-key-for-dev-only", algorithms=["HS256"]
        )
        assert result == expected_payload

    @patch("src.middleware.auth.jwt.decode")
    def test_decode_jwt_with_invalid_token(self, mock_decode):
        """Test decoding an invalid JWT token returns None."""
        from jose import JWTError

        mock_decode.side_effect = JWTError("Invalid token")

        result = decode_jwt("invalid.jwt.token")

        assert result is None

    @patch("src.middleware.auth.jwt.decode")
    def test_decode_jwt_with_expired_token(self, mock_decode):
        """Test decoding an expired JWT token returns None."""
        from jose import ExpiredSignatureError

        mock_decode.side_effect = ExpiredSignatureError("Token expired")

        result = decode_jwt("expired.jwt.token")

        assert result is None

    @patch("src.middleware.auth.jwt.decode")
    def test_decode_jwt_with_malformed_token(self, mock_decode):
        """Test decoding a malformed JWT token returns None."""
        from jose import JWTError

        mock_decode.side_effect = JWTError("Malformed token")

        result = decode_jwt("malformed")

        assert result is None


class TestGetCurrentUser:
    """Test user authentication middleware."""

    @pytest.mark.asyncio
    async def test_get_current_user_with_no_credentials(self):
        """Test authentication fails when no credentials provided."""
        mock_request = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, None)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authorization header missing"
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    @pytest.mark.asyncio
    async def test_get_current_user_with_demo_token(self):
        """Test authentication with demo token bypasses JWT validation."""
        mock_request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="insureco-demo-token"
        )

        result = await get_current_user(mock_request, credentials)

        assert result == {
            "policyholder_id": "00000000-0000-0000-0000-000000000001",
            "email": "demo@insureco.com",
            "role": "demo",
        }
        assert (
            mock_request.state.policyholder_id
            == "00000000-0000-0000-0000-000000000001"
        )

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_get_current_user_with_valid_jwt(self, mock_decode):
        """Test authentication with valid JWT token."""
        mock_request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="valid.jwt.token"
        )
        mock_decode.return_value = {
            "sub": "policyholder-123",
            "email": "john@example.com",
            "role": "policyholder",
        }

        result = await get_current_user(mock_request, credentials)

        assert result == {
            "policyholder_id": "policyholder-123",
            "email": "john@example.com",
            "role": "policyholder",
        }
        assert mock_request.state.policyholder_id == "policyholder-123"

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_get_current_user_with_invalid_jwt(self, mock_decode):
        """Test authentication fails with invalid JWT token."""
        mock_request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid.jwt.token"
        )
        mock_decode.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid or expired token"

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_get_current_user_with_missing_subject_claim(self, mock_decode):
        """Test authentication fails when JWT missing 'sub' claim."""
        mock_request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="token.without.sub"
        )
        mock_decode.return_value = {"email": "user@example.com"}

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token missing subject claim"

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_get_current_user_with_empty_subject_claim(self, mock_decode):
        """Test authentication fails when JWT has empty 'sub' claim."""
        mock_request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="token.with.empty.sub"
        )
        mock_decode.return_value = {"sub": "", "email": "user@example.com"}

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token missing subject claim"

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_get_current_user_with_default_role(self, mock_decode):
        """Test authentication assigns default role when not in JWT."""
        mock_request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="token.without.role"
        )
        mock_decode.return_value = {
            "sub": "user-456",
            "email": "jane@example.com",
        }

        result = await get_current_user(mock_request, credentials)

        assert result["role"] == "policyholder"
        assert result["policyholder_id"] == "user-456"
        assert result["email"] == "jane@example.com"


class TestOptionalAuth:
    """Test optional authentication middleware."""

    @pytest.mark.asyncio
    async def test_optional_auth_with_no_credentials(self):
        """Test optional auth returns None when no credentials provided."""
        mock_request = MagicMock()

        result = await optional_auth(mock_request, None)

        assert result is None

    @pytest.mark.asyncio
    async def test_optional_auth_with_valid_token(self):
        """Test optional auth returns user when valid token provided."""
        mock_request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="insureco-demo-token"
        )

        result = await optional_auth(mock_request, credentials)

        assert result == {
            "policyholder_id": "00000000-0000-0000-0000-000000000001",
            "email": "demo@insureco.com",
            "role": "demo",
        }

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_optional_auth_with_invalid_token(self, mock_decode):
        """Test optional auth returns None for invalid token."""
        mock_request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid.token"
        )
        mock_decode.return_value = None

        result = await optional_auth(mock_request, credentials)

        assert result is None

    @pytest.mark.asyncio
    @patch("src.middleware.auth.get_current_user")
    async def test_optional_auth_catches_http_exceptions(self, mock_get_user):
        """Test optional auth catches HTTPException and returns None."""
        mock_request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="some.token"
        )
        mock_get_user.side_effect = HTTPException(status_code=401, detail="Unauthorized")

        result = await optional_auth(mock_request, credentials)

        assert result is None
