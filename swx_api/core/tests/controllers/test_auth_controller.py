import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, Request
from sqlmodel import SQLModel, Session, create_engine
from swx_api.core.models.user import UserCreate, UserNewPassword
from swx_api.core.models.token import Token, TokenRefreshRequest
from swx_api.core.controllers.auth_controller import (
    login_controller,
    login_social_user_controller,
    refresh_token_controller,
    register_controller,
    logout_controller,
    recover_password_controller,
    reset_password_controller,
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
def mock_user():
    """Mock user object for testing."""
    return MagicMock(email="test@example.com", is_active=True)


# ---------- LOGIN TESTS ----------


@patch("swx_api.core.services.auth_service.login_user_service")
def test_login_controller_success(mock_login_service, test_db, mock_request):
    """Test successful user login."""
    mock_login_service.return_value = Token(
        access_token="mock_access_token", refresh_token="mock_refresh_token"
    )

    form_data = MagicMock(username="test@example.com", password="SecurePass123")
    response = login_controller(
        session=test_db, form_data=form_data, request=mock_request
    )

    assert response.access_token == "mock_access_token"
    assert response.refresh_token == "mock_refresh_token"


@patch(
    "swx_api.core.services.auth_service.login_user_service",
    side_effect=HTTPException(status_code=400, detail="Incorrect credentials"),
)
def test_login_controller_failure(mock_login_service, test_db, mock_request):
    """Test login failure due to incorrect credentials."""
    form_data = MagicMock(username="wrong@example.com", password="WrongPass")

    with pytest.raises(HTTPException) as exc_info:
        login_controller(session=test_db, form_data=form_data, request=mock_request)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Incorrect credentials"


# ---------- SOCIAL LOGIN TEST ----------


@patch("swx_api.core.services.auth_service.login_social_user_service")
def test_login_social_user_controller(mock_login_social_service, test_db):
    """Test social user login."""
    mock_login_social_service.return_value = Token(
        access_token="mock_access_token", refresh_token="mock_refresh_token"
    )

    form_data = "social@example.com"
    response = login_social_user_controller(session=test_db, form_data=form_data)

    assert response.access_token == "mock_access_token"
    assert response.refresh_token == "mock_refresh_token"


# ---------- REFRESH TOKEN TESTS ----------


@patch("swx_api.core.services.auth_service.refresh_access_token_service")
def test_refresh_token_controller_success(
    mock_refresh_token_service, test_db, mock_request
):
    """Test refreshing an access token successfully."""
    mock_refresh_token_service.return_value = Token(
        access_token="new_access_token", refresh_token="new_refresh_token"
    )

    request_data = TokenRefreshRequest(refresh_token="valid_refresh_token")
    response = refresh_token_controller(
        session=test_db, request_data=request_data, request=mock_request
    )

    assert response.access_token == "new_access_token"
    assert response.refresh_token == "new_refresh_token"


@patch(
    "swx_api.core.services.auth_service.refresh_access_token_service",
    side_effect=HTTPException(status_code=401, detail="Invalid token"),
)
def test_refresh_token_controller_failure(
    mock_refresh_token_service, test_db, mock_request
):
    """Test refreshing a token with an invalid refresh token fails."""
    request_data = TokenRefreshRequest(refresh_token="invalid_token")

    with pytest.raises(HTTPException) as exc_info:
        refresh_token_controller(
            session=test_db, request_data=request_data, request=mock_request
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token"


# ---------- USER REGISTRATION TESTS ----------


@patch("swx_api.core.services.auth_service.register_user_service")
def test_register_controller_success(mock_register_service, test_db, mock_request):
    """Test registering a new user successfully."""
    user_data = UserCreate(email="newuser@example.com", password="SecurePass123")
    mock_register_service.return_value = {"email": "newuser@example.com"}

    response = register_controller(
        session=test_db, user_in=user_data, request=mock_request
    )

    assert response["email"] == "newuser@example.com"


# ---------- LOGOUT TESTS ----------


@patch("swx_api.core.services.auth_service.logout_service")
def test_logout_controller_success(mock_logout_service, test_db, mock_request):
    """Test user logout successfully."""
    mock_logout_service.return_value = {"message": "Logged out successfully"}

    request_data = TokenRefreshRequest(refresh_token="valid_refresh_token")
    response = logout_controller(
        session=test_db, request_data=request_data, request=mock_request
    )

    assert response["message"] == "Logged out successfully"


# ---------- PASSWORD RECOVERY TESTS ----------


@patch("swx_api.core.services.auth_service.recover_password_service")
def test_recover_password_controller_success(
    mock_recover_service, test_db, mock_request
):
    """Test successful password recovery."""
    mock_recover_service.return_value = {
        "message": "Password recovery email sent successfully"
    }

    response = recover_password_controller(
        email="test@example.com", session=test_db, request=mock_request
    )

    assert response["message"] == "Password recovery email sent successfully"


# ---------- PASSWORD RESET TESTS ----------


@patch("swx_api.core.services.auth_service.reset_password_service")
def test_reset_password_controller_success(mock_reset_service, test_db, mock_request):
    """Test resetting a password successfully."""
    reset_data = UserNewPassword(token="valid_token", new_password="NewSecurePass")
    mock_reset_service.return_value = {"message": "Password reset successful"}

    response = reset_password_controller(
        session=test_db, body=reset_data, request=mock_request
    )

    assert response["message"] == "Password reset successful"


@patch(
    "swx_api.core.services.auth_service.reset_password_service",
    side_effect=HTTPException(status_code=400, detail="Invalid reset token"),
)
def test_reset_password_controller_failure(mock_reset_service, test_db, mock_request):
    """Test password reset with an invalid token fails."""
    reset_data = UserNewPassword(token="invalid_token", new_password="NewSecurePass")

    with pytest.raises(HTTPException) as exc_info:
        reset_password_controller(
            session=test_db, body=reset_data, request=mock_request
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid reset token"
