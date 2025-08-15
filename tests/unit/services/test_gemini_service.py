import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

# Import the function we want to test
from services.gemini_service import stream_gemini_response


def test_stream_gemini_response_success():
    """
    Tests the 'happy path' where the API call is successful and streams chunks.
    """
    # 1. Setup Mock
    # Create mock "chunks" that simulate the Gemini API response
    mock_chunk1 = MagicMock()
    mock_chunk1.text = "Hello"
    mock_chunk2 = MagicMock()
    mock_chunk2.text = ", "
    mock_chunk3 = MagicMock()
    mock_chunk3.text = "World!"
    mock_stream = [mock_chunk1, mock_chunk2, mock_chunk3]

    # Use patch to replace the google.generativeai module
    with patch("services.gemini_service.genai") as mock_genai:
        # Configure the mock to return our desired stream
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_stream
        mock_genai.GenerativeModel.return_value = mock_model

        # 2. Act
        # Call our service function, which will now use the mock instead of the real API
        generator = stream_gemini_response("fake_key", "gemini-pro", "test message")
        result = list(
            generator
        )  # Consume the generator to get a list of yielded values

        # 3. Assert
        # Verify that the configure and model initialization were called correctly
        mock_genai.configure.assert_called_once_with(api_key="fake_key")
        mock_genai.GenerativeModel.assert_called_once_with("gemini-pro")
        mock_model.generate_content.assert_called_once_with("test message", stream=True)

        # Verify that the yielded output matches our mock chunks' text
        assert result == ["Hello", ", ", "World!"]


def test_stream_gemini_response_invalid_key():
    """
    Tests the failure path where the API key is invalid, raising an exception.
    """
    # 1. Setup Mock
    # Configure the mock to raise a specific error that simulates an invalid key
    # We create a generic Exception but include the trigger text our function looks for.
    error_message = "API_KEY_INVALID"
    error = Exception(error_message)

    with patch("services.gemini_service.genai") as mock_genai:
        # The error is raised when trying to generate content
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = error
        mock_genai.GenerativeModel.return_value = mock_model

        # 2. Act & 3. Assert
        # Use pytest.raises to check that our function correctly catches the
        # SDK's error and raises our specific HTTPException.
        with pytest.raises(HTTPException) as exc_info:
            # We must consume the generator to trigger the exception
            list(stream_gemini_response("invalid_key", "gemini-pro", "test"))

        # Check the details of the raised HTTPException
        assert exc_info.value.status_code == 401
        assert "Invalid or expired API Key" in exc_info.value.detail
