# tests/integration/routers/test_chat_endpoints.py
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlmodel import Session
from db.models import Conversation, Message

anyio_backend_params = ["trio"]


def test_initiate_chat_creates_conversation_and_message(client: TestClient, session: Session):
    """
    Tests that initiating a chat with no conversation_id creates a new
    conversation and saves the first user message.
    """
    response = client.post(
        "/api/chat/initiate",
        json={"message": "Hello", "api_key": "fake_key", "selected_model": "flash"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "conversation_id" in data

    # Verify in the database
    db_conversation = session.get(Conversation, data["conversation_id"])
    assert db_conversation is not None
    assert db_conversation.topic == "Hello"
    assert len(db_conversation.messages) == 1
    assert db_conversation.messages[0].content == "Hello"
    assert db_conversation.messages[0].role == "user"


async def mock_successful_stream_gen(*args, **kwargs):
    """A mock async generator that yields a simple response."""
    yield "This "
    yield "is a test."


async def mock_failing_stream(*args, **kwargs):
    """A mock stream that simulates an API key failure by raising."""
    if False:
        yield  # This makes it a generator
    raise HTTPException(status_code=401, detail="Invalid API Key.")


@pytest.mark.parametrize("anyio_backend", anyio_backend_params)
async def test_stream_chat_with_history_success(client: TestClient, session: Session, anyio_backend):
    """
    Tests the full chat flow, ensuring that existing conversation history
    is correctly fetched and passed to the Gemini service.
    """
    # 1. Setup: Create a conversation with existing messages in the database
    convo = Conversation(topic="Test History")
    msg1 = Message(content="First user message", role="user", conversation=convo)
    msg2 = Message(content="First AI response", role="ai", conversation=convo)
    session.add_all([convo, msg1, msg2])
    session.commit()
    session.refresh(convo)

    # 2. Initiate a new chat turn in the same conversation
    init_response = client.post(
        "/api/chat/initiate",
        json={
            "message": "Second user message",
            "api_key": "fake_key",
            "selected_model": "pro",
            "conversation_id": convo.id,
        },
    )
    assert init_response.status_code == 200
    session_id = init_response.json()["session_id"]

    # 3. Mock the Gemini service and stream the response
    # --- THE FIX ---
    # We replace AsyncMock with a MagicMock that directly returns an async generator object.
    # This correctly simulates the behavior of the real streaming service.
    mock_gemini_service = MagicMock(return_value=mock_successful_stream_gen())

    with patch("routers.chat.async_stream_gemini_response", new=mock_gemini_service):
        response = client.get(f"/api/chat/stream/{session_id}")

    # 4. Assertions
    assert response.status_code == 200
    assert "event: stream_complete" in response.text

    # 5. CRITICAL: Verify the service was called with the correct history
    mock_gemini_service.assert_called_once()
    # For MagicMock, the call arguments are in the `.call_args.kwargs` attribute.
    call_kwargs = mock_gemini_service.call_args.kwargs

    assert call_kwargs["message"] == "Second user message"

    passed_history = call_kwargs["history"]
    assert len(passed_history) == 2
    assert passed_history[0].content == "First user message"
    assert passed_history[1].content == "First AI response"


@pytest.mark.parametrize("anyio_backend", anyio_backend_params)
async def test_stream_chat_api_key_error(client: TestClient, session: Session, anyio_backend):
    """
    Tests that a streaming error from the service is correctly propagated
    to the client as an SSE error event.
    """
    init_response = client.post(
        "/api/chat/initiate",
        json={"message": "Error test", "api_key": "bad_key", "selected_model": "flash"},
    )
    session_id = init_response.json()["session_id"]

    with patch("routers.chat.async_stream_gemini_response", new=mock_failing_stream):
        response = client.get(f"/api/chat/stream/{session_id}")

    assert response.status_code == 200
    assert "event: error" in response.text
    assert "Invalid API Key" in response.text
