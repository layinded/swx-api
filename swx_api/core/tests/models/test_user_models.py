import uuid
import pytest
from sqlmodel import SQLModel, Session, create_engine, select
from pydantic import ValidationError
from passlib.context import CryptContext
from swx_api.core.models.user import (
    User,
    UserCreate,
    UserUpdate,
    UserPublic,
    UsersPublic,
    UserUpdatePassword,
    UserNewPassword,
)

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Setup test database
@pytest.fixture(scope="function")
def test_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def hashed_password():
    """Fixture to return a hashed password for test cases."""
    return pwd_context.hash("securepassword123")


def test_password_hashing_and_verification(hashed_password):
    """Test password hashing and verification process."""
    # Ensure the password is hashed
    assert hashed_password != "securepassword123"

    # Verify the hashed password
    assert pwd_context.verify("securepassword123", hashed_password) is True
    assert pwd_context.verify("wrongpassword", hashed_password) is False


def test_user_creation_with_hashed_password(test_db, hashed_password):
    """Test that a User instance stores a hashed password correctly."""
    user = User(
        email="test@example.com",
        hashed_password=hashed_password,
        full_name="Test User",
        preferred_language="en",
        auth_provider="local",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.hashed_password != "securepassword123"  # Should be hashed
    assert pwd_context.verify("securepassword123", user.hashed_password) is True


def test_invalid_login_attempt(test_db, hashed_password):
    """Test that an incorrect password does not authenticate a user."""
    user = User(
        email="user@example.com",
        hashed_password=hashed_password,  # Correct hashed password
        full_name="User One",
        preferred_language="en",
        auth_provider="local",
    )
    test_db.add(user)
    test_db.commit()

    # Simulate incorrect password input
    assert pwd_context.verify("wrongpassword", user.hashed_password) is False


def test_successful_authentication(test_db, hashed_password):
    """Test a successful email and password authentication."""
    user = User(
        email="authuser@example.com",
        hashed_password=hashed_password,
        full_name="Authenticated User",
        preferred_language="cs",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    # Simulate correct password input
    assert pwd_context.verify("securepassword123", user.hashed_password) is True


def test_user_update_password_with_hashing(test_db, hashed_password):
    """Test updating a user password and ensuring it is hashed."""
    user = User(
        email="update@example.com",
        hashed_password=hashed_password,
        full_name="Update Test User",
        preferred_language="fr",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    # Simulate password update
    new_password = pwd_context.hash("newsecurepassword456")
    user.hashed_password = new_password
    test_db.commit()
    test_db.refresh(user)

    assert pwd_context.verify("newsecurepassword456", user.hashed_password) is True
    assert pwd_context.verify("securepassword123", user.hashed_password) is False


def test_user_new_password_schema():
    """Test UserNewPassword schema with token-based reset."""
    new_password_request = UserNewPassword(
        token="reset_token_123", new_password="newpass456"
    )

    assert new_password_request.token == "reset_token_123"
    assert new_password_request.new_password == "newpass456"


def test_user_update_password_schema():
    """Test updating password through schema validation."""
    password_update = UserUpdatePassword(
        current_password="oldpassword123", new_password="newsecurepass456"
    )

    assert password_update.current_password == "oldpassword123"
    assert password_update.new_password == "newsecurepass456"


def test_invalid_new_password():
    """Test that setting a too-short new password raises a validation error."""
    with pytest.raises(ValidationError):
        UserNewPassword(token="reset_token_123", new_password="short")
