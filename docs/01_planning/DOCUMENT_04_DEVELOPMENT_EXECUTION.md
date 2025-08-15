# **Revised** Development Execution Plan: Gemini Fusion v0.1.0

This plan outlines the milestones, workflows, and validation criteria required to successfully develop Gemini Fusion from a static mockup to a feature-complete v0.1.0 MVP. It has been updated to reflect feedback on timeline flexibility and error handling.

---

### **1. Milestone Structure**

We will adopt a structure of three distinct, sequential milestones. This approach prioritizes achieving a high-quality, stable outcome for each major block of functionality over adhering to a rigid, time-boxed schedule. While each milestone is estimated to take approximately one week, **Milestone 2 is recognized as the most complex and may require additional time.**

| Milestone       | Title                              | Estimated Duration | Primary Goal                                                                                                                                            |
| :-------------- | :--------------------------------- | :----------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Milestone 1** | Backend Foundation & Connectivity  | ~1 Week            | Establish a functional FastAPI backend with a connected database and a basic, non-streaming API endpoint.                                               |
| **Milestone 2** | The Core Chat Loop                 | ~1-2 Weeks         | Implement the end-to-end user journey of sending a message and receiving a streamed response from the live Gemini API, including conversation creation. |
| **Milestone 3** | State Management & UI Finalization | ~1 Week            | Build out conversation history management and integrate all remaining "Should Have" UI features, including robust error handling.                       |

**Milestone Validation Criteria:**

- **End of Milestone 1:** A developer can use an API client to send a JSON payload to a local `/api/chat/sync` endpoint and verify a new message is saved in the `gemini_fusion.db` file. The `GET /api/conversations` endpoint returns a list of conversation topics.
- **End of Milestone 2:** From the web UI, a user can enter a valid API key, type a message, press send, and see a streamed response from the Gemini API appear in the chat window. A new conversation with a generated topic is created and saved to the database.
- **End of Milestone 3 (MVP Complete):** The application meets all success criteria outlined in the `MVP Feature Prioritization Matrix`. A user can refresh the app, see their past chats, click to load them, and the experience is responsive and polished. The UI provides feedback for key error states.

**Progress Tracking:** A Kanban board (e.g., Trello, GitHub Projects) with columns for `To Do`, `In Progress`, and `Done` will be used. Each task in the "Implementation Sequence" below represents a card.

---

### **2. Development Workflow**

**Code Organization (Scalable Structure):**
The project will immediately adopt a scalable structure for maintainability:

````
/
|-- .env, .gitignore, main.py, requirements.txt
|-- db/
|   |-- database.py, models.py
|-- routers/
|   |-- chat.py, conversations.py
|-- schemas/
|   |-- chat.py
|-- services/
|   |-- gemini_service.py
|-- templates/
|   |-- index.html```

**Git Workflow (GitFlow-Lite):**
1.  `main`: Stable production-ready branch.
2.  `develop`: Primary integration branch. All feature branches merge into `develop`.
3.  `feature/<feature-name>`: Scoped branches for new work (e.g., `feature/sse-streaming`).
4.  **Pull Requests (PRs):** All merges into `develop` must go through a PR with a code review.
5.  **Release:** `develop` is merged into `main` and tagged `v0.1.0` upon completion of Milestone 3.

**Code Review & Quality Gates:**
*   Every PR into `develop` requires a review.
*   **Checklist:** Does it work? Does it follow the code structure? Are there unit tests? Does it handle errors gracefully?

---

### **3. Implementation Sequence**

This is a detailed breakdown of tasks for each milestone.

#### **Milestone 1: Backend Foundation & Connectivity**
*Goal: Prove the stack works together before adding external API complexity.*

1.  **Environment & Project Setup:** Initialize the virtual environment, install dependencies, and create the scalable directory structure.
2.  **Define Database Models:** Create `Conversation` and `Message` SQLModel classes in `db/models.py`.
3.  **Implement Database Logic:** Write functions in `db/database.py` to create the SQLite engine and initialize tables on startup.
4.  **Define Pydantic Schemas:** Create `ChatRequest`, `ConversationRead`, and `MessageRead` in `schemas/chat.py`.
5.  **Build Conversation Endpoints:** Implement `GET /api/conversations` and `GET /api/conversations/{conversation_id}`.
6.  **Build a Synchronous Chat Endpoint:** Implement a temporary `POST /api/chat/sync` to accept a message, save it, and return a hardcoded JSON response.
7.  **Integration Checkpoint:** Test all endpoints with an API client to verify database interaction.

#### **Milestone 2: The Core Chat Loop**
*Goal: Achieve the primary user journey. This is the most critical and complex milestone.*

1.  **Gemini Service Module:** Create a function in `services/gemini_service.py` that takes a message and API key, initializes the `google-generativeai` client, and `yield`s each chunk from the `model.generate_content(..., stream=True)` method.
2.  **Implement SSE Streaming Endpoint:** In `routers/chat.py`, create the `POST /api/chat/stream` endpoint using `EventSourceResponse` to call the Gemini service and stream its response.
3.  **Frontend HTMX Integration:** Wire up the message form to the SSE endpoint using `htmx` attributes and write the client-side logic to render the streamed response.
4.  **Implement Conversation Creation Logic:**
    *   **Sub-task:** When saving the first message of a new chat, the conversation `topic` must be generated. **Rule:** The `topic` will be populated using the first 50 characters of the user's initial message.
    *   After the stream from the Gemini API is complete, assemble the full response in the backend and save it as a new `Message` in the database, linked to the correct conversation.
5.  **Risk Mitigation:** Test the Gemini service function independently before full integration.

#### **Milestone 3: State Management & UI Finalization**
*Goal: Implement the "Should Have" features to create a complete and polished application.*

1.  **Conversation History UI:** Use HTMX to call the `GET /api/conversations` endpoint to populate the left sidebar, and make each item clickable to load history via `GET /api/conversations/{id}`.
2.  **Model Selection Integration:** Update the `ChatRequest` schema and backend logic to accept the selected model from the frontend and use it when calling the Gemini API.
3.  **Backend Error Handling:** Wrap Gemini SDK calls in a `try...except` block to catch errors (e.g., invalid API key) and raise an appropriate `HTTPException` (e.g., 401 Unauthorized).
4.  **Implement Frontend Error Handling for Stream Failures:**
    *   **New Task:** Enhance the frontend to provide feedback if an error occurs during an active chat stream.
    *   **Behavior:** If the SSE connection closes unexpectedly or sends an error event, display a browser `alert()` with a message like "The connection to the AI was lost. Please try again."
5.  **Final Polish & Verification:** Verify all UI functionality from the mockup (auto-expanding input, theme switching) and perform a full manual test against the MVP Success Criteria.

---

### **4. Testing Strategy**

*   **Unit Testing (Pytest):** Focus on business logic in `services/`, mocking external calls.
*   **Integration Testing (Pytest + `TestClient`):** Focus on API endpoints, verifying status codes and response schemas for both success and error conditions.
*   **Manual End-to-End Testing Checklist:** A comprehensive checklist will be used to validate the final MVP, including all new error-handling functionality.

---

### **5. Deployment Pipeline (Basics for Future)**

*   **Flow:** `Local Dev` -> `Git PR` -> `Merge to develop` -> `Merge to main` -> `Deploy from main`.
*   **Configuration:** Sensitive keys are handled per-request. A `Dockerfile` will be created for simple, containerized deployment.

---

### **6. Progress Validation**

*   **Definition of "Done":** Code is implemented, tested, reviewed, and merged into `develop`.
*   **Technical Debt:** Known shortcuts (manual DB migrations) will be documented as issues for post-MVP consideration.
*   **Course Correction:** If a milestone's primary goal is not met, the next block of work will not begin. The priority is to ensure the stability of each milestone before proceeding.
````
