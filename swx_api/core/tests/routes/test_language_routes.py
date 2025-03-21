import uuid
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from swx_api.core.models.language import (
    LanguageCreate,
    LanguageCreateSchema,
    LanguageUpdate,
)
from swx_api.core.main import app  # Import the FastAPI app instance

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


# Helper function to authenticate as superuser
def get_superuser_token_headers():
    """Mock authentication headers for an active superuser."""
    return {"Authorization": "Bearer mock_superuser_token"}


# ---------- GET ENDPOINT TESTS ----------


def test_get_all_languages(test_db):
    """Test retrieving all language resources via the API."""
    response = client.get("/language/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_language_by_id_not_found():
    """Test retrieving a non-existent language resource returns 404."""
    random_id = uuid.uuid4()
    response = client.get(f"/language/{random_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Language not found"


def test_get_language_by_code_not_found():
    """Test retrieving a non-existent language code returns 404."""
    response = client.get("/language/code/xx")

    assert response.status_code == 404
    assert response.json()["detail"] == "Language not found"


def test_get_language_by_code_and_key_not_found():
    """Test retrieving a non-existent key within a language returns 404."""
    response = client.get("/language/en/missing_key")

    assert response.status_code == 404
    assert response.json()["detail"] == "Language not found"


def test_get_bulk_languages(test_db):
    """Test retrieving multiple languages in bulk via the API."""
    response = client.get("/language/bulk", params={"languages": ["en", "fr"]})

    assert response.status_code == 200
    assert isinstance(response.json(), dict)


# ---------- POST ENDPOINT TESTS (Requires Authentication) ----------


def test_create_language():
    """Test creating a new language resource."""
    headers = get_superuser_token_headers()
    data = {"language_code": "en", "key": "greeting", "value": "Hello"}

    response = client.post("/language/", json=data, headers=headers)

    assert response.status_code == 201
    assert response.json()["language_code"] == "en"
    assert response.json()["key"] == "greeting"
    assert response.json()["value"] == "Hello"


def test_create_bulk_languages():
    """Test creating multiple language resources in bulk."""
    headers = get_superuser_token_headers()
    bulk_data = [
        {"language_code": "fr", "key": "hello", "value": "Bonjour"},
        {"language_code": "fr", "key": "bye", "value": "Au revoir"},
    ]

    response = client.post("/language/bulk", json=bulk_data, headers=headers)

    assert response.status_code == 201
    assert "message" in response.json()


def test_create_duplicate_language():
    """Test handling duplicate language keys on creation."""
    headers = get_superuser_token_headers()
    data = {"language_code": "en", "key": "greeting", "value": "Hello"}

    client.post("/language/", json=data, headers=headers)  # First time (Success)
    response = client.post("/language/", json=data, headers=headers)  # Duplicate

    assert response.status_code == 500  # IntegrityError should be caught


def test_create_language_unauthorized():
    """Test that unauthorized users cannot create languages."""
    data = {"language_code": "es", "key": "hello", "value": "Hola"}

    response = client.post("/language/", json=data)

    assert response.status_code == 403  # Requires authentication


# ---------- PUT (UPDATE) ENDPOINT TESTS ----------


def test_update_existing_language():
    """Test updating an existing language resource."""
    headers = get_superuser_token_headers()
    create_response = client.post(
        "/language/",
        json={"language_code": "de", "key": "thank_you", "value": "Danke"},
        headers=headers,
    )
    lang_id = create_response.json()["id"]

    update_data = {"value": "Vielen Dank"}
    response = client.put(f"/language/{lang_id}", json=update_data, headers=headers)

    assert response.status_code == 200
    assert response.json()["value"] == "Vielen Dank"


def test_update_non_existent_language():
    """Test updating a non-existent language returns 404."""
    headers = get_superuser_token_headers()
    random_id = uuid.uuid4()
    update_data = {"value": "Updated Value"}

    response = client.put(f"/language/{random_id}", json=update_data, headers=headers)

    assert response.status_code == 404


def test_update_language_unauthorized():
    """Test that unauthorized users cannot update languages."""
    random_id = uuid.uuid4()
    update_data = {"value": "Updated Value"}

    response = client.put(f"/language/{random_id}", json=update_data)

    assert response.status_code == 403  # Requires authentication


# ---------- DELETE ENDPOINT TESTS ----------


def test_delete_existing_language():
    """Test deleting an existing language resource."""
    headers = get_superuser_token_headers()
    create_response = client.post(
        "/language/",
        json={"language_code": "it", "key": "good_morning", "value": "Buongiorno"},
        headers=headers,
    )
    lang_id = create_response.json()["id"]

    delete_response = client.delete(f"/language/{lang_id}", headers=headers)

    assert delete_response.status_code == 204  # No content


def test_delete_non_existent_language():
    """Test deleting a non-existent language returns 404."""
    headers = get_superuser_token_headers()
    random_id = uuid.uuid4()

    response = client.delete(f"/language/{random_id}", headers=headers)

    assert response.status_code == 404


def test_delete_language_unauthorized():
    """Test that unauthorized users cannot delete languages."""
    random_id = uuid.uuid4()

    response = client.delete(f"/language/{random_id}")

    assert response.status_code == 403  # Requires authentication
