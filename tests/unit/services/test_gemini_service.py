# tests/unit/services/test_gemini_service.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException

# Import the ASYNC function we want to test
from services.gemini_service import async_stream_gemini_response


@pytest.mark.anyio
async def test_async_stream_gemini_response_success():
    """
    Tests the 'happy path' where the API call is successful and streams chunks asynchronously.
    """
    # 1. Setup Mock
    # Create mock "chunks" that simulate the Gemini API response
    mock_chunk1 = MagicMock()
    mock_chunk1.text = "Hello"
    mock_chunk2 = MagicMock()
    mock_chunk2.text = ", "
    mock_chunk3 = MagicMock()
    mock_chunk3.text = "World!"

    # Create an async iterator from our mock chunks
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

    # Use patch to replace the google.generativeai module
    with patch("services.gemini_service.genai") as mock_genai:
        # Configure the mock to return our desired async stream
        mock_model = MagicMock()
        # The async method now needs to return an awaitable that returns our async iterator
        mock_model.generate_content_async = AsyncMock(
            return_value=MockAsyncStream([mock_chunk1, mock_chunk2, mock_chunk3])
        )
        mock_genai.GenerativeModel.return_value = mock_model

        # 2. Act
        # Call our async service function
        result_stream = async_stream_gemini_response(
            "fake_key", "gemini-pro", "test message"
        )
        # Consume the async generator to get a list of yielded values
        result = [chunk async for chunk in result_stream]

        # 3. Assert
        # Verify that the configure and model initialization were called correctly
        mock_genai.configure.assert_called_once_with(api_key="fake_key")
        mock_genai.GenerativeModel.assert_called_once_with("gemini-pro")
        mock_model.generate_content_async.assert_called_once_with(
            "test message", stream=True
        )

        # Verify that the yielded output matches our mock chunks' text
        assert result == ["Hello", ", ", "World!"]


@pytest.mark.anyio
async def test_async_stream_gemini_response_invalid_key():
    """
    Tests the failure path where the API key is invalid, raising an exception.
    """
    # 1. Setup Mock
    error_message = "API_KEY_INVALID"
    error = Exception(error_message)

    with patch("services.gemini_service.genai") as mock_genai:
        mock_model = MagicMock()
        # The async method raises the error when awaited
        mock_model.generate_content_async.side_effect = error
        mock_genai.GenerativeModel.return_value = mock_model

        # 2. Act & 3. Assert
        # Use pytest.raises to check that our function correctly raises our HTTPException
        with pytest.raises(HTTPException) as exc_info:
            # We must consume the async generator to trigger the exception
            result_stream = async_stream_gemini_response(
                "invalid_key", "gemini-pro", "test"
            )
            _ = [chunk async for chunk in result_stream]

        # Check the details of the raised HTTPException
        assert exc_info.value.status_code == 401
        assert "Invalid or expired API Key" in exc_info.value.detail
