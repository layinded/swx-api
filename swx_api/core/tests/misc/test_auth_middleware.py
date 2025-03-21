import pytest
import jwt
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, Request
from sqlmodel import SQLModel, Session, create_engine
from swx_api.core.config.settings import settings
from swx_api.core.models.token import TokenPayload
from swx_api.core.models.user import User
from swx_api.core.security.dependencies import (
    get_current_user,
    get_current_active_superuser,
    require_roles,
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
    return User(email="test@example.com", is_active=True, is_superuser=False)


@pytest.fixture
def mock_superuser():
    """Mock superuser object for testing."""
    return User(email="admin@example.com", is_active=True, is_superuser=True)


# ---------- GET CURRENT USER TESTS ----------


@patch("jwt.decode")
@patch("sqlmodel.Session.exec")
def test_get_current_user_success(
    mock_db_exec, mock_jwt_decode, test_db, mock_request, mock_user
):
    """Test retrieving the current authenticated user from a valid JWT token."""
    mock_jwt_decode.return_value = {"sub": "test@example.com"}
    mock_db_exec.return_value.first.return_value = mock_user

    user = get_current_user(session=test_db, token="valid_token", request=mock_request)

    assert user.email == "test@example.com"


@patch("jwt.decode", side_effect=jwt.ExpiredSignatureError)
def test_get_current_user_expired_token(mock_jwt_decode, test_db, mock_request):
    """Test expired JWT token results in 401 Unauthorized."""
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(session=test_db, token="expired_token", request=mock_request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "could_not_validate_credentials"


@patch("jwt.decode", side_effect=jwt.InvalidTokenError)
def test_get_current_user_invalid_token(mock_jwt_decode, test_db, mock_request):
    """Test invalid JWT token results in 401 Unauthorized."""
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(session=test_db, token="invalid_token", request=mock_request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "could_not_validate_credentials"


@patch("jwt.decode")
@patch("sqlmodel.Session.exec")
def test_get_current_user_inactive_user(
    mock_db_exec, mock_jwt_decode, test_db, mock_request
):
    """Test inactive user cannot authenticate."""
    inactive_user = User(email="inactive@example.com", is_active=False)
    mock_jwt_decode.return_value = {"sub": "inactive@example.com"}
    mock_db_exec.return_value.first.return_value = inactive_user

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(session=test_db, token="valid_token", request=mock_request)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "inactive_user"


# ---------- SUPERUSER ACCESS TESTS ----------


def test_get_current_active_superuser_success(mock_superuser, mock_request):
    """Test a superuser can access admin routes."""
    user = get_current_active_superuser(
        current_user=mock_superuser, request=mock_request
    )

    assert user.is_superuser is True


def test_get_current_active_superuser_failure(mock_user, mock_request):
    """Test non-superuser gets 403 Forbidden when trying to access admin routes."""
    with pytest.raises(HTTPException) as exc_info:
        get_current_active_superuser(current_user=mock_user, request=mock_request)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "insufficient_privileges"


# ---------- ROLE-BASED ACCESS TESTS ----------


def test_require_roles_success(mock_user, mock_request):
    """Test a user with the required role can access the route."""
    mock_user.admin = True  # Simulating a role

    role_checker = require_roles("admin")
    user = role_checker(current_user=mock_user, request=mock_request)

    assert user.admin is True


def test_require_roles_failure(mock_user, mock_request):
    """Test a user without the required role gets 403 Forbidden."""
    role_checker = require_roles("moderator")

    with pytest.raises(HTTPException) as exc_info:
        role_checker(current_user=mock_user, request=mock_request)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "user_lacks_required_privileges"
