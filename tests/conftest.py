# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
import os
from datetime import datetime

# Import the main FastAPI app and the dependency function we want to override
from main import app
from routers.conversations import get_session
from db.models import Conversation, Message  # Ensure metadata is populated

# This is the test database URL
DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


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

    app.dependency_overrides[get_session] = get_session_override

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def test_run_dir():
    """Create a unique, timestamped directory for a single test run."""
    # Define the base directory for all E2E test runs
    base_dir = "logs/e2e_runs"
    # Create a timestamp string for the current run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Define the full path for this specific test run's artifacts
    run_dir = os.path.join(base_dir, timestamp)
    # Create the directory
    os.makedirs(run_dir, exist_ok=True)
    # Yield the path to the test function
    yield run_dir
