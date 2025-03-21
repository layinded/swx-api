import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, Request
from sqlmodel import SQLModel, Session, create_engine
from swx_api.core.models.user import User, UserUpdate, UserUpdatePassword
from swx_api.core.services.user_service import (
    update_user_profile_service,
    get_user_by_id_service,
    update_password_service,
    delete_user_service,
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
    return User(
        id=1,
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashedpass",
    )


# ---------- PROFILE UPDATE TESTS ----------


def test_update_user_profile_service(test_db, mock_user, mock_request):
    """Test updating a user's profile."""
    update_data = UserUpdate(full_name="Updated User")

    with patch(
        "swx_api.core.repositories.user_repository.update_user", return_value=mock_user
    ):
        updated_user = update_user_profile_service(
            session=test_db,
            user_in=update_data,
            current_user=mock_user,
            request=mock_request,
        )

    assert updated_user.full_name == "Updated User"


# ---------- GET USER TESTS ----------


@patch("swx_api.core.utils.language_helper.translate", return_value="User not found")
def test_get_user_by_id_service_not_found(mock_translate, mock_request, test_db):
    """Test getting a non-existent user raises 404."""
    with patch(
        "swx_api.core.repositories.user_repository.get_user_by_id", return_value=None
    ):
        with pytest.raises(HTTPException) as exc_info:
            get_user_by_id_service(
                test_db, user_id=999, current_user=None, request=mock_request
            )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


@patch("swx_api.core.repositories.user_repository.get_user_by_id")
def test_get_user_by_id_service(mock_get_user, test_db, mock_user, mock_request):
    """Test getting a user by ID successfully."""
    mock_get_user.return_value = mock_user

    retrieved_user = get_user_by_id_service(
        test_db, user_id=mock_user.id, current_user=None, request=mock_request
    )

    assert retrieved_user.email == "test@example.com"


# ---------- PASSWORD UPDATE TESTS ----------


@patch(
    "swx_api.core.utils.language_helper.translate",
    return_value="Password update failed",
)
def test_update_password_service_failure(
    mock_translate, test_db, mock_user, mock_request
):
    """Test updating password with incorrect current password fails."""
    password_update = UserUpdatePassword(
        current_password="wrongpass", new_password="newsecurepass"
    )

    with patch(
        "swx_api.core.repositories.user_repository.update_user_password",
        return_value=False,
    ):
        with pytest.raises(HTTPException) as exc_info:
            update_password_service(test_db, mock_user, password_update, mock_request)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Password update failed"


@patch(
    "swx_api.core.utils.language_helper.translate",
    return_value="Password updated successfully",
)
def test_update_password_service_success(
    mock_translate, test_db, mock_user, mock_request
):
    """Test updating password successfully."""
    password_update = UserUpdatePassword(
        current_password="SecurePass123", new_password="newsecurepass"
    )

    with patch(
        "swx_api.core.repositories.user_repository.update_user_password",
        return_value=True,
    ):
        response = update_password_service(
            test_db, mock_user, password_update, mock_request
        )

    assert response["message"] == "Password updated successfully"


# ---------- DELETE USER TESTS ----------


@patch(
    "swx_api.core.utils.language_helper.translate", return_value="User deletion failed"
)
def test_delete_user_service_failure(mock_translate, test_db, mock_user, mock_request):
    """Test deleting a user that does not exist."""
    with patch(
        "swx_api.core.repositories.user_repository.delete_user", return_value=False
    ):
        with pytest.raises(HTTPException) as exc_info:
            delete_user_service(test_db, mock_user, mock_request)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "User deletion failed"


@patch(
    "swx_api.core.utils.language_helper.translate",
    return_value="User deleted successfully",
)
def test_delete_user_service_success(mock_translate, test_db, mock_user, mock_request):
    """Test deleting a user successfully."""
    with patch(
        "swx_api.core.repositories.user_repository.delete_user", return_value=True
    ):
        response = delete_user_service(test_db, mock_user, mock_request)

    assert response["message"] == "User deleted successfully"
