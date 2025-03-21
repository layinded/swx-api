import uuid
import pytest
from sqlmodel import SQLModel, Session, create_engine
from swx_api.core.models.language import LanguageCreate, LanguageUpdate
from swx_api.core.services.language_service import LanguageService


# Setup test database
@pytest.fixture(scope="function")
def test_db():
    """Fixture to create a fresh in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_create_language(test_db):
    """Test creating a new language resource via the service layer."""
    data = LanguageCreate(language_code="en", key="greeting", value="Hello")

    new_language = LanguageService.create_new_language(test_db, data)

    assert new_language.id is not None
    assert new_language.language_code == "en"
    assert new_language.key == "greeting"
    assert new_language.value == "Hello"


def test_retrieve_language_by_id(test_db):
    """Test retrieving a language resource by ID via the service layer."""
    data = LanguageCreate(language_code="cs", key="welcome_message", value="Vítejte")
    created_lang = LanguageService.create_new_language(test_db, data)

    retrieved_lang = LanguageService.retrieve_language_by_id(test_db, created_lang.id)

    assert retrieved_lang is not None
    assert retrieved_lang.id == created_lang.id
    assert retrieved_lang.language_code == "cs"
    assert retrieved_lang.key == "welcome_message"
    assert retrieved_lang.value == "Vítejte"


def test_retrieve_non_existent_language_by_id(test_db):
    """Test retrieving a non-existent language resource via the service layer."""
    random_id = uuid.uuid4()
    retrieved_lang = LanguageService.retrieve_language_by_id(test_db, random_id)

    assert retrieved_lang is None


def test_retrieve_language_by_code_and_key(test_db):
    """Test retrieving a language resource by language code and key via the service layer."""
    data = LanguageCreate(language_code="fr", key="farewell", value="Au revoir")
    created_lang = LanguageService.create_new_language(test_db, data)

    retrieved_lang = LanguageService.retrieve_language_by_code_and_key(
        test_db, "fr", "farewell"
    )

    assert retrieved_lang is not None
    assert retrieved_lang.language_code == "fr"
    assert retrieved_lang.key == "farewell"
    assert retrieved_lang.value == "Au revoir"


def test_retrieve_all_languages(test_db):
    """Test retrieving all language resources with pagination via the service layer."""
    data1 = LanguageCreate(language_code="en", key="hello", value="Hello")
    data2 = LanguageCreate(language_code="es", key="hello", value="Hola")
    LanguageService.create_new_language(test_db, data1)
    LanguageService.create_new_language(test_db, data2)

    all_languages = LanguageService.retrieve_all_language_resources(
        test_db, skip=0, limit=10
    )

    assert len(all_languages) == 2
    assert {lang.language_code for lang in all_languages} == {"en", "es"}


def test_retrieve_by_language_code(test_db):
    """Test retrieving all translations for a specific language via the service layer."""
    data1 = LanguageCreate(language_code="de", key="hello", value="Hallo")
    data2 = LanguageCreate(language_code="de", key="bye", value="Tschüss")
    LanguageService.create_new_language(test_db, data1)
    LanguageService.create_new_language(test_db, data2)

    german_translations = LanguageService.retrieve_by_language_code(test_db, "de")

    assert len(german_translations) == 2
    assert {t.key for t in german_translations} == {"hello", "bye"}


def test_retrieve_all_bulk_language_resources(test_db):
    """Test retrieving multiple translations in bulk via the service layer."""
    data1 = LanguageCreate(language_code="en", key="hello", value="Hello")
    data2 = LanguageCreate(language_code="fr", key="hello", value="Bonjour")
    data3 = LanguageCreate(language_code="fr", key="bye", value="Au revoir")
    LanguageService.create_new_language(test_db, data1)
    LanguageService.create_new_language(test_db, data2)
    LanguageService.create_new_language(test_db, data3)

    translations = LanguageService.retrieve_all_bulk_language_resources(
        test_db, ["en", "fr"]
    )

    assert len(translations) == 2  # Two languages
    assert translations["en"]["hello"] == "Hello"
    assert translations["fr"]["hello"] == "Bonjour"
    assert translations["fr"]["bye"] == "Au revoir"


def test_update_existing_language(test_db):
    """Test updating an existing language resource via the service layer."""
    data = LanguageCreate(language_code="es", key="thank_you", value="Gracias")
    created_lang = LanguageService.create_new_language(test_db, data)

    update_data = LanguageUpdate(value="Muchas gracias")
    updated_lang = LanguageService.update_existing_language(
        test_db, created_lang.id, update_data
    )

    assert updated_lang is not None
    assert updated_lang.value == "Muchas gracias"


def test_update_non_existent_language(test_db):
    """Test updating a non-existent language resource via the service layer."""
    random_id = uuid.uuid4()
    update_data = LanguageUpdate(value="Updated Value")

    updated_lang = LanguageService.update_existing_language(
        test_db, random_id, update_data
    )

    assert updated_lang is None


def test_delete_existing_language(test_db):
    """Test deleting an existing language resource via the service layer."""
    data = LanguageCreate(language_code="it", key="good_morning", value="Buongiorno")
    created_lang = LanguageService.create_new_language(test_db, data)

    delete_success = LanguageService.delete_existing_language(test_db, created_lang.id)

    assert delete_success is True

    # Verify it's deleted
    deleted_lang = LanguageService.retrieve_language_by_id(test_db, created_lang.id)
    assert deleted_lang is None


def test_delete_non_existent_language(test_db):
    """Test deleting a non-existent language resource via the service layer."""
    random_id = uuid.uuid4()
    delete_success = LanguageService.delete_existing_language(test_db, random_id)

    assert delete_success is False
