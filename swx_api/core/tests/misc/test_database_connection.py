import pytest
from unittest.mock import MagicMock, patch
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy import event
from swx_api.core.database.db import (
    engine,
    get_db,
    log_sql_execute,
    SessionLocal,
    SessionDep,
)
from swx_api.core.middleware.logging_middleware import logger


# ---------- DATABASE CONNECTION TESTS ----------


@pytest.fixture(scope="function")
def test_db():
    """Fixture to create a fresh in-memory SQLite database for testing."""
    test_engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session


def test_database_session_creation(test_db):
    """Test database session creation and closure."""
    session = next(get_db())
    assert isinstance(session, Session)

    session.close()


# ---------- LOGGING SQL QUERIES TEST ----------


@patch.object(logger, "debug")
def test_log_sql_execute(mock_debug_logger):
    """Test SQL query logging."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    statement = "SELECT * FROM users"
    parameters = ()

    log_sql_execute(mock_conn, mock_cursor, statement, parameters, None, False)

    mock_debug_logger.assert_called_once_with(
        f"📌 SQL QUERY: {statement} | Params: {parameters}"
    )


# ---------- FASTAPI DEPENDENCY TEST ----------


@patch("swx_api.core.database.db.SessionLocal")
def test_fastapi_db_dependency(mock_session_local):
    """Test FastAPI's database session dependency injection."""
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session

    session = next(get_db())
    assert session == mock_session

    session.close.assert_called_once()
