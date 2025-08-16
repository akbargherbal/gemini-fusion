import google.generativeai as genai
from fastapi import HTTPException
import logging

# Configure logging to see potential errors in the console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def async_stream_gemini_response(api_key: str, model_name: str, message: str):
    """
    Initializes the Gemini client and streams the response from the model asynchronously.
    This is a native async generator.
    """
    try:
        # Configure the generative AI client with the provided API key
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)

        # Use the asynchronous version of the method to get an async stream
        response_stream = await model.generate_content_async(message, stream=True)

        # Asynchronously iterate over the stream and yield each chunk
        async for chunk in response_stream:
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
