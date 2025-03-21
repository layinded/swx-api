import pytest
import jwt
from datetime import datetime, timedelta, timezone
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from swx_api.core.security.password_security import (
    verify_password,
    get_password_hash,
    generate_password_reset_token,
    verify_password_reset_token,
)
from swx_api.core.config.settings import settings


# ---------- PASSWORD HASHING TESTS ----------


def test_get_password_hash():
    """Test password hashing produces a valid hash."""
    password = "SecurePass123"
    hashed_password = get_password_hash(password)

    assert isinstance(hashed_password, str)
    assert hashed_password != password  # Ensure it's hashed


def test_verify_password():
    """Test password verification succeeds for the correct password."""
    password = "SecurePass123"
    hashed_password = get_password_hash(password)

    assert verify_password(password, hashed_password) is True


def test_verify_password_failure():
    """Test password verification fails for incorrect passwords."""
    password = "SecurePass123"
    hashed_password = get_password_hash(password)

    assert verify_password("WrongPass", hashed_password) is False


# ---------- PASSWORD RESET TOKEN TESTS ----------


def test_generate_password_reset_token():
    """Test generating a password reset token."""
    email = "test@example.com"
    token = generate_password_reset_token(email)

    assert isinstance(token, str)


def test_generate_password_reset_token_social_account():
    """Test password reset token is not generated for social login users."""
    email = "test@example.com"
    token = generate_password_reset_token(email, auth_provider="google")

    assert token is None  # Should not generate a token for non-local accounts


def test_verify_password_reset_token():
    """Test verifying a valid password reset token."""
    email = "test@example.com"
    token = generate_password_reset_token(email)
    verified_email = verify_password_reset_token(token)

    assert verified_email == email


def test_verify_expired_password_reset_token():
    """Test verifying an expired password reset token fails."""
    email = "test@example.com"
    expired_token = jwt.encode(
        {
            "exp": (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp(),
            "sub": email,
        },
        settings.SECRET_KEY,
        algorithm=settings.PASSWORD_SECURITY_ALGORITHM,
    )

    assert verify_password_reset_token(expired_token) is None


def test_verify_invalid_password_reset_token():
    """Test verifying an invalid password reset token fails."""
    invalid_token = "invalid.jwt.token"

    assert verify_password_reset_token(invalid_token) is None
