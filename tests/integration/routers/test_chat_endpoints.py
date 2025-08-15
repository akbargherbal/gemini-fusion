import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import HTTPException


def test_chat_stream_success(client: TestClient):
    """
    Tests the happy path for the /api/chat/stream endpoint.
    Verifies that it streams data chunks correctly.
    """
    # 1. Setup Mock for the gemini_service
    mock_stream_data = ["This ", "is ", "a ", "stream."]

    with patch("routers.chat.stream_gemini_response") as mock_stream_service:
        mock_stream_service.return_value = mock_stream_data

        # 2. Act
        response = client.post(
            "/api/chat/stream",
            json={"message": "Hello", "api_key": "fake_key"},
        )

        # 3. Assert
        assert response.status_code == 200
        content = response.text

        # FIX: Use Windows-style line endings (\r\n) to match the test environment.
        assert "data: This \r\n\r\n" in content
        assert "data: is \r\n\r\n" in content
        assert "data: a \r\n\r\n" in content
        assert "data: stream.\r\n\r\n" in content
        assert "data: [DONE]\r\n\r\n" in content


def test_chat_stream_api_key_error(client: TestClient):
    """
    Tests the error handling path when the service raises a 401 HTTPException.
    """
    # 1. Setup Mock to raise an error
    error_detail = "Invalid or expired API Key."

    with patch("routers.chat.stream_gemini_response") as mock_stream_service:
        mock_stream_service.side_effect = HTTPException(
            status_code=401, detail=error_detail
        )

        # 2. Act
        response = client.post(
            "/api/chat/stream",
            json={"message": "Hello", "api_key": "invalid_key"},
        )

        # 3. Assert
        assert response.status_code == 200
        content = response.text

        # FIX: Use Windows-style line endings (\r\n) for the error event.
        expected_error_event = f"event: error\r\ndata: {error_detail}\r\n\r\n"
        assert expected_error_event in content
