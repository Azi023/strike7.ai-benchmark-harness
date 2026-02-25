"""
Strike7 Dashboard - Remote UI Smoke Test (WSL-optimized)

Validates basic start/stop flow via the UI against the remote VPS.

Run:
  python -m pytest dashboard/tests/test_e2e_smoke_remote.py -v
"""

import re
import time
import pytest
from playwright.sync_api import Page, expect, sync_playwright

BASE_URL = "http://139.59.80.137:5500"


def _launch_page():
    """Launch a Chromium page with WSL-friendly flags."""
    p = sync_playwright().start()
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--disable-extensions",
        ],
    )
    context = browser.new_context(viewport={"width": 1440, "height": 900}, ignore_https_errors=True)
    page = context.new_page()
    return p, browser, page


def _close(p, browser):
    try:
        browser.close()
    finally:
        p.stop()


def test_remote_ui_start_stop_smoke():
    """Load dashboard, start first benchmark, observe running, then stop and verify."""
    p, browser, page = _launch_page()
    try:
        # Load dashboard
        page.goto(BASE_URL, wait_until="domcontentloaded")

        # Basic load assertions
        expect(page).to_have_title(re.compile(r"Strike7|Dashboard", re.IGNORECASE))
        page.wait_for_selector(".benchmark-card, [class*='benchmark-card']", timeout=15000)

        # Click first visible Start button
        start_btn = page.locator("button, [class*='btn']").filter(has_text=re.compile(r"start", re.IGNORECASE)).first
        start_btn.click()

        # Wait for running indicators (stop button, running-info, access URL)
        page.wait_for_selector(
            ".running-info, :text('localhost:'), button:has-text('Stop'), [class*='status']",
            timeout=45000,
        )

        # Try to stop if stop button is present
        stop_btn = page.locator("button").filter(has_text=re.compile(r"stop", re.IGNORECASE)).first
        if stop_btn.count() > 0 and stop_btn.is_visible():
            stop_btn.click()
            page.wait_for_timeout(3000)

        # Start button should reappear
        expect(page.locator("button").filter(has_text=re.compile(r"start", re.IGNORECASE)).first).to_be_visible()
    finally:
        _close(p, browser)

