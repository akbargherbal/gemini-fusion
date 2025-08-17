# tests/integration/routers/test_chat_endpoints.py
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlmodel import Session
from db.models import Conversation, Message

anyio_backend_params = [
    "trio",
    pytest.param(
        "asyncio",
        marks=pytest.mark.skip(
            reason="Skipping asyncio tests on Windows due to event loop conflicts."
        ),
    ),
]


def test_initiate_chat_success(client: TestClient, session: Session):
    """
    Tests that the POST /api/chat/initiate endpoint correctly creates
    a conversation, saves the user message, and returns a session ID.
    """
    response = client.post(
        "/api/chat/initiate",
        json={"message": "Hello", "api_key": "fake_key", "selected_model": "flash"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "conversation_id" in data

    conversation_id = data["conversation_id"]
    db_conversation = session.get(Conversation, conversation_id)
    assert db_conversation is not None
    assert db_conversation.topic == "Hello"
    assert len(db_conversation.messages) == 1
    assert db_conversation.messages[0].content == "Hello"
    assert db_conversation.messages[0].role == "user"


async def mock_successful_stream(*args, **kwargs):
    """A mock async generator for a successful stream that accepts any arguments."""
    assert kwargs.get("model_name") in ["gemini-1.5-pro-latest", "gemini-1.5-flash-latest"]
    yield "This "
    yield "is a test."


async def mock_failing_stream(*args, **kwargs):
    """A mock async generator that simulates an API key error and accepts any arguments."""
    if False:
        yield
    raise HTTPException(status_code=401, detail="Invalid API Key.")


@pytest.mark.parametrize("anyio_backend", anyio_backend_params)
async def test_stream_chat_success(client: TestClient, session: Session, anyio_backend):
    """
    Tests the GET /api/chat/stream/{session_id} endpoint for a successful stream.
    """
    init_response = client.post(
        "/api/chat/initiate",
        json={"message": "Stream test", "api_key": "fake_key", "selected_model": "pro"},
    )
    session_id = init_response.json()["session_id"]

    with patch("routers.chat.async_stream_gemini_response", new=mock_successful_stream):
        response = client.get(f"/api/chat/stream/{session_id}")

    assert response.status_code == 200
    normalized_content = response.text.replace("\r\n", "\n")

    assert "event: stream_start\ndata: \n\n" in normalized_content
    assert "event: message\ndata: This \n\n" in normalized_content
    assert "event: message\ndata: is a test.\n\n" in normalized_content
    assert "event: stream_complete\ndata: [DONE]\n\n" in normalized_content


@pytest.mark.parametrize("anyio_backend", anyio_backend_params)
async def test_stream_chat_api_key_error(
    client: TestClient, session: Session, anyio_backend
):
    """
    Tests the GET /api/chat/stream/{session_id} endpoint for a 401 error.
    """
    init_response = client.post(
        "/api/chat/initiate",
        json={"message": "Error test", "api_key": "bad_key", "selected_model": "flash"},
    )
    session_id = init_response.json()["session_id"]

    with patch("routers.chat.async_stream_gemini_response", new=mock_failing_stream):
        response = client.get(f"/api/chat/stream/{session_id}")

    assert response.status_code == 200
    normalized_content = response.text.replace("\r\n", "\n")

    assert "event: stream_start\ndata: \n\n" in normalized_content
    assert "event: error\ndata: Invalid API Key.\n\n" in normalized_content


def test_stream_chat_invalid_session(client: TestClient):
    """
    Tests that accessing the stream with an invalid session ID returns a 404.
    """
    response = client.get("/api/chat/stream/invalid-session-id")
    assert response.status_code == 404
    assert response.json() == {"detail": "Chat session not found or expired."}


@pytest.mark.parametrize("anyio_backend", ["trio"])
async def test_full_chat_flow_and_persistence(
    client: TestClient, session: Session, anyio_backend
):
    """
    Verifies the entire chat and persistence flow.
    """
    init_response = client.post(
        "/api/chat/initiate",
        json={"message": "Test persistence", "api_key": "fake_key", "selected_model": "flash"},
    )
    assert init_response.status_code == 200
    init_data = init_response.json()
    session_id = init_data["session_id"]
    conversation_id = init_data["conversation_id"]

    db_convo_initial = session.get(Conversation, conversation_id)
    assert db_convo_initial is not None
    assert len(db_convo_initial.messages) == 1

    with patch(
        "routers.chat.async_stream_gemini_response", new=mock_successful_stream
    ):
        stream_response = client.get(f"/api/chat/stream/{session_id}")
        _ = stream_response.text

    assert stream_response.status_code == 200

    session.commit()

    db_convo_final = session.get(Conversation, conversation_id)
    assert db_convo_final is not None
    assert len(db_convo_final.messages) == 2

    roles = {msg.role for msg in db_convo_final.messages}
    assert roles == {"user", "ai"}

    ai_message_content = [m.content for m in db_convo_final.messages if m.role == 'ai'][0]
    assert ai_message_content == "This is a test."