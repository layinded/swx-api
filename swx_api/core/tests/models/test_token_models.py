import pytest
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from sqlmodel import SQLModel
from pydantic import ValidationError
from swx_api.core.models.token import (
    Token,
    TokenPayload,
    TokenRefreshRequest,
    NewPassword,
    RefreshTokenRequest,
    LogoutRequest,
)

# JWT Secret & Algorithm (for testing only)
JWT_SECRET = "testsecret"
JWT_ALGORITHM = "HS256"


@pytest.fixture
def valid_access_token():
    """Generate a valid JWT access token."""
    payload = {
        "sub": "user@example.com",
        "auth_provider": "local",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),  # Expires in 30 mins
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@pytest.fixture
def expired_access_token():
    """Generate an expired JWT token."""
    payload = {
        "sub": "user@example.com",
        "auth_provider": "local",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=5),  # Expired 5 mins ago
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def test_token_model():
    """Test token structure."""
    token = Token(
        access_token="valid_access_token", refresh_token="valid_refresh_token"
    )

    assert token.access_token == "valid_access_token"
    assert token.refresh_token == "valid_refresh_token"
    assert token.token_type == "bearer"


def test_token_payload():
    """Test token payload model."""
    payload = TokenPayload(sub="user@example.com", auth_provider="google")

    assert payload.sub == "user@example.com"
    assert payload.auth_provider == "google"


def test_token_refresh_request():
    """Test refresh token request structure."""
    refresh_request = TokenRefreshRequest(refresh_token="valid_refresh_token")

    assert refresh_request.refresh_token == "valid_refresh_token"


def test_logout_request():
    """Test logout request model."""
    logout_request = LogoutRequest(refresh_token="logout_refresh_token")

    assert logout_request.refresh_token == "logout_refresh_token"


def test_new_password_validation():
    """Test new password validation constraints."""
    valid_password = NewPassword(token="reset_token", new_password="SecurePass123")

    assert valid_password.token == "reset_token"
    assert valid_password.new_password == "SecurePass123"

    with pytest.raises(ValidationError):
        NewPassword(token="reset_token", new_password="short")  # Too short


def test_jwt_encoding_and_decoding(valid_access_token):
    """Test JWT encoding and decoding for token verification."""
    decoded = jwt.decode(valid_access_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

    assert decoded["sub"] == "user@example.com"
    assert decoded["auth_provider"] == "local"
    assert "exp" in decoded


def test_expired_jwt_token(expired_access_token):
    """Test handling of expired JWT tokens."""
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(expired_access_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def test_invalid_jwt_token():
    """Test decoding an invalid JWT token."""
    invalid_token = "invalid.token.string"

    with pytest.raises(jwt.DecodeError):
        jwt.decode(invalid_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
