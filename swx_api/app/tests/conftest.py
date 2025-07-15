import pytest
from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient


from swx_api.core.config.settings import settings
from swx_api.core.main import app

# Use a test SQLite DB (or test Postgres)
DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

@pytest.fixture(scope="session")
def test_db_engine():
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_session(test_db_engine):
    with Session(test_db_engine) as session:
        yield session

@pytest.fixture(scope="module")
def client():
    return TestClient(app)
