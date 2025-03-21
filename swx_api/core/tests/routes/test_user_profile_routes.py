import uuid
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from swx_api.core.models.user import User, UserUpdate, UserUpdatePassword
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


# Helper function to authenticate as a test user
def get_auth_headers(user_id=None):
    """Mock authentication headers for an active user."""
    return {"Authorization": f"Bearer mock_token_{user_id or 'default'}"}


# ---------- GET CURRENT USER TEST ----------


def test_get_current_user():
    """Test retrieving the current authenticated user."""
    headers = get_auth_headers(user_id=uuid.uuid4())

    response = client.get("/profile/", headers=headers)

    assert response.status_code == 200
    assert "email" in response.json()


# ---------- UPDATE USER PROFILE TEST ----------


@patch("swx_api.core.services.user_service.update_user_profile_service")
def test_update_user_profile(mock_update_service):
    """Test updating a user's profile."""
    headers = get_auth_headers(user_id=uuid.uuid4())
    mock_update_service.return_value = {"full_name": "Updated User"}

    data = {"full_name": "Updated User"}
    response = client.patch("/profile/", json=data, headers=headers)

    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated User"


# ---------- GET USER BY ID TEST ----------


@patch("swx_api.core.utils.language_helper.translate", return_value="Access denied")
def test_read_user_by_id_unauthorized(mock_translate):
    """Test retrieving another user's profile returns 403."""
    headers = get_auth_headers(user_id=uuid.uuid4())

    response = client.get(f"/profile/{uuid.uuid4()}", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Access denied"


@patch("swx_api.core.services.user_service.get_user_by_id_service")
def test_read_user_by_id(mock_get_user):
    """Test retrieving a user by ID."""
    user_id = uuid.uuid4()
    headers = get_auth_headers(user_id=user_id)
    mock_get_user.return_value = {"id": str(user_id), "email": "test@example.com"}

    response = client.get(f"/profile/{user_id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


# ---------- UPDATE PASSWORD TEST ----------


@patch("swx_api.core.services.user_service.update_password_service")
def test_update_password(mock_update_password_service):
    """Test updating a user's password."""
    headers = get_auth_headers(user_id=uuid.uuid4())
    mock_update_password_service.return_value = {
        "message": "Password updated successfully"
    }

    data = {"current_password": "oldpass", "new_password": "newsecurepass"}
    response = client.patch("/profile/password/update", json=data, headers=headers)

    assert response.status_code == 200
    assert response.json()["message"] == "Password updated successfully"


@patch(
    "swx_api.core.utils.language_helper.translate",
    return_value="Password update failed",
)
def test_update_password_failure(mock_translate):
    """Test updating password with incorrect current password fails."""
    headers = get_auth_headers(user_id=uuid.uuid4())

    data = {"current_password": "wrongpass", "new_password": "newsecurepass"}
    response = client.patch("/profile/password/update", json=data, headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Password update failed"


# ---------- DELETE USER TEST ----------


@patch("swx_api.core.services.user_service.delete_user_service")
def test_delete_user(mock_delete_user_service):
    """Test deleting a user successfully."""
    headers = get_auth_headers(user_id=uuid.uuid4())
    mock_delete_user_service.return_value = {"message": "User deleted successfully"}

    response = client.delete("/profile/delete", headers=headers)

    assert response.status_code == 200
    assert response.json()["message"] == "User deleted successfully"
