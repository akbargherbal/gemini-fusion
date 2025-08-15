# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

# Import the main FastAPI app and the dependency function we want to override
from main import app
from routers.conversations import get_session
from db.models import Conversation, Message  # Ensure metadata is populated

# This is the test database URL
DATABASE_URL = "sqlite:///:memory:"

# --- START OF FIX ---
# The 'connect_args' is required for SQLite.
# The 'poolclass=StaticPool' is the crucial part. It tells SQLAlchemy to use a
# single, static connection for the entire lifetime of the engine, ensuring
# that the connection that creates the tables is the same one used by the tests.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
# --- END OF FIX ---


@pytest.fixture(name="session")
def session_fixture():
    """Create a clean database session for each test."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a TestClient that uses the test database."""

    def get_session_override():
        """Override the get_session dependency to use the test session."""
        return session

    # Override the app's dependency
    app.dependency_overrides[get_session] = get_session_override

    # Yield the TestClient
    with TestClient(app) as client:
        yield client

    # Clean up the override after the test
    app.dependency_overrides.clear()
