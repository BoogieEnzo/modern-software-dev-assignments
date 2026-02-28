"""Frontend E2E tests for critical UI paths."""

from __future__ import annotations

import json
import subprocess
import time
from typing import Generator

import httpx
import pytest
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright


BASE_URL = "http://127.0.0.1:8015"


@pytest.fixture(scope="module")
def app_server() -> Generator[str, None, None]:
    """Start a local uvicorn server for browser tests."""
    proc = subprocess.Popen(
        [".venv/bin/python", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8015"],
        cwd="/home/fengde/Projects/modern-software-dev-assignments/week8",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                resp = httpx.get(f"{BASE_URL}/", timeout=1.0, trust_env=False)
                if resp.status_code in (200, 304):
                    break
            except Exception:
                pass
            time.sleep(0.3)
        else:
            raise RuntimeError("E2E server did not start in time")
        yield BASE_URL
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture(scope="module")
def browser() -> Generator[Browser, None, None]:
    """Launch a headless browser once for this module."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser: Browser) -> Generator[Page, None, None]:
    """Create a fresh browser context/page per test."""
    context: BrowserContext = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


def _json_fulfill(route, payload: object, status: int = 200) -> None:
    route.fulfill(
        status=status,
        headers={"Content-Type": "application/json"},
        body=json.dumps(payload),
    )


def test_load_papers_table_renders_rows(page: Page, app_server: str) -> None:
    page.route("**/api/papers/", lambda route: _json_fulfill(route, [{
        "id": 1,
        "title": "Operating Systems Paper",
        "authors": "Alice, Bob",
        "abstract": "A paper about kernels",
        "arxiv_id": None,
        "pdf_path": "/tmp/os-paper.pdf",
        "summary": None,
        "github_repo": None,
        "year": 2024,
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
        "is_favorite": False,
    }]))
    page.goto(app_server)
    page.click('[data-tab="papers"]')
    row = page.locator(".papers-table tbody tr").first
    row.wait_for()
    assert "Operating Systems Paper" in row.inner_text()
    assert "2024" in row.inner_text()


def test_clicking_paper_row_opens_pdf_new_tab(page: Page, app_server: str) -> None:
    page.route("**/api/papers/", lambda route: _json_fulfill(route, [{
        "id": 2,
        "title": "Click Opens PDF",
        "authors": "Carol",
        "abstract": "Test",
        "arxiv_id": None,
        "pdf_path": "/tmp/click-test.pdf",
        "summary": None,
        "github_repo": None,
        "year": 2025,
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
        "is_favorite": False,
    }]))
    page.goto(app_server)
    page.click('[data-tab="papers"]')
    with page.context.expect_page() as popup_info:
        page.click(".papers-table tbody tr")
    popup = popup_info.value
    popup.wait_for_load_state()
    assert popup.url.endswith("/papers/click-test.pdf")


def test_search_download_and_switch_to_papers_tab(page: Page, app_server: str) -> None:
    page.route("**/api/papers/", lambda route: _json_fulfill(route, []))
    page.route("**/api/search/**", lambda route: _json_fulfill(route, [{
        "title": "ArXiv Result",
        "authors": "Dana",
        "abstract": "Search result abstract",
        "arxiv_id": "2401.12345",
        "published": "2024-01-15",
    }]))
    page.route("**/api/papers/download", lambda route: _json_fulfill(route, {"id": 9, "title": "ArXiv Result"}))
    page.on("dialog", lambda dialog: dialog.accept())

    page.goto(app_server)
    page.fill("#arxiv-search-input", "distributed systems")
    page.click("#arxiv-search-btn")

    results_row = page.locator("#search-results .papers-table tbody tr").first
    results_row.wait_for()
    assert "2024" in results_row.inner_text()

    page.click("#search-results .btn-download")
    papers_tab = page.locator('[data-tab="papers"]')
    tab_class = papers_tab.get_attribute("class") or ""
    assert "active" in tab_class


def test_station_chat_displays_error_message(page: Page, app_server: str) -> None:
    page.route("**/api/papers/", lambda route: _json_fulfill(route, []))
    page.route(
        "**/api/chat",
        lambda route: _json_fulfill(
            route,
            {"detail": "Ollama is not running. Please start Ollama to enable chat."},
            status=503,
        ),
    )

    page.goto(app_server)
    page.click('[data-tab="papers"]')
    page.fill("#station-chat-input", "hello")
    page.click("#station-chat-send")

    messages = page.locator("#station-chat-messages")
    messages.locator(".msg-assistant").last.wait_for()
    assert "Ollama is not running" in messages.inner_text()
