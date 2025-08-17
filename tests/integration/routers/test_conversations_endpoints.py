# tests/integration/routers/test_conversations_endpoints.py
from fastapi.testclient import TestClient
from sqlmodel import Session
from db.models import Conversation, Message

def test_get_conversations_empty(client: TestClient):
    response = client.get("/api/conversations")
    assert response.status_code == 200
    assert response.json() == []

def test_get_conversations_with_data(client: TestClient, session: Session):
    conversation = Conversation(topic="Test Topic")
    session.add(conversation)
    session.commit()
    response = client.get("/api/conversations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["topic"] == "Test Topic"

def test_get_conversation_messages_not_found(client: TestClient):
    response = client.get("/api/conversations/999")
    assert response.status_code == 404

def test_get_conversation_messages_success(client: TestClient, session: Session):
    conversation = Conversation(topic="History Test")
    msg1 = Message(content="User message", role="user", conversation=conversation)
    msg2 = Message(content="AI response", role="ai", conversation=conversation)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    response = client.get(f"/api/conversations/{conversation.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2