# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.engine import Engine
import os
from datetime import datetime

# Import the main FastAPI app and the dependency function we want to override
from main import app
from routers.conversations import get_session
from db.models import Conversation, Message  # Ensure metadata is populated

# --- New Robust Test Database Configuration ---
TEST_DB_PATH = "test.db"
DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"


@pytest.fixture(name="session")
def session_fixture():
    """
    Creates a clean, file-based database with a new engine for each test.
    This ensures complete isolation and proper teardown, avoiding file lock issues.
    """
    # 1. Ensure no old DB file exists before the test
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    # 2. Create a new engine for this specific test
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )

    # 3. Create tables and yield the session
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

    # 4. Teardown: Dispose of the engine and remove the database file
    engine.dispose()  # This is the crucial step to release the file lock
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


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
    base_dir = "logs/e2e_runs"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(base_dir, timestamp)
    os.makedirs(run_dir, exist_ok=True)
    yield run_dir