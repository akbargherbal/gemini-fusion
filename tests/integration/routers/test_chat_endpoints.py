# tests/integration/routers/test_chat_endpoints.py
import pytest
from unittest.mock import patch, AsyncMock  # <-- CORRECTED THIS LINE
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlmodel import Session
from db.models import Conversation, Message

# This test now verifies the new two-phase chat architecture.


def test_initiate_chat_success(client: TestClient, session: Session):
    """
    Tests that the POST /api/chat/initiate endpoint correctly creates
    a conversation, saves the user message, and returns a session ID.
    """
    # 1. Act
    response = client.post(
        "/api/chat/initiate",
        json={"message": "Hello", "api_key": "fake_key"},
    )

    # 2. Assert
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "conversation_id" in data

    # 3. Verify Database State
    conversation_id = data["conversation_id"]
    db_conversation = session.get(Conversation, conversation_id)
    assert db_conversation is not None
    assert db_conversation.topic == "Hello"
    assert len(db_conversation.messages) == 1
    assert db_conversation.messages[0].content == "Hello"
    assert db_conversation.messages[0].role == "user"


# This is the NEW, corrected code
async def mock_successful_stream(*args, **kwargs):
    """A mock async generator for a successful stream that accepts any arguments."""
    yield "This "
    yield "is a test."


async def mock_failing_stream(*args, **kwargs):
    """A mock async generator that simulates an API key error and accepts any arguments."""
    if False:
        yield
    raise HTTPException(status_code=401, detail="Invalid API Key.")


@pytest.mark.anyio
async def test_stream_chat_success(client: TestClient, session: Session):
    """
    Tests the GET /api/chat/stream/{session_id} endpoint for a successful stream.
    """
    # 1. Setup: First, initiate a chat to get a valid session_id
    init_response = client.post(
        "/api/chat/initiate",
        json={"message": "Stream test", "api_key": "fake_key"},
    )
    session_id = init_response.json()["session_id"]

    # 2. Mock the Gemini service
    with patch("routers.chat.async_stream_gemini_response", new=mock_successful_stream):
        # 3. Act: Call the streaming endpoint
        response = client.get(f"/api/chat/stream/{session_id}")

    # 4. Assert
    assert response.status_code == 200
    content = response.text
    # Note: TestClient uses \n, not \r\n
    assert "event: stream_start\ndata: \n\n" in content
    assert "event: message\ndata: This \n\n" in content
    assert "event: message\ndata: is a test.\n\n" in content
    assert "event: stream_complete\ndata: [DONE]\n\n" in content


@pytest.mark.anyio
async def test_stream_chat_api_key_error(client: TestClient, session: Session):
    """
    Tests the GET /api/chat/stream/{session_id} endpoint for a 401 error.
    """
    # 1. Setup
    init_response = client.post(
        "/api/chat/initiate",
        json={"message": "Error test", "api_key": "bad_key"},
    )
    session_id = init_response.json()["session_id"]

    # 2. Mock the Gemini service to raise an exception
    with patch("routers.chat.async_stream_gemini_response", new=mock_failing_stream):
        # 3. Act
        response = client.get(f"/api/chat/stream/{session_id}")

    # 4. Assert
    assert response.status_code == 200
    content = response.text
    assert "event: error\ndata: Invalid API Key.\n\n" in content


def test_stream_chat_invalid_session(client: TestClient):
    """
    Tests that accessing the stream with an invalid session ID returns a 404.
    """
    response = client.get("/api/chat/stream/invalid-session-id")
    assert response.status_code == 404
    assert response.json() == {"detail": "Chat session not found or expired."}
