from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

# Import the database engine and session management from our db module
from db.database import engine

# Import the data models and schemas
from db.models import Conversation
from schemas.chat import ConversationRead, MessageRead


from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Create an API router for conversation-related endpoints
router = APIRouter()
# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Dependency function to get a database session for a request
def get_session():
    """
    Yields a database session to be used in a request.
    Ensures the session is always closed after the request.
    """
    print("[DIAGNOSTIC] Creating database session.")
    with Session(engine) as session:
        try:
            yield session
        finally:
            print("[DIAGNOSTIC] Closing database session.")


@router.get("/api/conversations/list", response_class=HTMLResponse)
def get_conversations_list(
    request: Request, session: Session = Depends(get_session)
):
    """
    Fetches all conversations and returns them as an HTML fragment
    to be injected into the sidebar by HTMX.
    """
    conversations = session.exec(select(Conversation).order_by(Conversation.id.desc())).all()
    return templates.TemplateResponse(
        "snippets/conversation_list.html",
        {"request": request, "conversations": conversations},
    )


@router.get("/api/conversations", response_model=list[ConversationRead])
def get_conversations(session: Session = Depends(get_session)):
    """
    Fetches a list of all existing conversation topics and their IDs
    to populate the left sidebar. (JSON endpoint for potential future use)
    """
    conversations = session.exec(select(Conversation).order_by(Conversation.id.desc())).all()
    return conversations


@router.get(
    "/api/conversations/{conversation_id}/messages", response_class=HTMLResponse
)
def get_conversation_messages_html(
    conversation_id: int, request: Request, session: Session = Depends(get_session)
):
    """
    Retrieves the full message history for a selected conversation and
    returns it as an HTML fragment.
    """
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        # In an HTMX context, it's often better to return an empty fragment
        # or a specific error message fragment than a 404 error code.
        return HTMLResponse(content="", status_code=404)

    return templates.TemplateResponse(
        "snippets/message_history.html",
        {"request": request, "messages": conversation.messages},
    )


@router.get("/api/conversations/{conversation_id}", response_model=list[MessageRead])
def get_conversation_messages(
    conversation_id: int, session: Session = Depends(get_session)
):
    """
    Retrieves the full message history for a selected conversation.
    (JSON endpoint for potential future use)
    """
    conversation = session.get(Conversation, conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation.messages