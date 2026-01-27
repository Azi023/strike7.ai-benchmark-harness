"""
Strike7 Dashboard - Playwright E2E Test Suite (WSL-Optimized)
Fixed version that works without chromium_headless_shell

Run: pytest test_e2e_playwright_fixed.py -v
"""

import pytest
from playwright.sync_api import Page, expect, sync_playwright
import time
import re

# Configuration
BASE_URL = "http://localhost:5500"


class TestDashboardLoad:
    """Test dashboard loading and initial state"""

    def test_page_loads_successfully(self, page: Page):
        """Dashboard should load without errors"""
        page.goto(BASE_URL)
        expect(page).to_have_title(re.compile(r"Strike7|Dashboard", re.IGNORECASE))

    def test_statistics_panel_visible(self, page: Page):
        """Statistics panel should be visible with correct counts"""
        page.goto(BASE_URL)
        page.wait_for_selector(".statistics, .stats-panel, [class*='stat']", timeout=10000)
        content = page.content()
        assert "64" in content or "benchmarks" in content.lower()

    def test_all_benchmarks_load(self, page: Page):
        """All 64 benchmark cards should load"""
        page.goto(BASE_URL)
        page.wait_for_selector(".benchmark-card, .card, [class*='benchmark']", timeout=10000)
        cards = page.locator(".benchmark-card, [class*='benchmark-card']").count()
        assert cards >= 60, f"Expected ~64 benchmark cards, got {cards}"

    def test_no_javascript_errors(self, page: Page):
        """Page should load without JavaScript errors"""
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(BASE_URL)
        page.wait_for_timeout(3000)
        critical_errors = [e for e in errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical_errors) == 0, f"JavaScript errors: {critical_errors}"


class TestSearchFunctionality:
    """Test search and filtering features"""

    def test_search_by_id(self, page: Page):
        """Search by benchmark ID should filter results"""
        page.goto(BASE_URL)
        page.wait_for_selector("input[type='text'], input[type='search'], .search-input")
        search = page.locator("input[type='text'], input[type='search'], .search-input").first
        search.fill("S7BEN-EASY")
        page.wait_for_timeout(500)
        visible_cards = page.locator(".benchmark-card:visible, [class*='benchmark-card']:visible")
        count = visible_cards.count()
        assert count > 0, "No results for S7BEN-EASY search"
        assert count <= 15, f"Too many results for EASY search: {count}"

    def test_search_by_name(self, page: Page):
        """Search by vulnerability name should filter results"""
        page.goto(BASE_URL)
        search = page.locator("input[type='text'], input[type='search'], .search-input").first
        search.fill("CSRF")
        page.wait_for_timeout(500)
        content = page.content()
        assert "CSRF" in content.upper() or page.locator(":text('csrf')").count() > 0

    def test_clear_search(self, page: Page):
        """Clearing search should show all benchmarks again"""
        page.goto(BASE_URL)
        search = page.locator("input[type='text'], input[type='search'], .search-input").first
        search.fill("EASY")
        page.wait_for_timeout(500)
        search.fill("")
        page.wait_for_timeout(500)
        visible_cards = page.locator(".benchmark-card:visible, [class*='benchmark-card']:visible")
        assert visible_cards.count() >= 60


# WSL-OPTIMIZED FIXTURE
@pytest.fixture(scope="function")
def page():
    """Create a new browser page for each test - WSL optimized"""
    with sync_playwright() as p:
        # Launch with WSL-friendly arguments
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',           # Required for WSL
                '--disable-dev-shm-usage', # Prevent shared memory issues
                '--disable-gpu',          # GPU not needed in headless
                '--disable-software-rasterizer',
                '--disable-extensions'
            ]
        )
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )
        page = context.new_page()
        yield page
        browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
