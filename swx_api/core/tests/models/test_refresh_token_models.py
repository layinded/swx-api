import uuid
import pytest
from datetime import datetime, timedelta, timezone
from sqlmodel import SQLModel, Session, create_engine
from swx_api.core.models.refresh_token import (
    RefreshToken,
    RefreshTokenCreate,
    RefreshTokenUpdate,
    RefreshTokenPublic,
)


# Setup test database
@pytest.fixture(scope="function")
def test_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_refresh_token_creation(test_db):
    """Test that a RefreshToken instance can be created and persisted."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)  # Expires in 7 days
    refresh_token = RefreshToken(
        token="test_token",
        expires_at=expires_at,
        user_email="user@example.com",
    )
    test_db.add(refresh_token)
    test_db.commit()
    test_db.refresh(refresh_token)

    assert refresh_token.id is not None
    assert refresh_token.token == "test_token"
    assert refresh_token.expires_at == expires_at
    assert refresh_token.user_email == "user@example.com"
    assert isinstance(refresh_token.created_at, datetime)


def test_refresh_token_create_schema():
    """Test that RefreshTokenCreate enforces constraints correctly."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=3)

    schema = RefreshTokenCreate(
        token="new_token",
        expires_at=expires_at,
    )

    assert schema.token == "new_token"
    assert schema.expires_at == expires_at
    assert isinstance(schema.created_at, datetime)


def test_refresh_token_update():
    """Test that RefreshTokenUpdate allows updates while preserving fields."""
    new_expiry = datetime.now(timezone.utc) + timedelta(days=5)

    update_data = RefreshTokenUpdate(expires_at=new_expiry)

    assert update_data.token is None  # Fields can be omitted
    assert update_data.expires_at == new_expiry
    assert isinstance(update_data.created_at, datetime)


def test_refresh_token_public_schema():
    """Test that RefreshTokenPublic correctly exposes fields."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=2)

    public_token = RefreshTokenPublic(
        id=uuid.uuid4(),
        token="public_token",
        expires_at=expires_at,
        created_at=datetime.now(timezone.utc),
        user_email="public@example.com",
    )

    assert isinstance(public_token.id, uuid.UUID)
    assert public_token.token == "public_token"
    assert public_token.expires_at == expires_at
    assert public_token.user_email == "public@example.com"
    assert isinstance(public_token.created_at, datetime)


# Edge Case: Expired Token
def test_expired_refresh_token(test_db):
    """Test that expired tokens are handled correctly."""
    expired_at = datetime.now(timezone.utc) - timedelta(days=1)  # Expired 1 day ago

    expired_token = RefreshToken(
        token="expired_token",
        expires_at=expired_at,
        user_email="expired@example.com",
    )

    test_db.add(expired_token)
    test_db.commit()
    test_db.refresh(expired_token)

    assert expired_token.id is not None
    assert expired_token.token == "expired_token"
    assert expired_token.expires_at < datetime.now(timezone.utc)  # Expired


def test_future_expiration_refresh_token(test_db):
    """Test that a token with a future expiration date is valid."""
    future_at = datetime.now(timezone.utc) + timedelta(days=10)  # Valid for 10 days

    valid_token = RefreshToken(
        token="valid_future_token",
        expires_at=future_at,
        user_email="future@example.com",
    )

    test_db.add(valid_token)
    test_db.commit()
    test_db.refresh(valid_token)

    assert valid_token.id is not None
    assert valid_token.token == "valid_future_token"
    assert valid_token.expires_at > datetime.now(timezone.utc)  # Still valid


def test_invalid_expiration_date():
    """Test that an invalid expiration date raises an error."""
    with pytest.raises(ValueError):
        RefreshTokenCreate(
            token="invalid_token",
            expires_at="invalid_date_string",  # This should cause an error
        )


def test_null_token_field():
    """Test that a null token field raises an error."""
    with pytest.raises(TypeError):
        RefreshTokenCreate(token=None, expires_at=datetime.now(timezone.utc))


def test_invalid_email_field(test_db):
    """Test that an invalid email format does not break the model but follows expected behavior."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    invalid_email_token = RefreshToken(
        token="invalid_email_token",
        expires_at=expires_at,
        user_email="invalid_email_format",  # Not enforcing email validation yet
    )

    test_db.add(invalid_email_token)
    test_db.commit()
    test_db.refresh(invalid_email_token)

    assert (
        invalid_email_token.user_email == "invalid_email_format"
    )  # Allowed unless explicit validation
