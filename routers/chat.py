from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from sse_starlette.sse import EventSourceResponse
import asyncio

# Import the dependency and models/schemas
from db.database import engine  # <-- Import the engine directly
from db.models import Conversation, Message
from routers.conversations import get_session
from schemas.chat import ChatRequest

# Import the ASYNC Gemini service
from services.gemini_service import async_stream_gemini_response

# Create an API router for chat-related endpoints
router = APIRouter()


# --- START: Synchronous Helper Functions for DB Operations ---


def prepare_conversation_and_save_user_message(
    session: Session, request: ChatRequest
) -> Conversation | None:
    """
    Synchronous, blocking function to handle all initial DB operations.
    This can be safely run in a thread pool.
    """
    conversation = None
    if request.conversation_id:
        conversation = session.get(Conversation, request.conversation_id)
        if not conversation:
            return None
    else:
        topic = request.message[:50]
        conversation = Conversation(topic=topic)
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

    user_message = Message(
        content=request.message, role="user", conversation_id=conversation.id
    )
    session.add(user_message)
    session.commit()
    session.refresh(conversation)
    print(f"[INFO] User message for conversation {conversation.id} saved.")
    return conversation


def save_ai_message(conversation_id: int, content: str):
    """
    Synchronous, blocking function that creates its OWN session to save the AI's message.
    This is safe to run in a background thread.
    """
    if not content:
        return

    # Create a new, independent session for this background task
    with Session(engine) as session:
        ai_message = Message(
            content=content.strip(), role="ai", conversation_id=conversation_id
        )
        session.add(ai_message)
        session.commit()
        print(f"[INFO] AI message for conversation {conversation_id} saved.")


# --- END: Synchronous Helper Functions ---


@router.post("/api/chat/stream")
async def chat_stream(request: ChatRequest, session: Session = Depends(get_session)):
    """
    Handles the streaming chat endpoint using proper concurrency for blocking calls.
    """
    model_to_use = "gemini-1.5-flash-latest"

    # Run the initial blocking DB operations in a separate thread
    conversation = await asyncio.to_thread(
        prepare_conversation_and_save_user_message, session, request
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    async def event_generator():
        """
        A generator that streams the AI response and saves the result in the background.
        """
        full_ai_response = ""
        try:
            response_stream = async_stream_gemini_response(
                api_key=request.api_key,
                model_name=model_to_use,
                message=request.message,
            )

            async for chunk in response_stream:
                if chunk:
                    full_ai_response += chunk
                    yield {"data": chunk}

            # Run the final save operation in a thread.
            # This function now creates its own session, so we don't pass the expired one.
            await asyncio.to_thread(save_ai_message, conversation.id, full_ai_response)

            yield {"data": "[DONE]"}

        except HTTPException as e:
            print(f"[ERROR] HTTPException in stream: {e.detail}")
            yield {"event": "error", "data": e.detail}
        except Exception as e:
            print(f"[ERROR] Unexpected Exception in stream: {e}")
            yield {
                "event": "error",
                "data": "An unexpected error occurred on the server.",
            }

    return EventSourceResponse(event_generator())


@router.post("/api/chat/sync")
def chat_sync(request: ChatRequest, session: Session = Depends(get_session)):
    """
    Temporary synchronous endpoint to test conversation and message creation.
    """
    conversation = prepare_conversation_and_save_user_message(session, request)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    return {"status": "success", "message": "Message received and saved."}
