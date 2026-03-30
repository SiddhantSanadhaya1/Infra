import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from src.middleware.auth import decode_jwt, get_current_user, optional_auth


class TestDecodeJWT:
    """Test suite for decode_jwt function."""

    @patch("src.middleware.auth.jwt")
    @patch("src.middleware.auth.SECRET_KEY", "test-secret")
    @patch("src.middleware.auth.ALGORITHM", "HS256")
    def test_decode_jwt_success(self, mock_jwt):
        """Test successful JWT decoding."""
        mock_jwt.decode.return_value = {"sub": "user-123", "email": "test@example.com"}

        result = decode_jwt("valid-token")

        assert result == {"sub": "user-123", "email": "test@example.com"}
        mock_jwt.decode.assert_called_once_with("valid-token", "test-secret", algorithms=["HS256"])

    @patch("src.middleware.auth.jwt")
    def test_decode_jwt_invalid_token(self, mock_jwt):
        """Test JWT decoding with invalid token."""
        from jose import JWTError
        mock_jwt.decode.side_effect = JWTError("Invalid token")

        result = decode_jwt("invalid-token")

        assert result is None

    @patch("src.middleware.auth.jwt")
    def test_decode_jwt_expired_token(self, mock_jwt):
        """Test JWT decoding with expired token."""
        from jose import JWTError
        mock_jwt.decode.side_effect = JWTError("Token expired")

        result = decode_jwt("expired-token")

        assert result is None

    @patch("src.middleware.auth.jwt")
    @patch("src.middleware.auth.SECRET_KEY", "another-secret")
    def test_decode_jwt_uses_configured_secret(self, mock_jwt):
        """Test that configured secret key is used."""
        mock_jwt.decode.return_value = {"sub": "user-123"}

        decode_jwt("token")

        call_args = mock_jwt.decode.call_args
        assert call_args[0][1] == "another-secret"


class TestGetCurrentUser:
    """Test suite for get_current_user dependency."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        request = Mock()
        request.state = Mock()
        return request

    @pytest.mark.asyncio
    async def test_get_current_user_no_credentials(self, mock_request):
        """Test authentication failure when no credentials provided."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, None)

        assert exc_info.value.status_code == 401
        assert "Authorization header missing" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("src.middleware.auth.DEV_TOKEN", "insureco-demo-token")
    async def test_get_current_user_dev_token(self, mock_request):
        """Test authentication with development bypass token."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="insureco-demo-token"
        )

        result = await get_current_user(mock_request, credentials)

        assert result["policyholder_id"] == "00000000-0000-0000-0000-000000000001"
        assert result["email"] == "demo@insureco.com"
        assert result["role"] == "demo"
        assert mock_request.state.policyholder_id == "00000000-0000-0000-0000-000000000001"

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_get_current_user_valid_jwt(self, mock_decode, mock_request):
        """Test authentication with valid JWT token."""
        mock_decode.return_value = {
            "sub": "user-123",
            "email": "test@example.com",
            "role": "policyholder"
        }

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid-jwt-token"
        )

        result = await get_current_user(mock_request, credentials)

        assert result["policyholder_id"] == "user-123"
        assert result["email"] == "test@example.com"
        assert result["role"] == "policyholder"
        assert mock_request.state.policyholder_id == "user-123"

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_get_current_user_invalid_jwt(self, mock_decode, mock_request):
        """Test authentication with invalid JWT token."""
        mock_decode.return_value = None

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid-jwt-token"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, credentials)

        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_get_current_user_missing_sub_claim(self, mock_decode, mock_request):
        """Test authentication when JWT is missing subject claim."""
        mock_decode.return_value = {"email": "test@example.com"}

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="jwt-without-sub"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, credentials)

        assert exc_info.value.status_code == 401
        assert "Token missing subject claim" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_get_current_user_sets_request_state(self, mock_decode, mock_request):
        """Test that policyholder_id is set in request state."""
        mock_decode.return_value = {
            "sub": "user-456",
            "email": "user@example.com"
        }

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid-token"
        )

        await get_current_user(mock_request, credentials)

        assert mock_request.state.policyholder_id == "user-456"

    @pytest.mark.asyncio
    @patch("src.middleware.auth.decode_jwt")
    async def test_get_current_user_default_role(self, mock_decode, mock_request):
        """Test that default role is set when not in token."""
        mock_decode.return_value = {
            "sub": "user-789",
            "email": "user@example.com"
        }

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="token-no-role"
        )

        result = await get_current_user(mock_request, credentials)

        assert result["role"] == "policyholder"


class TestOptionalAuth:
    """Test suite for optional_auth dependency."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        request = Mock()
        request.state = Mock()
        return request

    @pytest.mark.asyncio
    async def test_optional_auth_no_credentials(self, mock_request):
        """Test optional auth with no credentials returns None."""
        result = await optional_auth(mock_request, None)

        assert result is None

    @pytest.mark.asyncio
    @patch("src.middleware.auth.get_current_user")
    async def test_optional_auth_valid_credentials(self, mock_get_user, mock_request):
        """Test optional auth with valid credentials."""
        mock_get_user.return_value = {
            "policyholder_id": "user-123",
            "email": "test@example.com",
            "role": "policyholder"
        }

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid-token"
        )

        result = await optional_auth(mock_request, credentials)

        assert result == {
            "policyholder_id": "user-123",
            "email": "test@example.com",
            "role": "policyholder"
        }

    @pytest.mark.asyncio
    @patch("src.middleware.auth.get_current_user")
    async def test_optional_auth_invalid_credentials(self, mock_get_user, mock_request):
        """Test optional auth with invalid credentials returns None."""
        mock_get_user.side_effect = HTTPException(status_code=401, detail="Invalid token")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid-token"
        )

        result = await optional_auth(mock_request, credentials)

        assert result is None

    @pytest.mark.asyncio
    @patch("src.middleware.auth.DEV_TOKEN", "insureco-demo-token")
    @patch("src.middleware.auth.get_current_user")
    async def test_optional_auth_dev_token(self, mock_get_user, mock_request):
        """Test optional auth with dev token."""
        mock_get_user.return_value = {
            "policyholder_id": "00000000-0000-0000-0000-000000000001",
            "email": "demo@insureco.com",
            "role": "demo"
        }

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="insureco-demo-token"
        )

        result = await optional_auth(mock_request, credentials)

        assert result is not None
        assert result["role"] == "demo"


class TestAuthConfiguration:
    """Test suite for authentication configuration."""

    @patch("src.middleware.auth.SECRET_KEY", "test-secret-key")
    def test_secret_key_configured(self):
        """Test that SECRET_KEY is configured."""
        from src.middleware.auth import SECRET_KEY
        assert SECRET_KEY == "test-secret-key"

    @patch("src.middleware.auth.ALGORITHM", "HS256")
    def test_algorithm_configured(self):
        """Test that ALGORITHM is configured."""
        from src.middleware.auth import ALGORITHM
        assert ALGORITHM == "HS256"

    @patch("src.middleware.auth.DEV_TOKEN", "insureco-demo-token")
    def test_dev_token_configured(self):
        """Test that DEV_TOKEN is configured."""
        from src.middleware.auth import DEV_TOKEN
        assert DEV_TOKEN == "insureco-demo-token"
