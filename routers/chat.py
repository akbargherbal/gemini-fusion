from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from sse_starlette.sse import EventSourceResponse
import asyncio

# Import the dependency and models/schemas
from db.models import Conversation, Message
from routers.conversations import get_session
from schemas.chat import ChatRequest

# Import the new Gemini service
from services.gemini_service import stream_gemini_response

# Create an API router for chat-related endpoints
router = APIRouter()


@router.post("/api/chat/stream")
async def chat_stream(request: ChatRequest, session: Session = Depends(get_session)):
    """
    Handles the streaming chat endpoint.
    Receives a message, calls the Gemini service, and streams the response back.
    """
    # NOTE: Database logic for saving messages will be added in a future step
    # as per the project plan. This endpoint currently only handles the streaming.

    async def event_generator():
        """A generator function that yields SSE events."""
        try:
            # Call our synchronous service function that yields response chunks
            response_stream = stream_gemini_response(
                api_key=request.api_key,
                model_name="gemini-pro",  # Placeholder, will be dynamic later
                message=request.message,
            )

            # Iterate over the synchronous generator from the service
            for chunk in response_stream:
                # In an async context, it's good practice to yield control
                # briefly to the event loop, especially in a tight loop.
                await asyncio.sleep(0)
                # Yield the data in the format SSE expects: a dictionary.
                yield {"data": chunk}

            # After the stream is complete, send a special DONE message
            yield {"data": "[DONE]"}

        except HTTPException as e:
            # If our service raises an HTTPException (e.g., for a bad API key),
            # we can catch it and yield an error event to the client.
            yield {"event": "error", "data": e.detail}
        except Exception:
            # For any other unexpected errors.
            yield {
                "event": "error",
                "data": "An unexpected error occurred on the server.",
            }

    return EventSourceResponse(event_generator())


@router.post("/api/chat/sync")
def chat_sync(request: ChatRequest, session: Session = Depends(get_session)):
    """
    Temporary synchronous endpoint to test conversation and message creation.
    Accepts a message, saves it, and returns a hardcoded JSON response.
    """
    # Step 1: Find the conversation or create a new one
    conversation = None
    if request.conversation_id:
        conversation = session.get(Conversation, request.conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation with id {request.conversation_id} not found.",
            )
    else:
        # Create a new conversation
        # Topic is the first 50 chars of the user's message
        topic = request.message[:50]
        conversation = Conversation(topic=topic)
        session.add(conversation)
        # We need to commit here to get the conversation.id for the message
        session.commit()
        session.refresh(conversation)

    # Step 2: Create the user's message and link it to the conversation
    user_message = Message(
        content=request.message, role="user", conversation_id=conversation.id
    )

    # Step 3: Add the message to the session and commit
    session.add(user_message)
    session.commit()

    # Step 4: Return a simple confirmation response
    return {"status": "success", "message": "Message received and saved."}
