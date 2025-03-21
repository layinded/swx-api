import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from swx_api.core.models.user import User
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


# ---------- GET OAUTH URLS TEST ----------


def test_get_oauth_urls():
    """Test retrieving OAuth URLs."""
    response = client.get("/oauth/urls")

    assert response.status_code == 200
    assert "google" in response.json()
    assert "facebook" in response.json()


# ---------- GOOGLE LOGIN TESTS ----------


@patch("swx_api.core.config.social_settings.ENABLE_GOOGLE_LOGIN", True)
@patch(
    "swx_api.core.config.social_settings.GOOGLE_REDIRECT_URI",
    "https://example.com/callback",
)
@patch("swx_api.core.config.social_settings.GOOGLE_CLIENT_ID", "mock_client_id")
@patch("swx_api.core.config.social_settings.GOOGLE_CLIENT_SECRET", "mock_client_secret")
@patch(
    "swx_api.core.routers.oauth.oauth.google.authorize_redirect", new_callable=AsyncMock
)
async def test_google_login(mock_google_redirect):
    """Test redirecting to Google OAuth."""
    response = client.get("/oauth/google")

    assert response.status_code == 200 or response.status_code == 307  # Redirect status


@patch(
    "swx_api.core.routers.oauth.oauth.google.authorize_access_token",
    new_callable=AsyncMock,
)
@patch("swx_api.core.repositories.user_repository.get_user_by_email", return_value=None)
@patch(
    "swx_api.core.repositories.user_repository.create_social_user",
    return_value=User(email="test@example.com"),
)
@patch("swx_api.core.controllers.auth_controller.login_social_user_controller")
async def test_google_auth_callback_success(
    mock_login_social, mock_create_user, mock_get_user, mock_auth_token
):
    """Test Google OAuth callback successfully creates/logs in a user."""
    mock_auth_token.return_value = {"userinfo": {"email": "test@example.com"}}
    mock_login_social.return_value = {"access_token": "mock_access_token"}

    response = client.get("/oauth/google/callback?state=mock_state")

    assert response.status_code == 200
    assert response.json()["access_token"] == "mock_access_token"


@patch(
    "swx_api.core.routers.oauth.oauth.google.authorize_access_token",
    new_callable=AsyncMock,
)
async def test_google_auth_callback_failure(mock_auth_token):
    """Test Google OAuth callback failure due to missing email."""
    mock_auth_token.return_value = {"userinfo": {}}

    response = client.get("/oauth/google/callback?state=mock_state")

    assert response.status_code == 400
    assert "google_account_missing_email" in response.json()["error"]


# ---------- FACEBOOK LOGIN TESTS ----------


@patch("swx_api.core.config.social_settings.ENABLE_FACEBOOK_LOGIN", True)
@patch(
    "swx_api.core.config.social_settings.FACEBOOK_REDIRECT_URI",
    "https://example.com/callback",
)
@patch(
    "swx_api.core.routers.oauth.oauth.facebook.authorize_redirect",
    new_callable=AsyncMock,
)
async def test_facebook_login(mock_facebook_redirect):
    """Test redirecting to Facebook OAuth."""
    response = client.get("/oauth/facebook")

    assert response.status_code == 200 or response.status_code == 307  # Redirect status


@patch(
    "swx_api.core.routers.oauth.oauth.facebook.authorize_access_token",
    new_callable=AsyncMock,
)
@patch("swx_api.core.routers.oauth.fetch_facebook_user_info", new_callable=AsyncMock)
@patch("swx_api.core.repositories.user_repository.get_user_by_email", return_value=None)
@patch(
    "swx_api.core.repositories.user_repository.create_social_user",
    return_value=User(email="test@example.com"),
)
@patch("swx_api.core.controllers.auth_controller.login_social_user_controller")
async def test_facebook_auth_callback_success(
    mock_login_social, mock_create_user, mock_get_user, mock_fetch_user, mock_auth_token
):
    """Test Facebook OAuth callback successfully creates/logs in a user."""
    mock_auth_token.return_value = {"access_token": "mock_access_token"}
    mock_fetch_user.return_value = {"email": "test@example.com"}
    mock_login_social.return_value = {"access_token": "mock_access_token"}

    response = client.get("/oauth/facebook/callback?state=mock_state&code=mock_code")

    assert response.status_code == 200
    assert response.json()["access_token"] == "mock_access_token"


@patch(
    "swx_api.core.routers.oauth.oauth.facebook.authorize_access_token",
    new_callable=AsyncMock,
)
@patch("swx_api.core.routers.oauth.fetch_facebook_user_info", new_callable=AsyncMock)
async def test_facebook_auth_callback_failure(mock_fetch_user, mock_auth_token):
    """Test Facebook OAuth callback failure due to missing email."""
    mock_auth_token.return_value = {"access_token": "mock_access_token"}
    mock_fetch_user.return_value = {}

    response = client.get("/oauth/facebook/callback?state=mock_state&code=mock_code")

    assert response.status_code == 400
    assert "facebook_account_missing_email" in response.json()["error"]
