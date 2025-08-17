from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel


class Conversation(SQLModel, table=True):
    """Represents a single chat thread."""

    id: Optional[int] = Field(default=None, primary_key=True)
    topic: str = Field(index=True)

    # The one-to-many relationship to the Message table
    # This attribute will hold a list of Message objects
    messages: List["Message"] = Relationship(back_populates="conversation")


class Message(SQLModel, table=True):
    """Represents a single message within a Conversation."""

    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    role: str  # "user" or "ai"

    # The foreign key linking back to the Conversation
    conversation_id: Optional[int] = Field(default=None, foreign_key="conversation.id")
    # The one-to-one relationship back to the Conversation object
    conversation: Optional["Conversation"] = Relationship(back_populates="messages")