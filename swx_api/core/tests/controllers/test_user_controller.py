import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, Request
from sqlmodel import SQLModel, Session, create_engine
from swx_api.core.models.user import UserUpdate, UserUpdatePassword
from swx_api.core.controllers.user_controller import (
    update_user_controller,
    get_current_user_controller,
    get_user_by_id_controller,
    update_password_controller,
    delete_user_controller,
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
    return MagicMock(id=1, email="test@example.com", full_name="Test User")


# ---------- GET CURRENT USER TEST ----------


def test_get_current_user_controller(mock_user):
    """Test retrieving the current authenticated user."""
    response = get_current_user_controller(mock_user)
    assert response == mock_user


# ---------- PROFILE UPDATE TESTS ----------


@patch("swx_api.core.services.user_service.update_user_profile_service")
def test_update_user_controller(
    mock_update_user_service, test_db, mock_user, mock_request
):
    """Test updating a user's profile."""
    update_data = UserUpdate(full_name="Updated User")
    mock_update_user_service.return_value = mock_user

    response = update_user_controller(
        session=test_db,
        user_in=update_data,
        current_user=mock_user,
        request=mock_request,
    )

    assert response == mock_user


# ---------- GET USER BY ID TESTS ----------


@patch("swx_api.core.services.user_service.get_user_by_id_service")
def test_get_user_by_id_controller(
    mock_get_user_by_id, test_db, mock_user, mock_request
):
    """Test retrieving a user by ID."""
    mock_get_user_by_id.return_value = mock_user

    response = get_user_by_id_controller(
        test_db, user_id=mock_user.id, current_user=mock_user, request=mock_request
    )

    assert response == mock_user


@patch("swx_api.core.services.user_service.get_user_by_id_service")
@patch("swx_api.core.utils.language_helper.translate", return_value="User not found")
def test_get_user_by_id_controller_not_found(
    mock_translate, mock_get_user_by_id, test_db, mock_request
):
    """Test getting a non-existent user raises 404."""
    mock_get_user_by_id.side_effect = HTTPException(
        status_code=404, detail="User not found"
    )

    with pytest.raises(HTTPException) as exc_info:
        get_user_by_id_controller(
            test_db, user_id=999, current_user=None, request=mock_request
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


# ---------- PASSWORD UPDATE TESTS ----------


@patch("swx_api.core.services.user_service.update_password_service")
def test_update_password_controller_success(
    mock_update_password_service, test_db, mock_user, mock_request
):
    """Test updating password successfully."""
    password_update = UserUpdatePassword(
        current_password="SecurePass123", new_password="newsecurepass"
    )
    mock_update_password_service.return_value = {
        "message": "Password updated successfully"
    }

    response = update_password_controller(
        test_db, mock_user, password_update, mock_request
    )

    assert response["message"] == "Password updated successfully"


@patch("swx_api.core.services.user_service.update_password_service")
@patch(
    "swx_api.core.utils.language_helper.translate",
    return_value="Password update failed",
)
def test_update_password_controller_failure(
    mock_translate, mock_update_password_service, test_db, mock_user, mock_request
):
    """Test updating password with incorrect current password fails."""
    password_update = UserUpdatePassword(
        current_password="wrongpass", new_password="newsecurepass"
    )
    mock_update_password_service.side_effect = HTTPException(
        status_code=400, detail="Password update failed"
    )

    with pytest.raises(HTTPException) as exc_info:
        update_password_controller(test_db, mock_user, password_update, mock_request)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Password update failed"


# ---------- DELETE USER TESTS ----------


@patch("swx_api.core.services.user_service.delete_user_service")
def test_delete_user_controller_success(
    mock_delete_user_service, test_db, mock_user, mock_request
):
    """Test deleting a user successfully."""
    mock_delete_user_service.return_value = {"message": "User deleted successfully"}

    response = delete_user_controller(test_db, mock_user, mock_request)

    assert response["message"] == "User deleted successfully"


@patch("swx_api.core.services.user_service.delete_user_service")
@patch(
    "swx_api.core.utils.language_helper.translate", return_value="User deletion failed"
)
def test_delete_user_controller_failure(
    mock_translate, mock_delete_user_service, test_db, mock_user, mock_request
):
    """Test deleting a user that does not exist."""
    mock_delete_user_service.side_effect = HTTPException(
        status_code=400, detail="User deletion failed"
    )

    with pytest.raises(HTTPException) as exc_info:
        delete_user_controller(test_db, mock_user, mock_request)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "User deletion failed"
