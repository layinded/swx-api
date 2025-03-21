import uuid
import pytest
from sqlmodel import SQLModel, Session, create_engine
from swx_api.core.models.language import (
    Language,
    LanguageCreate,
    LanguageUpdate,
    LanguagePublic,
    LanguageCreateSchema,
    BulkLanguageResponse,
)


# Setup test database
@pytest.fixture(scope="function")
def test_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_language_creation(test_db):
    """Test that a Language instance can be created and persisted."""
    language = Language(language_code="en", key="welcome_message", value="Welcome")
    test_db.add(language)
    test_db.commit()
    test_db.refresh(language)

    assert language.id is not None
    assert language.language_code == "en"
    assert language.key == "welcome_message"
    assert language.value == "Welcome"


def test_language_create_schema():
    """Test that the LanguageCreateSchema enforces constraints correctly."""
    with pytest.raises(ValueError):
        LanguageCreateSchema(language_code="e", key="", value="Hello")  # Invalid input

    schema = LanguageCreateSchema(language_code="en", key="greeting", value="Hello")
    assert schema.language_code == "en"
    assert schema.key == "greeting"
    assert schema.value == "Hello"


def test_language_update():
    """Test that LanguageUpdate allows partial updates."""
    update_data = LanguageUpdate(value="New Welcome Message")

    assert update_data.language_code is None
    assert update_data.key is None
    assert update_data.value == "New Welcome Message"


def test_language_public():
    """Test the LanguagePublic schema"""
    public_language = LanguagePublic(
        id=uuid.uuid4(), language_code="cs", key="welcome_message", value="Vítejte"
    )

    assert isinstance(public_language.id, uuid.UUID)
    assert public_language.language_code == "cs"
    assert public_language.key == "welcome_message"
    assert public_language.value == "Vítejte"


def test_bulk_language_response():
    """Test bulk response schema."""
    bulk_response = BulkLanguageResponse(
        language_code="en",
        key="greeting",
        value="Hello",
        message="Bulk insert completed",
        inserted_count=10,
        failed_keys=["error1", "error2"],
    )

    assert bulk_response.language_code == "en"
    assert bulk_response.key == "greeting"
    assert bulk_response.value == "Hello"
    assert bulk_response.message == "Bulk insert completed"
    assert bulk_response.inserted_count == 10
    assert bulk_response.failed_keys == ["error1", "error2"]
