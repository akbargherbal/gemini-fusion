from pydantic import BaseModel


class ChatRequest(BaseModel):
    """
    Schema for an incoming chat message request from the client.
    FastAPI will use this to validate the request body.
    """

    message: str
    api_key: str
    conversation_id: int | None = None


class MessageRead(BaseModel):
    """
    Schema for representing a single message when returning
    conversation history.
    """

    id: int
    content: str
    role: str  # 'user' or 'ai'


class ConversationRead(BaseModel):
    """
    Schema for representing a conversation in the list view.
    Used to populate the left sidebar.
    """

    id: int
    topic: str
