# tests/integration/routers/test_conversations_endpoints.py

from fastapi.testclient import TestClient
from sqlmodel import Session

# Import the models to create test data
from db.models import Conversation, Message

# Integration tests for the conversations API endpoints.
# These tests will ensure that creating, listing, and retrieving
# conversation history works correctly with the database.


def test_get_conversations_empty(client: TestClient):
    """Test fetching conversations when the database is empty."""
    response = client.get("/api/conversations")
    assert response.status_code == 200
    assert response.json() == []


def test_get_conversations_with_data(client: TestClient, session: Session):
    """Test fetching conversations when there is data."""
    # Setup: Create a conversation in the test database
    conversation = Conversation(topic="Test Topic")
    session.add(conversation)
    session.commit()

    # Act: Call the API endpoint
    response = client.get("/api/conversations")

    # Assert: Check the response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == conversation.id
    assert data[0]["topic"] == "Test Topic"


def test_get_conversation_messages_not_found(client: TestClient):
    """Test fetching messages for a conversation that does not exist."""
    response = client.get("/api/conversations/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation not found"}


def test_get_conversation_messages_success(client: TestClient, session: Session):
    """Test fetching messages for an existing conversation."""
    # Setup: Create a conversation and messages
    conversation = Conversation(topic="History Test")
    msg1 = Message(content="User message", role="user", conversation=conversation)
    msg2 = Message(content="AI response", role="ai", conversation=conversation)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    # Act: Call the API endpoint
    response = client.get(f"/api/conversations/{conversation.id}")

    # Assert: Check the response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["role"] == "user"
    assert data[0]["content"] == "User message"
    assert data[1]["role"] == "ai"
    assert data[1]["content"] == "AI response"
