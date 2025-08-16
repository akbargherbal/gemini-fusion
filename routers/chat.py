# routers/chat.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from sse_starlette.sse import EventSourceResponse
import asyncio
import uuid
from typing import Dict
from sqlalchemy.engine import Engine

# Import the dependency and models/schemas
from db.database import engine as db_engine # Rename to avoid conflict
from db.models import Conversation, Message
from routers.conversations import get_session
from schemas.chat import ChatRequest

# Import the ASYNC Gemini service
from services.gemini_service import async_stream_gemini_response

# Create an API router for chat-related endpoints
router = APIRouter()

# In-memory store for active chat sessions
active_sessions: Dict[str, dict] = {}


def prepare_conversation_and_save_user_message(
    session: Session, request: ChatRequest
) -> Conversation | None:
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


# --- MODIFIED FUNCTION ---
def save_ai_message(conversation_id: int, content: str, engine: Engine):
    """
    Synchronous, blocking function that uses a specific engine to create its
    OWN session to save the AI's message.
    """
    if not content:
        return

    # Use the provided engine to create the session
    with Session(engine) as session:
        ai_message = Message(
            content=content.strip(), role="ai", conversation_id=conversation_id
        )
        session.add(ai_message)
        session.commit()
        print(f"[INFO] AI message for conversation {conversation_id} saved to engine: {engine.url}")


@router.post("/api/chat/initiate")
async def initiate_chat(request: ChatRequest, session: Session = Depends(get_session)):
    conversation = await asyncio.to_thread(
        prepare_conversation_and_save_user_message, session, request
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    session_id = str(uuid.uuid4())
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


# --- MODIFIED ENDPOINT ---
@router.get("/api/chat/stream/{session_id}")
async def stream_chat(session_id: str, session: Session = Depends(get_session)):
    if session_id not in active_sessions:
        raise HTTPException(
            status_code=404, detail="Chat session not found or expired."
        )

    session_data = active_sessions[session_id]
    model_to_use = "gemini-1.5-flash-latest"
    
    # Determine which engine to use. In tests, the session is bound to the test engine.
    # In production, it will be the global db_engine.
    engine_to_use = session.get_bind()

    async def event_generator():
        full_ai_response = ""
        try:
            response_stream = async_stream_gemini_response(
                api_key=session_data["api_key"],
                model_name=model_to_use,
                message=session_data["message"],
            )
            yield {"event": "stream_start", "data": ""}
            async for chunk in response_stream:
                if chunk:
                    full_ai_response += chunk
                    yield {"event": "message", "data": chunk}

            # Pass the correct engine to the background task
            await asyncio.to_thread(
                save_ai_message,
                session_data["conversation_id"],
                full_ai_response,
                engine_to_use,
            )
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
            if session_id in active_sessions:
                del active_sessions[session_id]
                print(f"[INFO] Chat session {session_id} cleaned up")

    return EventSourceResponse(event_generator())


@router.post("/api/chat/sync")
def chat_sync(request: ChatRequest, session: Session = Depends(get_session)):
    conversation = prepare_conversation_and_save_user_message(session, request)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"status": "success", "message": "Message received and saved."}