# tests/unit/services/test_gemini_service.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException

from services.gemini_service import async_stream_gemini_response, format_history_for_gemini
from db.models import Message
from google.api_core import exceptions as google_exceptions

anyio_backend_params = ["trio"]


@pytest.fixture
def mock_message_history():
    """Provides a fixture for a sample message history."""
    return [
        Message(id=1, content="What is Python?", role="user", conversation_id=1),
        Message(id=2, content="It's a programming language.", role="ai", conversation_id=1),
    ]


def test_format_history_for_gemini(mock_message_history):
    """Tests the history formatting utility function."""
    formatted = format_history_for_gemini(mock_message_history)
    assert formatted == [
        {"role": "user", "parts": ["What is Python?"]},
        {"role": "model", "parts": ["It's a programming language."]},
    ]


class MockAsyncStream:
    """Helper class to mock the async stream from the Gemini API."""
    def __init__(self, items):
        self._items = items
        self._iter = iter(self._items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


@pytest.mark.parametrize("anyio_backend", anyio_backend_params)
async def test_async_stream_gemini_response_success(anyio_backend):
    """
    Tests the 'happy path' where the API call is successful and streams chunks asynchronously.
    """
    mock_chunk1 = MagicMock()
    mock_chunk1.text = "Hello"

    with patch("services.gemini_service.genai") as mock_genai:
        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(
            return_value=MockAsyncStream([mock_chunk1])
        )
        mock_genai.GenerativeModel.return_value = mock_model

        result_stream = async_stream_gemini_response(
            "fake_key", "gemini-pro", "test message", history=[]
        )
        result = [chunk async for chunk in result_stream]

        mock_genai.configure.assert_called_once_with(api_key="fake_key")
        mock_genai.GenerativeModel.assert_called_once_with("gemini-pro")
        # Assert that the call includes the new message correctly formatted
        mock_model.generate_content_async.assert_called_once_with(
            contents=[{'role': 'user', 'parts': ['test message']}], stream=True
        )
        assert result == ["Hello"]


@pytest.mark.parametrize("anyio_backend", anyio_backend_params)
async def test_async_stream_gemini_response_with_history(anyio_backend, mock_message_history):
    """
    Tests that the service correctly formats and sends the history to the Gemini API.
    """
    mock_chunk = MagicMock()
    mock_chunk.text = "A new response."

    with patch("services.gemini_service.genai") as mock_genai:
        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(
            return_value=MockAsyncStream([mock_chunk])
        )
        mock_genai.GenerativeModel.return_value = mock_model

        result_stream = async_stream_gemini_response(
            "fake_key", "gemini-pro", "A new question", history=mock_message_history
        )
        _ = [chunk async for chunk in result_stream]

        # Verify the 'contents' argument was structured correctly with history + new message
        expected_contents = [
            {'role': 'user', 'parts': ['What is Python?']},
            {'role': 'model', 'parts': ["It's a programming language."]},
            {'role': 'user', 'parts': ['A new question']}
        ]
        mock_model.generate_content_async.assert_called_once_with(
            contents=expected_contents, stream=True
        )


@pytest.mark.parametrize("anyio_backend", anyio_backend_params)
async def test_async_stream_gemini_response_permission_denied(anyio_backend):
    error = google_exceptions.PermissionDenied("API key is invalid.")
    with patch("services.gemini_service.genai") as mock_genai:
        mock_model = MagicMock()
        mock_model.generate_content_async.side_effect = error
        mock_genai.GenerativeModel.return_value = mock_model
        with pytest.raises(HTTPException) as exc_info:
            result_stream = async_stream_gemini_response("invalid_key", "gemini-pro", "test", [])
            _ = [chunk async for chunk in result_stream]
        assert exc_info.value.status_code == 401


@pytest.mark.parametrize("anyio_backend", anyio_backend_params)
async def test_async_stream_gemini_response_quota_exceeded(anyio_backend):
    error = google_exceptions.ResourceExhausted("Quota has been exceeded.")
    with patch("services.gemini_service.genai") as mock_genai:
        mock_model = MagicMock()
        mock_model.generate_content_async.side_effect = error
        mock_genai.GenerativeModel.return_value = mock_model
        with pytest.raises(HTTPException) as exc_info:
            result_stream = async_stream_gemini_response("valid_key", "gemini-pro", "test", [])
            _ = [chunk async for chunk in result_stream]
        assert exc_info.value.status_code == 429


@pytest.mark.parametrize("anyio_backend", anyio_backend_params)
async def test_async_stream_gemini_response_generic_error(anyio_backend):
    error = Exception("A generic, unexpected error occurred.")
    with patch("services.gemini_service.genai") as mock_genai:
        mock_model = MagicMock()
        mock_model.generate_content_async.side_effect = error
        mock_genai.GenerativeModel.return_value = mock_model
        with pytest.raises(HTTPException) as exc_info:
            result_stream = async_stream_gemini_response("valid_key", "gemini-pro", "test", [])
            _ = [chunk async for chunk in result_stream]
        assert exc_info.value.status_code == 500
