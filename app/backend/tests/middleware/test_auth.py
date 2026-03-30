"""
Comprehensive unit tests for auth middleware.
Tests JWT decoding, token validation, and authentication flows.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from src.middleware.auth import (
    decode_jwt,
    get_current_user,
    optional_auth,
    SECRET_KEY,
    ALGORITHM,
    DEV_TOKEN,
)


class TestDecodeJwt:
    """Test JWT token decoding functionality."""

    @patch("src.middleware.auth.jwt.decode")
    def test_decode_jwt_valid_token(self, mock_decode):
        """Test decoding a valid JWT token."""
        mock_decode.return_value = {"sub": "user-123", "email": "user@example.com"}

        payload = decode_jwt("valid.jwt.token")

        assert payload == {"sub": "user-123", "email": "user@example.com"}
        mock_decode.assert_called_once_with("valid.jwt.token", SECRET_KEY, algorithms=[ALGORITHM])

    @patch("src.middleware.auth.jwt.decode")
    def test_decode_jwt_invalid_token(self, mock_decode):
        """Test decoding an invalid JWT token."""
        from jose import JWTError
        mock_decode.side_effect = JWTError("Invalid token")

        payload = decode_jwt("invalid.token")

        assert payload is None

    @patch("src.middleware.auth.jwt.decode")
    def test_decode_jwt_expired_token(self, mock_decode):
        """Test decoding an expired JWT token."""
        from jose import JWTError
        mock_decode.side_effect = JWTError("Token expired")

        payload = decode_jwt("expired.token")

        assert payload is None

    @patch("src.middleware.auth.jwt.decode")
    def test_decode_jwt_empty_payload(self, mock_decode):
        """Test decoding token that returns empty payload."""
        mock_decode.return_value = {}

        payload = decode_jwt("token")

        assert payload == {}

    @patch("src.middleware.auth.jwt.decode")
    def test_decode_jwt_payload_with_role(self, mock_decode):
        """Test decoding token with role claim."""
        mock_decode.return_value = {
            "sub": "user-123",
            "email": "admin@example.com",
            "role": "admin"
        }

        payload = decode_jwt("token")

        assert payload["role"] == "admin"

    @patch("src.middleware.auth.jwt.decode")
    def test_decode_jwt_uses_correct_algorithm(self, mock_decode):
        """Test that decode_jwt uses the configured algorithm."""
        mock_decode.return_value = {"sub": "user-123"}

        decode_jwt("token")

        call_args = mock_decode.call_args
        assert call_args[1]["algorithms"] == [ALGORITHM]

    @patch("src.middleware.auth.jwt.decode")
    def test_decode_jwt_uses_secret_key(self, mock_decode):
        """Test that decode_jwt uses the configured secret key."""
        mock_decode.return_value = {"sub": "user-123"}

        decode_jwt("token")

        call_args = mock_decode.call_args
        assert call_args[0][1] == SECRET_KEY


class TestGetCurrentUser:
    """Test authentication middleware for getting current user."""

    @pytest.mark.asyncio
    async def test_get_current_user_no_credentials(self):
        """Test authentication fails when no credentials provided."""
        request = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request, None)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Authorization header missing"

    @pytest.mark.asyncio
    async def test_get_current_user_demo_token(self):
        """Test authentication with demo bypass token."""
        request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=DEV_TOKEN
        )

        user = await get_current_user(request, credentials)

        assert user["policyholder_id"] == "00000000-0000-0000-0000-000000000001"
        assert user["email"] == "demo@insureco.com"
        assert user["role"] == "demo"
        assert request.state.policyholder_id == "00000000-0000-0000-0000-000000000001"

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_get_current_user_valid_jwt(self, mock_decode):
        """Test authentication with valid JWT token."""
        request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid.jwt.token"
        )
        mock_decode.return_value = {
            "sub": "user-123",
            "email": "user@example.com",
            "role": "policyholder"
        }

        user = await get_current_user(request, credentials)

        assert user["policyholder_id"] == "user-123"
        assert user["email"] == "user@example.com"
        assert user["role"] == "policyholder"
        assert request.state.policyholder_id == "user-123"

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_get_current_user_invalid_jwt(self, mock_decode):
        """Test authentication fails with invalid JWT token."""
        request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.token"
        )
        mock_decode.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request, credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid or expired token"

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_get_current_user_token_missing_subject(self, mock_decode):
        """Test authentication fails when token missing 'sub' claim."""
        request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="token.without.sub"
        )
        mock_decode.return_value = {"email": "user@example.com"}

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request, credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Token missing subject claim"

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_get_current_user_token_with_empty_subject(self, mock_decode):
        """Test authentication fails when 'sub' claim is empty."""
        request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="token"
        )
        mock_decode.return_value = {"sub": "", "email": "user@example.com"}

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request, credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Token missing subject claim"

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_get_current_user_token_with_none_subject(self, mock_decode):
        """Test authentication fails when 'sub' claim is None."""
        request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="token"
        )
        mock_decode.return_value = {"sub": None, "email": "user@example.com"}

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request, credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_get_current_user_token_without_role(self, mock_decode):
        """Test authentication succeeds with default role when none provided."""
        request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="token"
        )
        mock_decode.return_value = {"sub": "user-123", "email": "user@example.com"}

        user = await get_current_user(request, credentials)

        assert user["role"] == "policyholder"  # Default role

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_get_current_user_token_with_custom_role(self, mock_decode):
        """Test authentication with custom role."""
        request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="token"
        )
        mock_decode.return_value = {
            "sub": "admin-123",
            "email": "admin@example.com",
            "role": "admin"
        }

        user = await get_current_user(request, credentials)

        assert user["role"] == "admin"

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_get_current_user_sets_request_state(self, mock_decode):
        """Test that policyholder_id is set in request state."""
        request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="token"
        )
        mock_decode.return_value = {"sub": "user-123", "email": "user@example.com"}

        await get_current_user(request, credentials)

        assert hasattr(request.state, "policyholder_id")
        assert request.state.policyholder_id == "user-123"

    @pytest.mark.asyncio
    async def test_get_current_user_demo_token_sets_request_state(self):
        """Test that demo token sets request state correctly."""
        request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=DEV_TOKEN
        )

        await get_current_user(request, credentials)

        assert request.state.policyholder_id == "00000000-0000-0000-0000-000000000001"


class TestOptionalAuth:
    """Test optional authentication middleware."""

    @pytest.mark.asyncio
    async def test_optional_auth_no_credentials(self):
        """Test optional auth returns None when no credentials provided."""
        request = MagicMock()

        result = await optional_auth(request, None)

        assert result is None

    @pytest.mark.asyncio
    async def test_optional_auth_demo_token(self):
        """Test optional auth with valid demo token."""
        request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=DEV_TOKEN
        )

        result = await optional_auth(request, credentials)

        assert result is not None
        assert result["policyholder_id"] == "00000000-0000-0000-0000-000000000001"
        assert result["role"] == "demo"

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_optional_auth_valid_token(self, mock_decode):
        """Test optional auth with valid JWT token."""
        request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid.token"
        )
        mock_decode.return_value = {"sub": "user-123", "email": "user@example.com"}

        result = await optional_auth(request, credentials)

        assert result is not None
        assert result["policyholder_id"] == "user-123"

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_optional_auth_invalid_token_returns_none(self, mock_decode):
        """Test optional auth returns None for invalid token instead of raising."""
        request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.token"
        )
        mock_decode.return_value = None

        result = await optional_auth(request, credentials)

        assert result is None

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_optional_auth_token_without_subject_returns_none(self, mock_decode):
        """Test optional auth returns None when token missing subject."""
        request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="token"
        )
        mock_decode.return_value = {"email": "user@example.com"}

        result = await optional_auth(request, credentials)

        assert result is None

    @pytest.mark.asyncio
    async def test_optional_auth_does_not_raise_exception(self):
        """Test that optional_auth never raises HTTPException."""
        request = MagicMock()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="any.invalid.token"
        )

        # Should not raise
        result = await optional_auth(request, credentials)

        # Should return None for invalid tokens
        assert result is None or isinstance(result, dict)


class TestAuthConstants:
    """Test authentication constants are properly defined."""

    def test_secret_key_defined(self):
        """Test that SECRET_KEY is defined."""
        assert SECRET_KEY is not None
        assert isinstance(SECRET_KEY, str)
        assert len(SECRET_KEY) > 0

    def test_algorithm_defined(self):
        """Test that ALGORITHM is defined."""
        assert ALGORITHM is not None
        assert isinstance(ALGORITHM, str)
        assert ALGORITHM == "HS256"

    def test_dev_token_defined(self):
        """Test that DEV_TOKEN is defined."""
        assert DEV_TOKEN is not None
        assert isinstance(DEV_TOKEN, str)
        assert DEV_TOKEN == "insureco-demo-token"

    def test_dev_token_is_simple_string(self):
        """Test that dev token is a simple bypass string, not JWT."""
        # Dev token should not look like a JWT (no dots)
        assert "." not in DEV_TOKEN or DEV_TOKEN.count(".") < 2
