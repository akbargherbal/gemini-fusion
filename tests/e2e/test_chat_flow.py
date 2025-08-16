import pytest
from playwright.sync_api import Page, expect
import re
import os
from datetime import datetime

# Define the base URL of your running application
BASE_URL = "http://127.0.0.1:8000"


def test_single_message_sends_only_one_request(page: Page, test_run_dir: str):
    """
    This test verifies the core user journey and explicitly checks for the double-submission bug.
    It now saves failure artifacts to a unique, timestamped directory.
    """
    try:
        # 1. Navigate to the application
        page.goto(BASE_URL)

        # --- MODIFIED ---
        # Objective: Wait for a reliable signal that Alpine.js has initialized.
        # The gear icon's container div has `x-show` and is initially hidden.
        # Waiting for it to be visible is a reliable indicator that the UI is ready.
        gear_icon_container = page.locator("div.fixed.z-50.top-4.right-4")
        expect(gear_icon_container).to_be_visible(timeout=10000)
        # --- END MODIFICATION ---

        # 2. Configure the API Key
        # Now that we know the container is visible, we can safely locate the button within it.
        settings_button = gear_icon_container.locator('button[title="Toggle Settings"]')
        api_key_input = page.locator('input[placeholder*="Enter your Gemini API key"]')

        settings_button.click()
        expect(api_key_input).to_be_visible()
        api_key_input.fill("FAKE_API_KEY")

        page.locator('button[title="Close settings"]').click()

        # 3. Prepare to listen for network requests
        request_count = 0

        def count_request(route):
            nonlocal request_count
            request = route.request
            if "/api/chat/stream" in request.url and request.method == "POST":
                print(f"Intercepted POST request to {request.url}")
                request_count += 1

            headers = {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
            }
            route.fulfill(status=200, headers=headers, body="data: [DONE]\n\n")

        page.route("**/api/chat/stream", count_request)

        # 4. Send a message
        message_input = page.locator('textarea[placeholder*="Message Gemini Fusion"]')
        send_button = page.locator('button[title="Send message"]')

        message_input.fill("Hello, World!")
        send_button.click()

        # 5. Assertions
        user_message = page.locator("#chat-container").get_by_text(
            re.compile(r"Hello, World!")
        )
        expect(user_message).to_be_visible()

        ai_placeholder = page.locator('[id^="ai-msg-"]')
        expect(ai_placeholder).to_be_visible()

        print(f"Final request count: {request_count}")
        assert (
            request_count == 1
        ), f"Expected 1 network request, but found {request_count}!"

    except Exception as e:
        # On any failure, capture the state into the unique test_run_dir
        screenshot_path = os.path.join(test_run_dir, "failure_screenshot.png")
        html_path = os.path.join(test_run_dir, "failure_dom.html")

        page.screenshot(path=screenshot_path)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(page.content())

        print(f"\n--- E2E TEST FAILED ---")
        print(f"Failure artifacts saved to: {test_run_dir}")
        # Re-raise the exception to ensure the test is still marked as failed
        raise e
