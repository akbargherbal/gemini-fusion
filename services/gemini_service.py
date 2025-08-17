# services/gemini_service.py
import google.generativeai as genai
from fastapi import HTTPException
import logging
from google.api_core import exceptions as google_exceptions
from typing import List
from db.models import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def format_history_for_gemini(history: List[Message]):
    """
    Formats the conversation history from SQLModel objects into the
    structure required by the Google Gemini API.
    """
    gemini_history = []
    for msg in history:
        # The Gemini API uses 'model' for the AI's role
        role = "model" if msg.role == "ai" else "user"
        gemini_history.append({"role": role, "parts": [msg.content]})
    return gemini_history


async def async_stream_gemini_response(
    api_key: str, model_name: str, message: str, history: List[Message]
):
    """
    Initializes the Gemini client and streams the response from the model asynchronously,
    now including conversation history for context.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)

        # Format the history and combine it with the new message
        # The history should not include the current user message, which is sent separately.
        gemini_history = format_history_for_gemini(history)
        
        logger.info(f"Sending request to Gemini with {len(gemini_history)} history messages.")

        # The last message is the new prompt
        response_stream = await model.generate_content_async(
            contents=[*gemini_history, {"role": "user", "parts": [message]}], stream=True
        )

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
