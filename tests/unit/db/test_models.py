import pytest
from sqlmodel import Session, SQLModel, create_engine

# Import the models we defined
from db.models import Conversation, Message


# Unit tests for the database models (Conversation, Message).
# These tests will verify model creation, relationships,
# and any specific logic within the models themselves.


# Fixture to create a fresh, in-memory SQLite database for each test function
@pytest.fixture(name="session")
def session_fixture():
    # Use an in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")
    # Create the database tables based on the SQLModel definitions
    SQLModel.metadata.create_all(engine)
    # Yield a session to be used by the test function
    with Session(engine) as session:
        yield session


def test_create_and_link_models(session: Session):
    """
    Tests creating a Conversation and linking Messages to it.
    """
    # 1. Create instances of the models
    conversation_1 = Conversation(topic="Test Topic")
    message_1_user = Message(content="Hello AI!", role="user")
    message_2_ai = Message(content="Hello User! How can I help?", role="ai")

    # 2. Establish the relationship
    # Appending to the list automatically sets the .conversation attribute on the message
    conversation_1.messages.append(message_1_user)
    conversation_1.messages.append(message_2_ai)

    # 3. Add to the session and commit to the database
    session.add(conversation_1)
    session.commit()

    # 4. Refresh the objects to get the updated state from the DB (like assigned IDs)
    session.refresh(conversation_1)
    session.refresh(message_1_user)
    session.refresh(message_2_ai)

    # 5. Assert that the data was saved correctly
    assert conversation_1.id is not None
    assert conversation_1.topic == "Test Topic"
    assert len(conversation_1.messages) == 2

    # 6. Assert that the relationship is correctly loaded
    assert conversation_1.messages[0].content == "Hello AI!"
    assert conversation_1.messages[0].role == "user"
    assert conversation_1.messages[1].content == "Hello User! How can I help?"

    # 7. Assert that the back-population works
    assert message_1_user.conversation == conversation_1
    assert message_2_ai.conversation_id == conversation_1.id
