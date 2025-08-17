# tests/e2e/test_chat_flow.py
import pytest
from playwright.sync_api import Page, expect, Route
import os

BASE_URL = "http://127.0.0.1:8000"

def test_chat_flow_with_two_phase_sse(page: Page, test_run_dir: str):
    try:
        page.goto(BASE_URL)
        expect(page.locator('button[title="Toggle Settings"]')).to_be_visible(timeout=10000)
        page.locator('button[title="Toggle Settings"]').click()
        page.locator('input[placeholder*="Enter your Gemini API key"]').fill("FAKE_API_KEY")
        page.locator('button[title="Close settings"]').click()

        session_id_container = {"id": None}
        def handle_initiate(route: Route):
            response = route.fetch()
            body = response.json()
            session_id_container["id"] = body.get("session_id")
            route.fulfill(response=response)

        def handle_stream(route: Route):
            body = (
                "event: stream_start\ndata: \n\n"
                "data: Mocked AI response.\n\n"
                "event: stream_complete\ndata: [DONE]\n\n"
            )
            route.fulfill(status=200, headers={"Content-Type": "text/event-stream"}, body=body)

        page.route("**/api/chat/initiate", handle_initiate)
        page.route("**/api/chat/stream/*", handle_stream)

        page.locator('textarea[placeholder*="Message Gemini Fusion"]').fill("Hello, test!")
        page.locator('button[title="Send message"]').click()

        expect(page.locator("#chat-container").get_by_text("Hello, test!")).to_be_visible()
        expect(page.locator('[id^="ai-msg-"]')).to_contain_text("Mocked AI response.", timeout=5000)
    except Exception as e:
        screenshot_path = os.path.join(test_run_dir, "failure_screenshot.png")
        page.screenshot(path=screenshot_path)
        raise e