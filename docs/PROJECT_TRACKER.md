# Gemini Fusion - Project Tracker v0.1.0

**Last Updated:** 2025-08-14 (Session 0)

### **1. Governance and Change Control**

This document serves as the single source of truth for tracking the implementation progress of the Gemini Fusion MVP. Its structure and tasks are directly derived from the planning and specification documents (`DOCUMENT_01` through `DOCUMENT_05`).

**Change Protocol:** The original planning documents are considered the project's constitution. Should a situation arise where a task in this tracker cannot be completed as planned, or a fundamental assumption is proven incorrect, the following protocol will be initiated:

1.  **Proposal:** The AI Assistant will explicitly flag the issue and propose a change to the core plan.
2.  **Impact Analysis:** The AI Assistant will identify which of the foundational documents (`DOCUMENT_01` to `DOCUMENT_04`) are impacted by the proposed change.
3.  **Approval:** The User (Lead Developer) must approve the change before any implementation proceeds.
4.  **Documentation Update:** Upon approval, the AI Assistant will first provide the updated text for the relevant foundational document(s).
5.  **Tracker Update:** Only after the foundational documents are amended will this Project Tracker be updated to reflect the new plan.

This ensures that our project's "law" and its "enforcement" remain in perfect alignment at all times.

---

### **2. High-Level Status**

- **Overall Progress:** 0%
- **Current Milestone:** Milestone 1: Backend Foundation & Connectivity
- **Session Goal:** Project setup, planning review, and establishing our workflow.
- **Focus for Next Session:** Begin Milestone 1 by creating the `tests/` directory and then defining the database models.

---

### **3. Milestone Checklist**

#### **Milestone 1: Backend Foundation & Connectivity (`In Progress`)**

- **Goal:** Establish a functional FastAPI backend with a connected database and basic, non-streaming API endpoints.
- **Tasks:**
  - [>] **Environment & Project Setup:** Create the `tests/` directory and update `.gitignore`.
  - [ ] **Define Database Models:** Create `Conversation` and `Message` SQLModel classes in `db/models.py`.
  - [ ] **Implement Database Logic:** Write functions in `db/database.py` to create the SQLite engine and initialize tables on startup.
  - [ ] **Test Database Models:** Write a `Pytest` file to verify model creation and session commits.
  - [ ] **Define Pydantic Schemas:** Create `ChatRequest`, `ConversationRead`, and `MessageRead` in `schemas/chat.py`.
  - [ ] **Build Conversation Endpoints:** Implement `GET /api/conversations` and `GET /api/conversations/{conversation_id}`.
  - [ ] **Build a Synchronous Chat Endpoint:** Implement `POST /api/chat/sync` as a temporary test endpoint.
  - [ ] **Integration Test for Endpoints:** Test all endpoints with `TestClient` to verify database interaction.

#### **Milestone 2: The Core Chat Loop (`To Do`)**

- **Goal:** Implement the end-to-end user journey of sending a message and receiving a streamed response from the live Gemini API.
- **Tasks:**
  - [ ] **Gemini Service Module:** Create a testable service in `services/gemini_service.py` that streams responses from the Google API.
  - [ ] **Unit Test Gemini Service:** Write a `Pytest` unit test for the service, mocking the external API call.
  - [ ] **Implement SSE Streaming Endpoint:** In `routers/chat.py`, create the `POST /api/chat/stream` endpoint using `EventSourceResponse`.
  - [ ] **Frontend HTMX Integration:** Wire up the message form to the SSE endpoint to render the streamed response.
  - [ ] **Implement Conversation Creation Logic:** Generate a topic from the first user message.
  - [ ] **Implement Message Persistence:** Save the user message and the full AI response to the database after the stream completes.
  - [ ] **Integration Test for Core Loop:** Write a test to verify the entire chat and persistence flow.

#### **Milestone 3: State Management & UI Finalization (`To Do`)**

- **Goal:** Build out conversation history management and integrate all remaining "Should Have" UI features.
- **Tasks:**
  - [ ] **Conversation History UI:** Use HTMX to populate and load conversations from the backend.
  - [ ] **Model Selection Integration:** Pass the selected model (`pro` vs. `flash`) to the backend.
  - [ ] **Backend Error Handling:** Implement `try...except` blocks for Gemini API calls and return proper `HTTPException`s.
  - [ ] **Frontend Error Handling:** Add frontend logic to display an `alert()` on stream failures.
  - [ ] **Final Polish & Verification:** Conduct a full manual test against the MVP Success Criteria.
