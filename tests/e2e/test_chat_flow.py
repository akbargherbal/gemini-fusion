# tests/e2e/test_chat_flow.py
import pytest
from playwright.sync_api import Page, expect, Route
import re
import os
import json

# Define the base URL of your running application
BASE_URL = "http://127.0.0.1:8000"


def test_chat_flow_with_two_phase_sse(page: Page, test_run_dir: str):
    """
    This test verifies the new two-phase chat flow.
    1. It intercepts the POST /initiate call and lets it proceed.
    2. It intercepts the GET /stream call and provides a mock SSE response.
    """
    try:
        # --- 1. Navigate and wait for UI to be ready ---
        page.goto(BASE_URL)
        gear_icon_container = page.locator("div.fixed.z-50.top-4.right-4")
        expect(gear_icon_container).to_be_visible(timeout=10000)

        # --- 2. Configure the API Key ---
        settings_button = gear_icon_container.locator('button[title="Toggle Settings"]')
        api_key_input = page.locator('input[placeholder*="Enter your Gemini API key"]')
        settings_button.click()
        expect(api_key_input).to_be_visible()
        api_key_input.fill("FAKE_API_KEY")
        page.locator('button[title="Close settings"]').click()

        # --- 3. Set up network interception for the two-phase flow ---
        session_id_container = {"id": None}

        def handle_initiate(route: Route):
            """Let the initiate request go through to the server but capture the response."""
            response = route.fetch()
            body = response.json()
            session_id_container["id"] = body.get("session_id")
            print(
                f"Intercepted /initiate. Captured session_id: {session_id_container['id']}"
            )
            route.fulfill(response=response)

        def handle_stream(route: Route):
            """Intercept the stream request and fulfill with a mock SSE stream."""
            session_id = session_id_container["id"]
            if session_id and f"/api/chat/stream/{session_id}" in route.request.url:
                print(
                    f"Intercepted /stream for session_id: {session_id}. Fulfilling with mock data."
                )
                headers = {
                    "Content-Type": "text/event-stream",
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
                # --- CORRECTED THIS BLOCK ---
                # The frontend listens for the default 'message' event, which has no 'event:' line.
                # We also need to send the custom events the frontend now listens for.
                body = (
                    "event: stream_start\ndata: \n\n"
                    "data: Mocked AI response.\n\n"  # This is a default message event
                    "event: stream_complete\ndata: [DONE]\n\n"
                )
                # --- END CORRECTION ---
                route.fulfill(status=200, headers=headers, body=body)
            else:
                route.continue_()

        page.route("**/api/chat/initiate", handle_initiate)
        page.route("**/api/chat/stream/*", handle_stream)

        # --- 4. Send a message ---
        message_input = page.locator('textarea[placeholder*="Message Gemini Fusion"]')
        send_button = page.locator('button[title="Send message"]')

        message_input.fill("Hello, test!")
        send_button.click()

        # --- 5. Assertions ---
        user_message = page.locator("#chat-container").get_by_text("Hello, test!")
        expect(user_message).to_be_visible()

        ai_message_container = page.locator('[id^="ai-msg-"]')
        expect(ai_message_container).to_be_visible()

        expect(ai_message_container).to_contain_text(
            "Mocked AI response.", timeout=5000
        )

        expect(ai_message_container.locator(".blinking-cursor")).not_to_be_visible()

    except Exception as e:
        screenshot_path = os.path.join(test_run_dir, "failure_screenshot.png")
        html_path = os.path.join(test_run_dir, "failure_dom.html")
        page.screenshot(path=screenshot_path)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(page.content())
        print(f"\n--- E2E TEST FAILED ---")
        print(f"Failure artifacts saved to: {test_run_dir}")
        raise e
