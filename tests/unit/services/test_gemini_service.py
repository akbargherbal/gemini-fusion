# tests/unit/services/test_gemini_service.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException

from services.gemini_service import async_stream_gemini_response
from google.api_core import exceptions as google_exceptions

anyio_backend_params = [
    "trio",
    pytest.param(
        "asyncio",
        marks=pytest.mark.skip(
            reason="Skipping asyncio tests on Windows due to event loop conflicts."
        ),
    ),
]


@pytest.mark.parametrize("anyio_backend", anyio_backend_params)
async def test_async_stream_gemini_response_success(anyio_backend):
    """
    Tests the 'happy path' where the API call is successful and streams chunks asynchronously.
    """
    mock_chunk1 = MagicMock()
    mock_chunk1.text = "Hello"
    mock_chunk2 = MagicMock()
    mock_chunk2.text = ", "
    mock_chunk3 = MagicMock()
    mock_chunk3.text = "World!"

    class MockAsyncStream:
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

    with patch("services.gemini_service.genai") as mock_genai:
        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(
            return_value=MockAsyncStream([mock_chunk1, mock_chunk2, mock_chunk3])
        )
        mock_genai.GenerativeModel.return_value = mock_model

        result_stream = async_stream_gemini_response(
            "fake_key", "gemini-pro", "test message"
        )
        result = [chunk async for chunk in result_stream]

        mock_genai.configure.assert_called_once_with(api_key="fake_key")
        mock_genai.GenerativeModel.assert_called_once_with("gemini-pro")
        mock_model.generate_content_async.assert_called_once_with(
            "test message", stream=True
        )
        assert result == ["Hello", ", ", "World!"]


@pytest.mark.parametrize("anyio_backend", anyio_backend_params)
async def test_async_stream_gemini_response_permission_denied(anyio_backend):
    """
    Tests that a google_exceptions.PermissionDenied is handled as a 401 error.
    """
    error = google_exceptions.PermissionDenied("API key is invalid.")

    with patch("services.gemini_service.genai") as mock_genai:
        mock_model = MagicMock()
        mock_model.generate_content_async.side_effect = error
        mock_genai.GenerativeModel.return_value = mock_model

        with pytest.raises(HTTPException) as exc_info:
            result_stream = async_stream_gemini_response(
                "invalid_key", "gemini-pro", "test"
            )
            _ = [chunk async for chunk in result_stream]

        assert exc_info.value.status_code == 401
        assert "Invalid API Key" in exc_info.value.detail


@pytest.mark.parametrize("anyio_backend", anyio_backend_params)
async def test_async_stream_gemini_response_quota_exceeded(anyio_backend):
    """
    Tests that a google_exceptions.ResourceExhausted is handled as a 429 error.
    """
    error = google_exceptions.ResourceExhausted("Quota has been exceeded.")

    with patch("services.gemini_service.genai") as mock_genai:
        mock_model = MagicMock()
        mock_model.generate_content_async.side_effect = error
        mock_genai.GenerativeModel.return_value = mock_model

        with pytest.raises(HTTPException) as exc_info:
            result_stream = async_stream_gemini_response(
                "valid_key", "gemini-pro", "test"
            )
            _ = [chunk async for chunk in result_stream]

        assert exc_info.value.status_code == 429
        assert "exceeded your API quota" in exc_info.value.detail


@pytest.mark.parametrize("anyio_backend", anyio_backend_params)
async def test_async_stream_gemini_response_generic_error(anyio_backend):
    """
    Tests that any other Exception is handled as a 500 error.
    """
    error = Exception("A generic, unexpected error occurred.")

    with patch("services.gemini_service.genai") as mock_genai:
        mock_model = MagicMock()
        mock_model.generate_content_async.side_effect = error
        mock_genai.GenerativeModel.return_value = mock_model

        with pytest.raises(HTTPException) as exc_info:
            result_stream = async_stream_gemini_response(
                "valid_key", "gemini-pro", "test"
            )
            _ = [chunk async for chunk in result_stream]

        assert exc_info.value.status_code == 500
        assert "unexpected error occurred" in exc_info.value.detail