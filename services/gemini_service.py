# services/gemini_service.py
import google.generativeai as genai
from fastapi import HTTPException
import logging
from google.api_core import exceptions as google_exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def async_stream_gemini_response(api_key: str, model_name: str, message: str):
    """
    Initializes the Gemini client and streams the response from the model asynchronously.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response_stream = await model.generate_content_async(message, stream=True)

        async for chunk in response_stream:
            if chunk.text:
                yield chunk.text

    except google_exceptions.PermissionDenied as e:
        logger.error(f"Gemini API Permission Denied: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key. Please verify your key in the settings.",
        )
    except google_exceptions.ResourceExhausted as e:
        logger.error(f"Gemini API Resource Exhausted: {e}")
        raise HTTPException(
            status_code=429,
            detail="You have exceeded your API quota. Please check your Google AI Platform billing.",
        )
    except Exception as e:
        logger.error(f"Gemini API call failed unexpectedly: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while communicating with the AI service.",
        )