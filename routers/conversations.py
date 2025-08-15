from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

# Import the database engine and session management from our db module
from db.database import engine

# Import the data models and schemas
from db.models import Conversation
from schemas.chat import ConversationRead, MessageRead

# Create an API router for conversation-related endpoints
router = APIRouter()


# Dependency function to get a database session for a request
def get_session():
    """
    Yields a database session to be used in a request.
    Ensures the session is always closed after the request.
    """
    with Session(engine) as session:
        yield session


@router.get("/api/conversations", response_model=list[ConversationRead])
def get_conversations(session: Session = Depends(get_session)):
    """
    Fetches a list of all existing conversation topics and their IDs
    to populate the left sidebar.
    """
    conversations = session.exec(select(Conversation)).all()
    return conversations


@router.get("/api/conversations/{conversation_id}", response_model=list[MessageRead])
def get_conversation_messages(
    conversation_id: int, session: Session = Depends(get_session)
):
    """
    Retrieves the full message history for a selected conversation.
    """
    # Get the conversation by its ID. If not found, get() returns None.
    conversation = session.get(Conversation, conversation_id)

    if not conversation:
        # If no conversation is found, raise a 404 error
        raise HTTPException(status_code=404, detail="Conversation not found")

    # The response model will automatically format the messages
    # using the MessageRead schema.
    return conversation.messages
