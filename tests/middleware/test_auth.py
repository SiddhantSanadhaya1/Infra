"""Unit tests for authentication middleware"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException
from jose import JWTError


class TestDecodeJwt:
    """Test JWT decoding function"""

    @patch('src.middleware.auth.jwt.decode')
    @patch('src.middleware.auth.SECRET_KEY', 'test-secret')
    @patch('src.middleware.auth.ALGORITHM', 'HS256')
    def test_decode_jwt_valid_token(self, mock_decode):
        """Test decoding valid JWT token"""
        from src.middleware.auth import decode_jwt

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
        mock_decode.assert_called_once_with("valid.jwt.token", "test-secret", algorithms=["HS256"])

    @patch('src.middleware.auth.jwt.decode')
    def test_decode_jwt_invalid_token(self, mock_decode):
        """Test decoding invalid JWT token returns None"""
        from src.middleware.auth import decode_jwt

        mock_decode.side_effect = JWTError("Invalid token")

        result = decode_jwt("invalid.token")

        assert result is None

    @patch('src.middleware.auth.jwt.decode')
    def test_decode_jwt_expired_token(self, mock_decode):
        """Test decoding expired JWT token returns None"""
        from src.middleware.auth import decode_jwt

        mock_decode.side_effect = JWTError("Token expired")

        result = decode_jwt("expired.token")

        assert result is None

    @patch('src.middleware.auth.jwt.decode')
    def test_decode_jwt_malformed_token(self, mock_decode):
        """Test decoding malformed JWT token returns None"""
        from src.middleware.auth import decode_jwt

        mock_decode.side_effect = JWTError("Malformed token")

        result = decode_jwt("malformed")

        assert result is None

    @patch('src.middleware.auth.jwt.decode')
    def test_decode_jwt_empty_token(self, mock_decode):
        """Test decoding empty token"""
        from src.middleware.auth import decode_jwt

        mock_decode.side_effect = JWTError("Empty token")

        result = decode_jwt("")

        assert result is None


@pytest.mark.asyncio
class TestGetCurrentUser:
    """Test get_current_user authentication function"""

    async def test_get_current_user_demo_token(self):
        """Test authentication with demo bypass token"""
        from src.middleware.auth import get_current_user

        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "insureco-demo-token"

        user = await get_current_user(mock_request, mock_credentials)

        assert user["policyholder_id"] == "00000000-0000-0000-0000-000000000001"
        assert user["email"] == "demo@insureco.com"
        assert user["role"] == "demo"
        assert mock_request.state.policyholder_id == "00000000-0000-0000-0000-000000000001"

    async def test_get_current_user_missing_credentials(self):
        """Test authentication fails with missing credentials"""
        from src.middleware.auth import get_current_user

        mock_request = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, None)

        assert exc_info.value.status_code == 401
        assert "Authorization header missing" in exc_info.value.detail

    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_valid_jwt(self, mock_decode):
        """Test authentication with valid JWT token"""
        from src.middleware.auth import get_current_user

        mock_decode.return_value = {
            "sub": "user-123",
            "email": "user@example.com",
            "role": "policyholder"
        }

        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid.jwt.token"

        user = await get_current_user(mock_request, mock_credentials)

        assert user["policyholder_id"] == "user-123"
        assert user["email"] == "user@example.com"
        assert user["role"] == "policyholder"
        assert mock_request.state.policyholder_id == "user-123"

    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_invalid_jwt(self, mock_decode):
        """Test authentication fails with invalid JWT token"""
        from src.middleware.auth import get_current_user

        mock_decode.return_value = None

        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid.jwt.token"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_credentials)

        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail

    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_missing_sub_claim(self, mock_decode):
        """Test authentication fails when JWT missing 'sub' claim"""
        from src.middleware.auth import get_current_user

        mock_decode.return_value = {
            "email": "user@example.com",
            "role": "policyholder"
        }  # Missing 'sub'

        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "token.without.sub"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_credentials)

        assert exc_info.value.status_code == 401
        assert "Token missing subject claim" in exc_info.value.detail

    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_empty_sub_claim(self, mock_decode):
        """Test authentication fails when JWT has empty 'sub' claim"""
        from src.middleware.auth import get_current_user

        mock_decode.return_value = {
            "sub": "",
            "email": "user@example.com"
        }

        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "token.with.empty.sub"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_credentials)

        assert exc_info.value.status_code == 401
        assert "Token missing subject claim" in exc_info.value.detail

    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_none_sub_claim(self, mock_decode):
        """Test authentication fails when JWT has None 'sub' claim"""
        from src.middleware.auth import get_current_user

        mock_decode.return_value = {
            "sub": None,
            "email": "user@example.com"
        }

        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "token.with.none.sub"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_credentials)

        assert exc_info.value.status_code == 401

    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_default_role(self, mock_decode):
        """Test default role is 'policyholder' when not in JWT"""
        from src.middleware.auth import get_current_user

        mock_decode.return_value = {
            "sub": "user-123",
            "email": "user@example.com"
        }  # No role

        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "token.without.role"

        user = await get_current_user(mock_request, mock_credentials)

        assert user["role"] == "policyholder"

    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_custom_role(self, mock_decode):
        """Test authentication with custom role in JWT"""
        from src.middleware.auth import get_current_user

        mock_decode.return_value = {
            "sub": "admin-123",
            "email": "admin@example.com",
            "role": "admin"
        }

        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "admin.jwt.token"

        user = await get_current_user(mock_request, mock_credentials)

        assert user["role"] == "admin"

    @patch('src.middleware.auth.decode_jwt')
    async def test_get_current_user_sets_request_state(self, mock_decode):
        """Test that policyholder_id is set in request state"""
        from src.middleware.auth import get_current_user

        mock_decode.return_value = {
            "sub": "user-456",
            "email": "user@example.com"
        }

        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid.token"

        await get_current_user(mock_request, mock_credentials)

        assert hasattr(mock_request.state, 'policyholder_id')
        assert mock_request.state.policyholder_id == "user-456"


@pytest.mark.asyncio
class TestOptionalAuth:
    """Test optional_auth function"""

    async def test_optional_auth_no_credentials(self):
        """Test optional auth returns None when no credentials"""
        from src.middleware.auth import optional_auth

        mock_request = MagicMock()

        result = await optional_auth(mock_request, None)

        assert result is None

    @patch('src.middleware.auth.get_current_user')
    async def test_optional_auth_valid_credentials(self, mock_get_current_user):
        """Test optional auth returns user when valid credentials"""
        from src.middleware.auth import optional_auth

        mock_get_current_user.return_value = {
            "policyholder_id": "user-123",
            "email": "user@example.com"
        }

        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid.token"

        result = await optional_auth(mock_request, mock_credentials)

        assert result == {
            "policyholder_id": "user-123",
            "email": "user@example.com"
        }

    @patch('src.middleware.auth.get_current_user')
    async def test_optional_auth_invalid_credentials(self, mock_get_current_user):
        """Test optional auth returns None on authentication failure"""
        from src.middleware.auth import optional_auth

        mock_get_current_user.side_effect = HTTPException(status_code=401, detail="Invalid token")

        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid.token"

        result = await optional_auth(mock_request, mock_credentials)

        assert result is None

    @patch('src.middleware.auth.get_current_user')
    async def test_optional_auth_demo_token(self, mock_get_current_user):
        """Test optional auth works with demo token"""
        from src.middleware.auth import optional_auth

        mock_get_current_user.return_value = {
            "policyholder_id": "00000000-0000-0000-0000-000000000001",
            "email": "demo@insureco.com",
            "role": "demo"
        }

        mock_request = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.credentials = "insureco-demo-token"

        result = await optional_auth(mock_request, mock_credentials)

        assert result is not None
        assert result["role"] == "demo"


class TestAuthConstants:
    """Test authentication constants"""

    @patch.dict('os.environ', {}, clear=True)
    def test_secret_key_default(self):
        """Test default SECRET_KEY value"""
        import sys
        if 'src.middleware.auth' in sys.modules:
            del sys.modules['src.middleware.auth']

        from src.middleware.auth import SECRET_KEY
        assert SECRET_KEY == "insureco-secret-key-for-dev-only"

    @patch.dict('os.environ', {}, clear=True)
    def test_algorithm_default(self):
        """Test default ALGORITHM value"""
        import sys
        if 'src.middleware.auth' in sys.modules:
            del sys.modules['src.middleware.auth']

        from src.middleware.auth import ALGORITHM
        assert ALGORITHM == "HS256"

    def test_dev_token_value(self):
        """Test DEV_TOKEN constant value"""
        from src.middleware.auth import DEV_TOKEN
        assert DEV_TOKEN == "insureco-demo-token"
