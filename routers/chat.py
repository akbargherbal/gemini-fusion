from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from sse_starlette.sse import EventSourceResponse
import asyncio
import uuid
from typing import Dict

# Import the dependency and models/schemas
from db.database import engine  # <-- Import the engine directly
from db.models import Conversation, Message
from routers.conversations import get_session
from schemas.chat import ChatRequest

# Import the ASYNC Gemini service
from services.gemini_service import async_stream_gemini_response

# Create an API router for chat-related endpoints
router = APIRouter()

# In-memory store for active chat sessions
active_sessions: Dict[str, dict] = {}


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


@router.post("/api/chat/initiate")
async def initiate_chat(request: ChatRequest, session: Session = Depends(get_session)):
    """
    Phase 1: Initiate chat by saving user message and creating a streaming session.
    Returns a session ID for the SSE connection.
    """
    # Run the initial blocking DB operations in a separate thread
    conversation = await asyncio.to_thread(
        prepare_conversation_and_save_user_message, session, request
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    # Create a unique session ID for this chat stream
    session_id = str(uuid.uuid4())

    # Store session data for the streaming endpoint
    active_sessions[session_id] = {
        "conversation_id": conversation.id,
        "api_key": request.api_key,
        "message": request.message,
        "created_at": asyncio.get_event_loop().time(),
    }

    print(
        f"[INFO] Chat session {session_id} initiated for conversation {conversation.id}"
    )

    return {"session_id": session_id, "conversation_id": conversation.id}


@router.get("/api/chat/stream/{session_id}")
async def stream_chat(session_id: str):
    """
    Phase 2: Stream the AI response using Server-Sent Events.
    This endpoint is called via HTMX SSE connection.
    """
    # Check if session exists
    if session_id not in active_sessions:
        raise HTTPException(
            status_code=404, detail="Chat session not found or expired."
        )

    session_data = active_sessions[session_id]
    model_to_use = "gemini-1.5-flash-latest"

    async def event_generator():
        """
        Generator that streams the AI response and saves the result in the background.
        """
        full_ai_response = ""
        try:
            response_stream = async_stream_gemini_response(
                api_key=session_data["api_key"],
                model_name=model_to_use,
                message=session_data["message"],
            )

            # Send start event
            yield {"event": "stream_start", "data": ""}

            async for chunk in response_stream:
                if chunk:
                    full_ai_response += chunk
                    yield {"event": "message", "data": chunk}

            # Save the complete AI response in the background
            await asyncio.to_thread(
                save_ai_message, session_data["conversation_id"], full_ai_response
            )

            # Send completion event
            yield {"event": "stream_complete", "data": "[DONE]"}

        except HTTPException as e:
            print(f"[ERROR] HTTPException in stream {session_id}: {e.detail}")
            yield {"event": "error", "data": e.detail}
        except Exception as e:
            print(f"[ERROR] Unexpected Exception in stream {session_id}: {e}")
            yield {
                "event": "error",
                "data": "An unexpected error occurred on the server.",
            }
        finally:
            # Clean up the session
            if session_id in active_sessions:
                del active_sessions[session_id]
                print(f"[INFO] Chat session {session_id} cleaned up")

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
