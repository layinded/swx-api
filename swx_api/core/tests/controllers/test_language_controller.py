import uuid
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.exc import IntegrityError
from swx_api.core.models.language import (
    LanguageCreate,
    LanguageUpdate,
    LanguageCreateSchema,
)
from swx_api.core.controllers.language_controller import LanguageController


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


@patch(
    "swx_api.core.utils.language_helper.translate", return_value="Language not found"
)
def test_retrieve_non_existent_language_by_id(mock_translate, mock_request, test_db):
    """Test retrieving a non-existent language resource returns 404."""
    random_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc_info:
        LanguageController.retrieve_language_by_id(mock_request, random_id, test_db)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Language not found"


def test_create_new_language(mock_request, test_db):
    """Test creating a new language resource via the controller."""
    data = LanguageCreate(language_code="en", key="greeting", value="Hello")

    new_language = LanguageController.create_new_language(mock_request, data, test_db)

    assert new_language.id is not None
    assert new_language.language_code == "en"
    assert new_language.key == "greeting"
    assert new_language.value == "Hello"


@patch(
    "swx_api.core.utils.language_helper.translate", return_value="Language not found"
)
def test_update_non_existent_language(mock_translate, mock_request, test_db):
    """Test updating a non-existent language resource returns 404."""
    random_id = uuid.uuid4()
    update_data = LanguageUpdate(value="Updated Value")

    with pytest.raises(HTTPException) as exc_info:
        LanguageController.update_existing_language(
            mock_request, random_id, update_data, test_db
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Language not found"


@patch(
    "swx_api.core.utils.language_helper.translate", return_value="Language not found"
)
def test_delete_non_existent_language(mock_translate, mock_request, test_db):
    """Test deleting a non-existent language resource returns 404."""
    random_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc_info:
        LanguageController.delete_existing_language(mock_request, random_id, test_db)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Language not found"


def test_retrieve_all_languages(mock_request, test_db):
    """Test retrieving all language resources via the controller."""
    data1 = LanguageCreate(language_code="en", key="hello", value="Hello")
    data2 = LanguageCreate(language_code="es", key="hello", value="Hola")
    LanguageController.create_new_language(mock_request, data1, test_db)
    LanguageController.create_new_language(mock_request, data2, test_db)

    all_languages = LanguageController.retrieve_all_language_resources(
        mock_request, test_db, skip=0, limit=10
    )

    assert len(all_languages) == 2
    assert {lang.language_code for lang in all_languages} == {"en", "es"}


def test_bulk_language_creation(mock_request, test_db):
    """Test creating multiple language resources in bulk via the controller."""
    bulk_data = [
        LanguageCreateSchema(language_code="fr", key="hello", value="Bonjour"),
        LanguageCreateSchema(language_code="fr", key="bye", value="Au revoir"),
    ]

    response = LanguageController.create_new_bulk_language(
        mock_request, bulk_data, test_db
    )

    assert response["message"] == "new_translation_created"


@patch(
    "swx_api.core.utils.language_helper.translate",
    return_value="new_translation_created",
)
def test_bulk_language_creation_with_duplicates(mock_translate, mock_request, test_db):
    """Test handling duplicate key errors in bulk language creation."""
    bulk_data = [
        LanguageCreateSchema(language_code="fr", key="hello", value="Bonjour"),
        LanguageCreateSchema(
            language_code="fr", key="hello", value="Bonjour"
        ),  # Duplicate
    ]

    # Mock database session to raise IntegrityError for duplicate key
    test_db.add = MagicMock(side_effect=IntegrityError("Duplicate key", {}, None))

    response = LanguageController.create_new_bulk_language(
        mock_request, bulk_data, test_db
    )

    assert "new_translation_created" in response["message"]


@patch(
    "swx_api.core.utils.language_helper.translate", return_value="Language not found"
)
def test_retrieve_non_existent_language_by_code_and_key(
    mock_translate, mock_request, test_db
):
    """Test retrieving a non-existent language by code and key returns 404."""
    with pytest.raises(HTTPException) as exc_info:
        LanguageController.retrieve_language_by_code_and_key(
            mock_request, test_db, "fr", "unknown_key"
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Language not found"


def test_update_existing_language(mock_request, test_db):
    """Test updating an existing language resource via the controller."""
    data = LanguageCreate(language_code="de", key="thank_you", value="Danke")
    created_lang = LanguageController.create_new_language(mock_request, data, test_db)

    update_data = LanguageUpdate(value="Vielen Dank")
    updated_lang = LanguageController.update_existing_language(
        mock_request, created_lang.id, update_data, test_db
    )

    assert updated_lang is not None
    assert updated_lang.value == "Vielen Dank"


def test_delete_existing_language(mock_request, test_db):
    """Test deleting an existing language resource via the controller."""
    data = LanguageCreate(language_code="it", key="good_morning", value="Buongiorno")
    created_lang = LanguageController.create_new_language(mock_request, data, test_db)

    delete_success = LanguageController.delete_existing_language(
        mock_request, created_lang.id, test_db
    )

    assert delete_success is None  # Deletion returns None as per controller definition
