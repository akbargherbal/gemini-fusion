import google.generativeai as genai
from fastapi import HTTPException
import logging

# Configure logging to see potential errors in the console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def stream_gemini_response(api_key: str, model_name: str, message: str):
    """
    Initializes the Gemini client and streams the response from the model.

    Args:
        api_key: The user-provided Google API key.
        model_name: The name of the model to use (e.g., 'gemini-pro').
        message: The user's message content.

    Yields:
        str: Chunks of the response text from the Gemini API.

    Raises:
        HTTPException: If there is an authentication or permission issue with the API key.
        HTTPException: For other unexpected errors during the API call.
    """
    try:
        # Configure the generative AI client with the provided API key
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)

        # Start generating content with streaming enabled
        # The empty history is for starting a new, non-conversational chat
        response_stream = model.generate_content(message, stream=True)

        # Yield each chunk of text from the stream
        for chunk in response_stream:
            # The API might send empty chunks or chunks without text.
            if chunk.text:
                yield chunk.text

    except Exception as e:
        # Log the full, detailed error for server-side debugging
        logger.error(f"Gemini API call failed unexpectedly: {e}")

        # The google-generativeai SDK often wraps errors. We check the string
        # representation for common, user-fixable authentication issues.
        error_text = str(e).lower()
        if "api_key_invalid" in error_text or "permission" in error_text:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired API Key. Please verify your key in the settings.",
            )

        # For any other exception, return a generic 500 server error
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while communicating with the AI service.",
        )
