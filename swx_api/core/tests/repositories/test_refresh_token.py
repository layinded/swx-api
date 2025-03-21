import pytest
from sqlmodel import SQLModel, Session, create_engine
from swx_api.core.models.refresh_token import RefreshToken
from swx_api.core.auth.token_auth import revoke_refresh_token


# Setup test database
@pytest.fixture(scope="function")
def test_db():
    """Fixture to create a fresh in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def mock_refresh_token(test_db):
    """Create a mock refresh token for testing."""
    token = RefreshToken(token="test_refresh_token", user_email="user@example.com")
    test_db.add(token)
    test_db.commit()
    test_db.refresh(token)
    return token


# ---------- REVOKE REFRESH TOKEN TESTS ----------


def test_revoke_existing_refresh_token(test_db, mock_refresh_token):
    """Test revoking an existing refresh token."""
    revoked = revoke_refresh_token(test_db, "test_refresh_token")

    assert revoked is True

    # Ensure the token is deleted
    token = (
        test_db.query(RefreshToken)
        .filter(RefreshToken.token == "test_refresh_token")
        .first()
    )
    assert token is None


def test_revoke_non_existent_refresh_token(test_db):
    """Test revoking a non-existent refresh token returns False."""
    revoked = revoke_refresh_token(test_db, "non_existent_token")

    assert revoked is False
