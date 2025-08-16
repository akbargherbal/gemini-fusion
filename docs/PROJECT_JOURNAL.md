# Project Journal: Gemini Fusion

This document serves as a living log of key technical decisions, architectural patterns, and solutions that emerge during the development of Gemini Fusion. Its purpose is to capture the "why" behind our choices, especially for issues not explicitly covered in the initial planning documents.

---

### **Entry 1: E2E Test Failure Diagnostics**

-   **Date:** 2025-08-16
-   **Topic:** Standardizing Diagnostic Artifacts for E2E Test Failures

#### **Context**

During Session 4, we encountered a persistent and difficult-to-diagnose E2E test failure (`test_single_message_sends_only_one_request`). The test browser would often see a "blank page," indicating a race condition with the Alpine.js framework, but we had no visual evidence to confirm this, leading to a frustrating "guess-and-fix" cycle.

#### **Decision**

We have implemented a standardized, automated process for capturing diagnostic information whenever an E2E test fails:

1.  A new, unique directory will be created for each test run within `logs/e2e_runs/`, named with a timestamp (e.g., `20250816_143000/`).
2.  If any test within that run fails, the following artifacts will be automatically saved into that specific directory:
    -   `failure_screenshot.png`: A screenshot of the browser at the exact moment of failure.
    -   `failure_dom.html`: A complete snapshot of the page's HTML at that moment.
3.  The console output will clearly state the path to the directory containing these artifacts.

#### **Rationale**

This approach moves us from speculation to evidence-based debugging. It provides invaluable, concrete data about the state of the application when a test fails, which will drastically reduce the time required to diagnose and fix frontend and E2E-related issues in the future. This process is now our standard operating procedure for handling such failures.