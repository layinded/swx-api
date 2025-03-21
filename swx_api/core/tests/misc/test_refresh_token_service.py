import pytest
import jwt
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
from sqlmodel import SQLModel, Session, create_engine
from fastapi import HTTPException, Request
from swx_api.core.config.settings import settings
from swx_api.core.models.refresh_token import RefreshToken
from swx_api.core.security.refresh_token_service import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    revoke_refresh_token,
    revoke_all_tokens,
)


# Setup test database
@pytest.fixture(scope="function")
def test_db():
    """Fixture to create a fresh in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def mock_request():
    """Mock request object for translation helper."""
    return MagicMock()


@pytest.fixture
def mock_refresh_token(test_db):
    """Create a mock refresh token for testing."""
    token = RefreshToken(
        token="mock_refresh_token",
        user_email="test@example.com",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    test_db.add(token)
    test_db.commit()
    test_db.refresh(token)
    return token


# ---------- ACCESS TOKEN TESTS ----------


def test_create_access_token():
    """Test generating an access token."""
    access_token = create_access_token(
        email="test@example.com",
        expires_delta=timedelta(minutes=30),
        auth_provider="local",
    )

    assert isinstance(access_token, str)

    decoded_token = jwt.decode(
        access_token,
        settings.SECRET_KEY,
        algorithms=[settings.PASSWORD_SECURITY_ALGORITHM],
    )

    assert decoded_token["sub"] == "test@example.com"
    assert decoded_token["auth_provider"] == "local"


# ---------- REFRESH TOKEN CREATION TESTS ----------


def test_create_refresh_token(test_db):
    """Test creating and storing a refresh token in the database."""
    refresh_token = create_refresh_token(
        session=test_db,
        email="test@example.com",
        expires_delta=timedelta(days=7),
        auth_provider="local",
    )

    assert isinstance(refresh_token, str)

    # Check if token is stored in the database
    stored_token = test_db.exec(
        select(RefreshToken).where(RefreshToken.user_email == "test@example.com")
    ).first()

    assert stored_token is not None
    assert stored_token.token == refresh_token


# ---------- REFRESH TOKEN VERIFICATION TESTS ----------


@patch("jwt.decode")
@patch("sqlmodel.Session.exec")
def test_verify_valid_refresh_token(
    mock_db_exec, mock_jwt_decode, test_db, mock_request, mock_refresh_token
):
    """Test verifying a valid refresh token."""
    mock_jwt_decode.return_value = {"sub": "test@example.com", "auth_provider": "local"}
    mock_db_exec.return_value.first.return_value = mock_refresh_token

    email, auth_provider = verify_refresh_token(
        session=test_db, refresh_token="mock_refresh_token", request=mock_request
    )

    assert email == "test@example.com"
    assert auth_provider == "local"


@patch("jwt.decode", side_effect=jwt.ExpiredSignatureError)
def test_verify_expired_refresh_token(mock_jwt_decode, test_db, mock_request):
    """Test verifying an expired refresh token fails."""
    with pytest.raises(HTTPException) as exc_info:
        verify_refresh_token(
            session=test_db, refresh_token="expired_token", request=mock_request
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "refresh_token_expired"


@patch("jwt.decode", side_effect=jwt.InvalidTokenError)
def test_verify_invalid_refresh_token(mock_jwt_decode, test_db, mock_request):
    """Test verifying an invalid refresh token fails."""
    with pytest.raises(HTTPException) as exc_info:
        verify_refresh_token(
            session=test_db, refresh_token="invalid_token", request=mock_request
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "invalid_refresh_token"


# ---------- REFRESH TOKEN REVOCATION TESTS ----------


def test_revoke_existing_refresh_token(test_db, mock_refresh_token):
    """Test revoking an existing refresh token."""
    revoked = revoke_refresh_token(test_db, "mock_refresh_token")

    assert revoked is True

    # Ensure the token is deleted
    token = test_db.exec(
        select(RefreshToken).where(RefreshToken.token == "mock_refresh_token")
    ).first()
    assert token is None


def test_revoke_non_existent_refresh_token(test_db):
    """Test revoking a non-existent refresh token returns True (idempotent)."""
    revoked = revoke_refresh_token(test_db, "non_existent_token")

    assert revoked is True


# ---------- REVOKE ALL TOKENS TEST ----------


def test_revoke_all_tokens(test_db):
    """Test revoking all refresh tokens for a user."""
    # Create multiple refresh tokens for a single user
    refresh_token_1 = RefreshToken(
        token="token1",
        user_email="test@example.com",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    refresh_token_2 = RefreshToken(
        token="token2",
        user_email="test@example.com",
        expires_at=datetime.now(timezone.utc) + timedelta(days=2),
    )
    test_db.add(refresh_token_1)
    test_db.add(refresh_token_2)
    test_db.commit()

    # Revoke all tokens
    revoke_all_tokens(test_db, "test@example.com")

    # Ensure all tokens are deleted
    tokens = test_db.exec(
        select(RefreshToken).where(RefreshToken.user_email == "test@example.com")
    ).all()
    assert len(tokens) == 0
