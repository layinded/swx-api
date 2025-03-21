import uuid
import pytest
from sqlmodel import SQLModel, Session, create_engine
from passlib.context import CryptContext
from swx_api.core.models.user import User, UserCreate, UserUpdate
from swx_api.core.security.password_security import verify_password
from swx_api.core.auth.user_auth import (
    authenticate_user,
    get_user_by_email,
    create_user,
    get_user_by_id,
    update_user,
    update_user_password,
    delete_user,
    create_social_user,
)

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Setup test database
@pytest.fixture(scope="function")
def test_db():
    """Fixture to create a fresh in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def mock_user():
    """Returns a mock user creation payload."""
    return UserCreate(
        email="test@example.com", password="SecurePass123", full_name="Test User"
    )


# ---------- USER CREATION & AUTHENTICATION TESTS ----------


def test_create_user(test_db, mock_user):
    """Test creating a new user."""
    new_user = create_user(session=test_db, user_create=mock_user)

    assert new_user.id is not None
    assert new_user.email == "test@example.com"
    assert new_user.auth_provider == "local"
    assert verify_password("SecurePass123", new_user.hashed_password) is True


def test_authenticate_user_success(test_db, mock_user):
    """Test user authentication with correct credentials."""
    create_user(session=test_db, user_create=mock_user)

    authenticated_user = authenticate_user(
        session=test_db, email="test@example.com", password="SecurePass123"
    )

    assert authenticated_user is not None
    assert authenticated_user.email == "test@example.com"


def test_authenticate_user_invalid_password(test_db, mock_user):
    """Test user authentication failure due to incorrect password."""
    create_user(session=test_db, user_create=mock_user)

    authenticated_user = authenticate_user(
        session=test_db, email="test@example.com", password="WrongPassword"
    )

    assert authenticated_user is None


def test_authenticate_non_existent_user(test_db):
    """Test authentication failure when user does not exist."""
    authenticated_user = authenticate_user(
        session=test_db, email="doesnotexist@example.com", password="Password123"
    )

    assert authenticated_user is None


# ---------- USER FETCHING TESTS ----------


def test_get_user_by_email(test_db, mock_user):
    """Test retrieving a user by email."""
    create_user(session=test_db, user_create=mock_user)

    retrieved_user = get_user_by_email(session=test_db, email="test@example.com")

    assert retrieved_user is not None
    assert retrieved_user.email == "test@example.com"


def test_get_user_by_email_not_found(test_db):
    """Test retrieving a user that does not exist."""
    retrieved_user = get_user_by_email(session=test_db, email="missing@example.com")

    assert retrieved_user is None


def test_get_user_by_id(test_db, mock_user):
    """Test retrieving a user by ID."""
    new_user = create_user(session=test_db, user_create=mock_user)

    retrieved_user = get_user_by_id(session=test_db, user_id=new_user.id)

    assert retrieved_user is not None
    assert retrieved_user.email == "test@example.com"


# ---------- USER UPDATING TESTS ----------


def test_update_user_full_name(test_db, mock_user):
    """Test updating user details, including full name."""
    new_user = create_user(session=test_db, user_create=mock_user)

    update_data = UserUpdate(full_name="Updated User")
    updated_user = update_user(session=test_db, db_user=new_user, user_in=update_data)

    assert updated_user.full_name == "Updated User"


def test_update_user_password(test_db, mock_user):
    """Test updating a user's password and ensuring it's hashed."""
    new_user = create_user(session=test_db, user_create=mock_user)

    password_updated = update_user_password(
        session=test_db,
        current_user=new_user.id,
        current_password="SecurePass123",
        new_password="NewSecurePass",
    )

    assert password_updated is True

    updated_user = get_user_by_id(session=test_db, user_id=new_user.id)
    assert verify_password("NewSecurePass", updated_user.hashed_password) is True


def test_update_user_password_invalid_current_password(test_db, mock_user):
    """Test updating password fails when providing an incorrect current password."""
    new_user = create_user(session=test_db, user_create=mock_user)

    password_updated = update_user_password(
        session=test_db,
        current_user=new_user.id,
        current_password="WrongPass",
        new_password="NewSecurePass",
    )

    assert password_updated is False


# ---------- USER DELETION TESTS ----------


def test_delete_user(test_db, mock_user):
    """Test deleting a user."""
    new_user = create_user(session=test_db, user_create=mock_user)

    delete_success = delete_user(session=test_db, current_user=new_user)

    assert delete_success is True

    # Ensure the user no longer exists
    deleted_user = get_user_by_email(session=test_db, email="test@example.com")
    assert deleted_user is None


# ---------- SOCIAL LOGIN USER CREATION ----------


def test_create_social_user_google(test_db):
    """Test creating a user via Google login."""
    user_info = {"sub": "google123", "name": "Google User"}
    new_user = create_social_user(
        session=test_db,
        email="google@example.com",
        user_info=user_info,
        provider="google",
    )

    assert new_user.id is not None
    assert new_user.email == "google@example.com"
    assert new_user.auth_provider == "google"
    assert new_user.provider_id == "google123"


def test_create_social_user_facebook(test_db):
    """Test creating a user via Facebook login."""
    user_info = {"id": "facebook456", "name": "Facebook User"}
    new_user = create_social_user(
        session=test_db,
        email="fb@example.com",
        user_info=user_info,
        provider="facebook",
    )

    assert new_user.id is not None
    assert new_user.email == "fb@example.com"
    assert new_user.auth_provider == "facebook"
    assert new_user.provider_id == "facebook456"


def test_create_social_user_missing_provider_id(test_db):
    """Test that a social user creation fails when provider ID is missing."""
    user_info = {"name": "No ID User"}

    with pytest.raises(ValueError):
        create_social_user(
            session=test_db,
            email="noid@example.com",
            user_info=user_info,
            provider="google",
        )
