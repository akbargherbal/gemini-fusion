# tests/integration/routers/test_chat_endpoints.py
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlmodel import Session
from db.models import Conversation

anyio_backend_params = ["trio"]

def test_initiate_chat_success(client: TestClient, session: Session):
    response = client.post(
        "/api/chat/initiate",
        json={"message": "Hello", "api_key": "fake_key", "selected_model": "flash"},
    )
    assert response.status_code == 200
    data = response.json()
    db_conversation = session.get(Conversation, data["conversation_id"])
    assert db_conversation is not None
    assert len(db_conversation.messages) == 1

async def mock_successful_stream(*args, **kwargs):
    yield "This "
    yield "is a test."

async def mock_failing_stream(*args, **kwargs):
    if False: yield
    raise HTTPException(status_code=401, detail="Invalid API Key.")

@pytest.mark.parametrize("anyio_backend", anyio_backend_params)
async def test_stream_chat_success(client: TestClient, session: Session, anyio_backend):
    init_response = client.post(
        "/api/chat/initiate",
        json={"message": "Stream test", "api_key": "fake_key", "selected_model": "pro"},
    )
    session_id = init_response.json()["session_id"]
    with patch("routers.chat.async_stream_gemini_response", new=mock_successful_stream):
        response = client.get(f"/api/chat/stream/{session_id}")
    assert response.status_code == 200
    assert "event: stream_complete" in response.text

@pytest.mark.parametrize("anyio_backend", anyio_backend_params)
async def test_stream_chat_api_key_error(client: TestClient, session: Session, anyio_backend):
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