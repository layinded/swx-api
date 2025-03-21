import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, Request
from datetime import timedelta
from sqlmodel import SQLModel, Session, create_engine
from swx_api.core.models.user import UserCreate, UserNewPassword
from swx_api.core.models.token import Token, TokenRefreshRequest
from swx_api.core.services.auth_service import (
    login_user_service,
    login_social_user_service,
    refresh_access_token_service,
    register_user_service,
    logout_service,
    recover_password_service,
    reset_password_service,
)
from swx_api.core.security.password_security import get_password_hash


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
def mock_user():
    """Mock user object for testing."""
    return MagicMock(
        email="test@example.com",
        hashed_password=get_password_hash("SecurePass123"),
        is_active=True,
    )


# ---------- LOGIN TESTS ----------


@patch("swx_api.core.repositories.user_repository.authenticate_user")
@patch(
    "swx_api.core.security.refresh_token_service.create_access_token",
    return_value="mock_access_token",
)
@patch(
    "swx_api.core.security.refresh_token_service.create_refresh_token",
    return_value="mock_refresh_token",
)
def test_login_user_service_success(
    mock_create_refresh, mock_create_access, mock_authenticate, test_db, mock_request
):
    """Test successful user login."""
    mock_authenticate.return_value = mock_user

    form_data = MagicMock(username="test@example.com", password="SecurePass123")
    token = login_user_service(
        session=test_db, form_data=form_data, request=mock_request
    )

    assert token.access_token == "mock_access_token"
    assert token.refresh_token == "mock_refresh_token"


@patch("swx_api.core.repositories.user_repository.authenticate_user", return_value=None)
@patch(
    "swx_api.core.utils.language_helper.translate",
    return_value="Incorrect email or password",
)
def test_login_user_service_failure(
    mock_translate, mock_authenticate, test_db, mock_request
):
    """Test login with incorrect credentials fails."""
    form_data = MagicMock(username="wrong@example.com", password="WrongPass")

    with pytest.raises(HTTPException) as exc_info:
        login_user_service(session=test_db, form_data=form_data, request=mock_request)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Incorrect email or password"


# ---------- SOCIAL LOGIN TESTS ----------


@patch(
    "swx_api.core.security.refresh_token_service.create_access_token",
    return_value="mock_access_token",
)
@patch(
    "swx_api.core.security.refresh_token_service.create_refresh_token",
    return_value="mock_refresh_token",
)
def test_login_social_user_service(mock_create_refresh, mock_create_access, test_db):
    """Test social user login."""
    token = login_social_user_service(session=test_db, user_email="social@example.com")

    assert token.access_token == "mock_access_token"
    assert token.refresh_token == "mock_refresh_token"


# ---------- REFRESH TOKEN TESTS ----------


@patch(
    "swx_api.core.security.refresh_token_service.verify_refresh_token",
    return_value=("user@example.com", "local"),
)
@patch(
    "swx_api.core.security.refresh_token_service.create_access_token",
    return_value="new_access_token",
)
@patch(
    "swx_api.core.security.refresh_token_service.create_refresh_token",
    return_value="new_refresh_token",
)
def test_refresh_access_token_service_success(
    mock_create_refresh, mock_create_access, mock_verify, test_db, mock_request
):
    """Test refreshing an access token successfully."""
    request_data = TokenRefreshRequest(refresh_token="valid_refresh_token")
    token = refresh_access_token_service(
        session=test_db, request_data=request_data, request=mock_request
    )

    assert token.access_token == "new_access_token"
    assert token.refresh_token == "new_refresh_token"


@patch(
    "swx_api.core.security.refresh_token_service.verify_refresh_token",
    return_value=None,
)
@patch(
    "swx_api.core.utils.language_helper.translate",
    return_value="Invalid or expired refresh token",
)
def test_refresh_access_token_service_failure(
    mock_translate, mock_verify, test_db, mock_request
):
    """Test refreshing a token with an invalid refresh token fails."""
    request_data = TokenRefreshRequest(refresh_token="invalid_token")

    with pytest.raises(HTTPException) as exc_info:
        refresh_access_token_service(
            session=test_db, request_data=request_data, request=mock_request
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or expired refresh token"


# ---------- USER REGISTRATION TESTS ----------


@patch("swx_api.core.repositories.user_repository.create_user")
def test_register_user_service_success(mock_create_user, test_db, mock_request):
    """Test registering a new user successfully."""
    user_data = UserCreate(email="newuser@example.com", password="SecurePass123")
    mock_create_user.return_value = {"email": "newuser@example.com"}

    response = register_user_service(
        session=test_db, user_in=user_data, request=mock_request
    )

    assert response["email"] == "newuser@example.com"


# ---------- PASSWORD RECOVERY TESTS ----------


@patch(
    "swx_api.core.repositories.user_repository.get_user_by_email",
    return_value=mock_user,
)
@patch(
    "swx_api.core.security.password_security.generate_password_reset_token",
    return_value="mock_reset_token",
)
@patch("swx_api.core.email.email_service.send_email")
def test_recover_password_service_success(
    mock_send_email, mock_generate_token, mock_get_user, test_db, mock_request
):
    """Test successful password recovery email."""
    response = recover_password_service(
        email="test@example.com", session=test_db, request=mock_request
    )

    assert "message" in response


@patch("swx_api.core.repositories.user_repository.get_user_by_email", return_value=None)
@patch(
    "swx_api.core.utils.language_helper.translate", return_value="User email not found"
)
def test_recover_password_service_failure(
    mock_translate, mock_get_user, test_db, mock_request
):
    """Test password recovery for non-existent user fails."""
    with pytest.raises(HTTPException) as exc_info:
        recover_password_service(
            email="wrong@example.com", session=test_db, request=mock_request
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User email not found"


# ---------- PASSWORD RESET TESTS ----------


@patch(
    "swx_api.core.security.password_security.verify_password_reset_token",
    return_value="test@example.com",
)
@patch(
    "swx_api.core.repositories.user_repository.get_user_by_email",
    return_value=mock_user,
)
@patch(
    "swx_api.core.security.password_security.get_password_hash",
    return_value="hashed_new_pass",
)
@patch("swx_api.core.security.refresh_token_service.revoke_all_tokens")
def test_reset_password_service_success(
    mock_revoke_tokens,
    mock_hash,
    mock_get_user,
    mock_verify_token,
    test_db,
    mock_request,
):
    """Test resetting a password successfully."""
    reset_data = UserNewPassword(token="valid_token", new_password="NewSecurePass")

    response = reset_password_service(
        session=test_db, body=reset_data, request=mock_request
    )

    assert "message" in response


@patch(
    "swx_api.core.security.password_security.verify_password_reset_token",
    return_value=None,
)
@patch(
    "swx_api.core.utils.language_helper.translate",
    return_value="Invalid or expired reset token",
)
def test_reset_password_service_invalid_token(
    mock_translate, mock_verify_token, test_db, mock_request
):
    """Test password reset with an invalid token fails."""
    reset_data = UserNewPassword(token="invalid_token", new_password="NewSecurePass")

    with pytest.raises(HTTPException) as exc_info:
        reset_password_service(session=test_db, body=reset_data, request=mock_request)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid or expired reset token"
