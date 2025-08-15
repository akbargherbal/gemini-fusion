# Technical Foundation Specification: Gemini Fusion v0.1.0

This document provides the concrete technical specifications for building version 0.1.0 of the Gemini Fusion application. It translates the strategic blueprint into definitive architectural decisions, API contracts, and data models to guide implementation.

---

### **1. Technology Stack Decisions**

Based on the strategic blueprint, the following technology stack is mandated to prioritize development velocity, a smooth learning curve, and alignment with modern Python web standards.

- **Backend Framework:** **FastAPI**. It is chosen for its high performance, asynchronous capabilities, and automatic data validation and documentation powered by Pydantic.
- **Web Server:** **Uvicorn**. The recommended high-performance ASGI server for FastAPI.
- **Database:** **SQLite**. Selected to eliminate setup and configuration overhead, allowing complete focus on application logic for v0.1.0. The database will exist as a single `gemini_fusion.db` file in the project root.
- **Database Interaction:** **SQLModel**. Chosen for its modern, Pydantic-based approach to ORM. Its design provides typing, validation, and database mapping in single, unified models, which is ideal for a FastAPI application.
- **Frontend Integration:** **HTMX** and **Alpine.js**. The frontend will be served directly by FastAPI using Jinja2 templates. The core real-time chat functionality will be powered by **Server-Sent Events (SSE)**, which integrates seamlessly with HTMX.
- **Key Python Dependencies:**
  - `fastapi`: The core web framework.
  - `uvicorn[standard]`: The application server.
  - `sqlmodel`: The Object-Relational Mapper.
  - `jinja2`: For server-side HTML templating.
  - `python-dotenv`: To manage environment variables, specifically the `GOOGLE_API_KEY`.
  - `google-generativeai`: The official Python SDK for the Gemini API.
  - `sse-starlette`: A server-sent event middleware for FastAPI/Starlette.

---

### **2. API Contract Definition**

The API will be structured around conversations and real-time messaging. All endpoints will be prefixed with `/api`.

#### **Core Business Logic Endpoints**

1.  **`POST /api/chat/stream`**: The primary endpoint for handling chat messages.

    - **Description**: Receives a user's message, the conversation context, and the API key. It initiates a streaming connection with the Google Gemini API and relays the response back to the client token-by-token using Server-Sent Events (SSE).
    - **Request Schema (`ChatRequest`)**:

      ```python
      from pydantic import BaseModel

      class ChatRequest(BaseModel):
          message: str
          api_key: str
          # conversation_id can be optional to start a new chat
          conversation_id: int | None = None
      ```

    - **Response**: An `EventSourceResponse` that streams SSE messages. Each message will contain a chunk of the AI's response. The stream will be terminated with a special `[DONE]` message.

2.  **`GET /api/conversations`**:

    - **Description**: Fetches a list of all existing conversation topics and their IDs to populate the left sidebar.
    - **Response Schema (`list[ConversationRead]`)**:

      ```python
      from pydantic import BaseModel

      class ConversationRead(BaseModel):
          id: int
          topic: str
      ```

3.  **`GET /api/conversations/{conversation_id}`**:

    - **Description**: Retrieves the full message history for a selected conversation.
    - **Response Schema (`list[MessageRead]`)**:

      ```python
      from pydantic import BaseModel

      class MessageRead(BaseModel):
          id: int
          content: str
          role: str # 'user' or 'ai'
      ```

#### **Error Response Patterns**

Errors will use standard HTTP status codes and return a JSON object with a `detail` key.

- **`400 Bad Request`**: For validation errors (e.g., missing `message` in `ChatRequest`).
- **`401 Unauthorized`**: For invalid or missing Google API keys.
- **`404 Not Found`**: For requesting a `conversation_id` that does not exist.
- **`500 Internal Server Error`**: For unexpected server-side issues.

---

### **3. Data Model Architecture**

The database schema will be defined using SQLModel classes. This approach ensures our database tables are directly mapped from validated Python objects.

#### **Primary Entities and Relationships**

- **Conversation**: Represents a single chat thread. It has a one-to-many relationship with the `Message` table.
- **Message**: Represents a single message within a `Conversation`, belonging to either the 'user' or 'ai'.

#### **Database Schema (SQLModel Definitions)**

```python
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

class Conversation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    topic: str = Field(index=True)

    # The one-to-many relationship
    messages: List["Message"] = Relationship(back_populates="conversation")

class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    role: str # "user" or "ai"

    # The foreign key linking back to the Conversation
    conversation_id: Optional[int] = Field(default=None, foreign_key="conversation.id")
    conversation: Optional[Conversation] = Relationship(back_populates="messages")
```

#### **Migration Strategy**

For v0.1.0, migrations will be handled manually. The database will be created from the SQLModel metadata on the first application startup. Given the simplicity of the initial schema and the use of SQLite, formal migration tools like Alembic are not required at this stage.

---

### **4. Integration Architecture**

#### **External API Integration (Google Gemini)**

- **Pattern**: The `google-generativeai` SDK will be used for all interactions with the Gemini API. A single, reusable client instance will be configured.
- **Authentication**: The user-provided `api_key` from the `ChatRequest` will be used to configure the Gemini client for each request. This ensures user data privacy and cost isolation.
- **Streaming**: The `model.generate_content(..., stream=True)` method from the SDK will be used. The FastAPI backend will iterate over this stream and `yield` each chunk as a Server-Sent Event.

_Example Gemini Client Initialization:_

````python
import google.generativeai as genai

# This will be done inside the chat request endpoint
# using the key provided by the user.
genai.configure(api_key=user_provided_api_key)
model = genai.GenerativeModel('gemini-pro') # Or 'gemini-flash'```

#### **Configuration Management**

*   **Method**: The `python-dotenv` library will be used to manage local configuration.
*   **`.env` file**: A `.env` file will be created in the project root to store non-sensitive development configurations. It should be added to `.gitignore`. For this project, it's primarily a placeholder, as the sensitive Google API key is provided per-request by the user.

`.env` example:
````

# .env

# Application settings

APP_TITLE="Gemini Fusion"

````

---

### **5. Development Environment Setup**

A standardized and simple development environment is crucial for getting started quickly.

*   **Local Development Requirements**:
    *   Python 3.9+
    *   A virtual environment tool (e.g., `venv`)

*   **Setup Steps**:
    1.  Clone the repository.
    2.  Create and activate a virtual environment:
        ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows: venv\Scripts\activate
        ```
    3.  Install dependencies from a `requirements.txt` file:
        ```bash
        pip install -r requirements.txt
        ```
    4.  Create a `.env` file in the root of the project.

*   **`requirements.txt` file content**:
    ```
    fastapi
    uvicorn[standard]
    sqlmodel
    jinja2
    python-dotenv
    google-generativeai
    sse-starlette
    ```

*   **Running the Development Server**:
    The application will be launched using Uvicorn from the terminal root. The `--reload` flag will be used to automatically restart the server on code changes.
    ```bash
    uvicorn main:app --reload
    ```
    *(Assuming the main FastAPI app instance is named `app` in a file named `main.py`)*

*   **Testing Framework Selections**:
    *   **Backend Unit/Integration Tests**: **Pytest** with `fastapi.testclient.TestClient`.
    *   **End-to-End (E2E) Tests**: **Playwright** is recommended for testing the full application stack, including HTMX-driven frontend interactions.
````
