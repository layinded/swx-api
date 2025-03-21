import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from swx_api.core.models.token import Token, TokenRefreshRequest
from swx_api.core.models.user import UserCreate, UserNewPassword
from swx_api.main import app  # Import FastAPI app instance

# Create a test client for FastAPI
client = TestClient(app)


# Setup test database
@pytest.fixture(scope="function")
def test_db():
    """Fixture to create a fresh in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


# ---------- LOGIN TESTS ----------


@patch("swx_api.core.controllers.auth_controller.login_controller")
def test_login_success(mock_login_controller, test_db):
    """Test successful user login."""
    mock_login_controller.return_value = Token(
        access_token="mock_access_token", refresh_token="mock_refresh_token"
    )

    response = client.post(
        "/auth/", data={"username": "test@example.com", "password": "SecurePass123"}
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "mock_access_token"
    assert response.json()["refresh_token"] == "mock_refresh_token"


@patch("swx_api.core.controllers.auth_controller.login_controller")
def test_login_failure(mock_login_controller, test_db):
    """Test login failure with incorrect credentials."""
    mock_login_controller.side_effect = ValueError("Incorrect credentials")

    response = client.post(
        "/auth/", data={"username": "wrong@example.com", "password": "WrongPass"}
    )

    assert (
        response.status_code == 400
    )  # Expected FastAPI to return 400 for invalid credentials


# ---------- REFRESH TOKEN TESTS ----------


@patch("swx_api.core.controllers.auth_controller.refresh_token_controller")
def test_refresh_token_success(mock_refresh_token_controller, test_db):
    """Test successful token refresh."""
    mock_refresh_token_controller.return_value = Token(
        access_token="new_access_token", refresh_token="new_refresh_token"
    )

    response = client.post(
        "/auth/refresh", json={"refresh_token": "valid_refresh_token"}
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "new_access_token"
    assert response.json()["refresh_token"] == "new_refresh_token"


# ---------- REGISTRATION TESTS ----------


@patch("swx_api.core.controllers.auth_controller.register_controller")
def test_register_user_success(mock_register_controller, test_db):
    """Test registering a new user successfully."""
    mock_register_controller.return_value = {"email": "newuser@example.com"}

    response = client.post(
        "/auth/register",
        json={"email": "newuser@example.com", "password": "SecurePass123"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "newuser@example.com"


# ---------- LOGOUT TESTS ----------


@patch("swx_api.core.controllers.auth_controller.logout_controller")
def test_logout_success(mock_logout_controller, test_db):
    """Test user logout successfully."""
    mock_logout_controller.return_value = {"message": "Logged out successfully"}

    response = client.post(
        "/auth/revoke", json={"refresh_token": "valid_refresh_token"}
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"


# ---------- PASSWORD RECOVERY TESTS ----------


@patch("swx_api.core.controllers.auth_controller.recover_password_controller")
def test_recover_password_success(mock_recover_password_controller, test_db):
    """Test successful password recovery email."""
    mock_recover_password_controller.return_value = {
        "message": "Password recovery email sent successfully"
    }

    response = client.post("/auth/password/recover/test@example.com")

    assert response.status_code == 200
    assert response.json()["message"] == "Password recovery email sent successfully"


# ---------- PASSWORD RESET TESTS ----------


@patch("swx_api.core.controllers.auth_controller.reset_password_controller")
def test_reset_password_success(mock_reset_password_controller, test_db):
    """Test resetting a password successfully."""
    mock_reset_password_controller.return_value = {
        "message": "Password reset successful"
    }

    response = client.post(
        "/auth/password/reset",
        json={"token": "valid_token", "new_password": "NewSecurePass"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Password reset successful"
