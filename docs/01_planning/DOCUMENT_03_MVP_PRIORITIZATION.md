### **Revised MVP Feature Prioritization Matrix: Gemini Fusion v0.1.0**

**Context:** This document outlines the development priorities for creating a functional Minimum Viable Product (MVP) of Gemini Fusion. It translates the comprehensive feature set into an actionable roadmap, balancing the core user value against implementation complexity to ensure rapid, focused development toward version 0.1.0.

---

#### **Feature Priority Classification**

The features identified from the project documentation are classified into four tiers. The goal of this MVP is to deliver a complete "Must Have" and "Should Have" experience.

##### **Tier 1: Must Have (MVP Core)**

_These features represent the absolute minimum required for the application to be functional and fulfill its core promise: a private chat interface to Gemini models._

| Feature Name                             | Implementation Complexity | Rationale                                                                                                                                                                                                                                     |
| :--------------------------------------- | :------------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Backend Scaffolding (FastAPI)**        | Medium                    | The foundational server environment. All other backend features depend on this.                                                                                                                                                               |
| **Database Setup (SQLite + SQLModel)**   | Medium                    | Essential for persisting data. Required for conversation history and message storage. Choosing SQLite minimizes setup friction.                                                                                                               |
| **Core Database Models**                 | Simple                    | Defining `Conversation` and `Message` models in SQLModel is a prerequisite for any database interaction.                                                                                                                                      |
| **API Key Management (State & Input)**   | Simple                    | The core mechanism for user authentication with the Gemini API. The app is unusable without it.                                                                                                                                               |
| **Send Message & Stream Response (SSE)** | **Complex**               | **This is the primary user journey.** It involves the full loop: frontend (HTMX) -> backend (FastAPI) -> external API (Gemini) -> backend (SSE stream) -> frontend update. It also includes saving both user and AI messages to the database. |
| **Basic Chat UI**                        | Simple                    | The static HTML/CSS for displaying user and AI messages. This is largely complete in the mockup.                                                                                                                                              |

##### **Tier 2: Should Have (MVP Enhanced)**

_These features are critical for delivering a good user experience and differentiating the product. They are key to the app's identity as described in the summary._

| Feature Name                          | Implementation Complexity | Rationale                                                                                                                                                                                |
| :------------------------------------ | :------------------------ | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Conversation History Management**   | Medium                    | Includes API endpoints (`GET /conversations`, `GET /conversations/{id}`) and the HTMX to render the chat list and load selected chats. This makes the app stateful and useful over time. |
| **Select Chat Model (Pro vs. Flash)** | Medium                    | A key feature from the app summary. Involves passing the model choice to the backend to use the correct Gemini model.                                                                    |
| **Dynamic Theme Switching**           | Simple                    | Tightly coupled with Model Selection. This visual feedback is a core part of the app's branding and user experience.                                                                     |
| **Auto-Expanding Message Input**      | Simple                    | A significant UX improvement that is already implemented in the mockup's JS. It should be verified.                                                                                      |
| **Error Handling (Invalid API Key)**  | Medium                    | Crucial for user feedback. The backend must validate the key with the Gemini API and return a clear error (`401 Unauthorized`) to the frontend.                                          |

##### **Tier 3: Could Have (Post-MVP / Polish)**

_Nice-to-have features that improve the experience but are not essential for the core functionality. They can be added in a fast-follow release._

| Feature Name                      | Implementation Complexity | Rationale                                                                                                                            |
| :-------------------------------- | :------------------------ | :----------------------------------------------------------------------------------------------------------------------------------- |
| **Zen Mode**                      | Simple                    | A purely cosmetic UI state change that can be implemented entirely on the frontend with AlpineJS. Adds polish but not core function. |
| **User Preference Persistence**   | Medium                    | Saving settings like the selected model or Zen Mode to the database. The app functions without this, using defaults on each visit.   |
| **Toggle API Key Visibility**     | Simple                    | A minor UX enhancement for the settings panel. It's helpful but not critical.                                                        |
| **New Chat Button Functionality** | Simple                    | Should clear the current chat view and prepare for a new conversation. Simple, but secondary to viewing existing chats.              |
| **Developer Console Logging**     | Simple                    | Already in the mockup for debugging; can be formalized or removed as needed.                                                         |

##### **Tier 4: Won't Have (Out of Scope for v0.1.0)**

_Features explicitly deferred to maintain focus and reduce the scope of the MVP._

| Feature Name                             | Implementation Complexity | Rationale                                                                                                                                   |
| :--------------------------------------- | :------------------------ | :------------------------------------------------------------------------------------------------------------------------------------------ |
| **User Authentication (Logout)**         | Complex                   | The `strategic_blueprint_plan.md` explicitly defers user accounts. The "Logout" button is therefore non-functional for the MVP.             |
| **Full End-to-End Testing (Playwright)** | Complex                   | While Pytest for the backend is advisable, a full E2E test suite is a significant effort best reserved for post-MVP stabilization.          |
| **Formal DB Migrations (Alembic)**       | Medium                    | As per the `Technical Foundation Specification`, migrations will be handled manually for v0.1.0 due to the simple schema and use of SQLite. |

---

#### **Dependency Mapping & Development Sequence**

Development must follow a logical progression, building foundational layers before adding dependent features.

1.  **Milestone 1: Backend Foundation (Must Have)**

    - **Goal:** Create a non-streaming, "echo" API.
    - **Tasks:**
      - Setup FastAPI project with Uvicorn.
      - Define Pydantic/SQLModel schemas (`ChatRequest`, `Conversation`, `Message`).
      - Initialize SQLite database and create tables on startup.
      - Create a `POST /api/chat/sync` endpoint that takes a message, saves it to the DB, and returns a static JSON response.
      - Create `GET /api/conversations` to prove the DB connection works.
    - **Outcome:** A running server with a connected database.

2.  **Milestone 2: Core Chat Loop (Must Have -> Should Have)**

    - **Goal:** Enable real-time chat and history.
    - **Tasks:**
      - Implement the **`POST /api/chat/stream`** endpoint, integrating the `google-generativeai` SDK.
      - Implement the Server-Sent Events (SSE) logic to stream the response.
      - Connect the frontend `textarea` and send button using HTMX to call the stream endpoint.
      - Wire up the frontend to receive SSE messages and display the AI response.
      - Implement the logic to save the AI's full response to the database upon completion.
    - **Outcome:** A user can type a message, press send, and see a streamed response from the live Gemini API.

3.  **Milestone 3: UI Enhancement & State (Should Have -> Could Have)**
    - **Goal:** Build out the full application feel.
    - **Tasks:**
      - Implement the "Select Chat Model" feature, passing the choice to the backend.
      - Implement the "Conversation History" UI, using HTMX to fetch and display conversations from the backend.
      - Verify all theme-switching and responsive behaviors from the mockup are functional with the dynamic data.
      - Implement robust backend error handling for API keys.
    - **Outcome:** The application is feature-complete for an enhanced MVP.

---

#### **MVP Success Criteria**

To be considered a successful v0.1.0 MVP, the application must meet the following criteria:

- **Core User Journey:** A user can open the application, enter their Google API key, send a message, and receive a complete, streamed response from the selected Gemini model (Pro or Flash).
- **Persistence:** The user can refresh the page and see their previous conversation in the left sidebar. They can click on it to reload the entire chat history.
- **Usability:** The UI must be responsive and function correctly on both desktop and mobile viewports. All "Must Have" and "Should Have" features must be bug-free.
- **Quality Threshold:**
  - **Must Have Features:** Zero critical bugs. The core chat loop must be reliable.
  - **Should Have Features:** Minor cosmetic bugs are acceptable, but functionality must be intact.
- **Validation:** Success is validated when a new user can successfully complete the Core User Journey without any instructions beyond what is presented in the UI.
