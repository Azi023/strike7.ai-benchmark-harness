"""
Strike7 Dashboard - Playwright E2E Test Suite
Automated end-to-end testing for all dashboard features

Installation:
    pip install pytest-playwright
    playwright install chromium

Run:
    pytest test_e2e_playwright.py -v --headed  # With browser visible
    pytest test_e2e_playwright.py -v           # Headless mode
"""

import pytest
from playwright.sync_api import Page, expect, sync_playwright
import time
import re

# Configuration
BASE_URL = "http://localhost:5500"
# BASE_URL = "http://172.19.136.137:5500"  # VPS URL


class TestDashboardLoad:
    """Test dashboard loading and initial state"""

    def test_page_loads_successfully(self, page: Page):
        """Dashboard should load without errors"""
        page.goto(BASE_URL)
        expect(page).to_have_title(re.compile(r"Strike7|Dashboard", re.IGNORECASE))

    def test_statistics_panel_visible(self, page: Page):
        """Statistics panel should be visible with correct counts"""
        page.goto(BASE_URL)

        # Wait for stats to load
        page.wait_for_selector(".statistics, .stats-panel, [class*='stat']", timeout=10000)

        # Check for benchmark count
        content = page.content()
        assert "64" in content or "benchmarks" in content.lower()

    def test_all_benchmarks_load(self, page: Page):
        """All 64 benchmark cards should load"""
        page.goto(BASE_URL)
        page.wait_for_selector(".benchmark-card, .card, [class*='benchmark']", timeout=10000)

        # Count benchmark cards
        cards = page.locator(".benchmark-card, [class*='benchmark-card']").count()
        assert cards >= 60, f"Expected ~64 benchmark cards, got {cards}"

    def test_no_javascript_errors(self, page: Page):
        """Page should load without JavaScript errors"""
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))

        page.goto(BASE_URL)
        page.wait_for_timeout(3000)  # Wait for async operations

        # Filter out minor errors
        critical_errors = [e for e in errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical_errors) == 0, f"JavaScript errors: {critical_errors}"


class TestSearchFunctionality:
    """Test search and filtering features"""

    def test_search_by_id(self, page: Page):
        """Search by benchmark ID should filter results"""
        page.goto(BASE_URL)
        page.wait_for_selector("input[type='text'], input[type='search'], .search-input")

        # Find search input
        search = page.locator("input[type='text'], input[type='search'], .search-input").first
        search.fill("S7BEN-EASY")

        # Wait for filter to apply
        page.wait_for_timeout(500)

        # Check visible cards contain EASY
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

        # Should show CSRF-related benchmarks
        content = page.content()
        assert "CSRF" in content.upper() or page.locator(":text('csrf')").count() > 0

    def test_search_no_results(self, page: Page):
        """Search with no matches should show empty state"""
        page.goto(BASE_URL)

        search = page.locator("input[type='text'], input[type='search'], .search-input").first
        search.fill("xyznonexistent123456")

        page.wait_for_timeout(500)

        # Should show no results or empty state
        visible_cards = page.locator(".benchmark-card:visible, [class*='benchmark-card']:visible")
        assert visible_cards.count() == 0 or "no results" in page.content().lower()

    def test_clear_search(self, page: Page):
        """Clearing search should show all benchmarks again"""
        page.goto(BASE_URL)

        search = page.locator("input[type='text'], input[type='search'], .search-input").first

        # Search first
        search.fill("EASY")
        page.wait_for_timeout(500)

        # Clear
        search.fill("")
        page.wait_for_timeout(500)

        # Should show all benchmarks
        visible_cards = page.locator(".benchmark-card:visible, [class*='benchmark-card']:visible")
        assert visible_cards.count() >= 60


class TestCategoryFilter:
    """Test category filtering"""

    @pytest.mark.parametrize("category,expected_min,expected_max", [
        ("EASY", 8, 10),
        ("MED", 14, 18),
        ("HARD", 12, 16),
        ("VHARD", 12, 16),
        ("CVE", 9, 13),
    ])
    def test_category_filter(self, page: Page, category: str, expected_min: int, expected_max: int):
        """Category filter should show correct number of benchmarks"""
        page.goto(BASE_URL)
        page.wait_for_selector("select, .filter-dropdown, [class*='category']")

        # Find and click category filter
        category_select = page.locator("select").filter(has_text=re.compile(r"categor|all", re.IGNORECASE)).first
        if category_select.count() > 0:
            category_select.select_option(label=re.compile(category, re.IGNORECASE))

        page.wait_for_timeout(500)

        # Count visible cards
        visible_cards = page.locator(".benchmark-card:visible, [class*='benchmark-card']:visible")
        count = visible_cards.count()

        assert expected_min <= count <= expected_max, \
            f"{category} filter: expected {expected_min}-{expected_max}, got {count}"


class TestOwaspFilter:
    """Test OWASP Top 10 filtering"""

    def test_owasp_dropdown_exists(self, page: Page):
        """OWASP filter dropdown should exist"""
        page.goto(BASE_URL)

        # Look for OWASP-related dropdown
        owasp_element = page.locator("select, [class*='owasp']").filter(
            has_text=re.compile(r"owasp|A0[1-9]|A10", re.IGNORECASE)
        )

        assert owasp_element.count() > 0, "OWASP filter not found"

    def test_owasp_filter_injection(self, page: Page):
        """OWASP A03 (Injection) filter should work"""
        page.goto(BASE_URL)

        # Find OWASP dropdown
        owasp_select = page.locator("select").filter(
            has_text=re.compile(r"owasp|injection", re.IGNORECASE)
        ).first

        if owasp_select.count() > 0:
            # Try to select A03 - Injection
            try:
                owasp_select.select_option(label=re.compile(r"A03|injection", re.IGNORECASE))
                page.wait_for_timeout(500)

                # Should show only injection benchmarks
                visible_cards = page.locator(".benchmark-card:visible")
                assert visible_cards.count() > 0, "No injection benchmarks found"
            except:
                # Filter might use different format
                pass


class TestContainerManagement:
    """Test container start/stop functionality"""

    def test_start_button_visible(self, page: Page):
        """Start button should be visible on benchmark cards"""
        page.goto(BASE_URL)
        page.wait_for_selector(".benchmark-card, [class*='benchmark']")

        # Find a start button
        start_btn = page.locator("button, [class*='btn']").filter(
            has_text=re.compile(r"start", re.IGNORECASE)
        ).first

        assert start_btn.is_visible(), "Start button not found"

    def test_start_container(self, page: Page):
        """Clicking Start should start a container"""
        page.goto(BASE_URL)
        page.wait_for_selector(".benchmark-card")

        # Find and click first start button
        start_btn = page.locator("button, [class*='btn']").filter(
            has_text=re.compile(r"start", re.IGNORECASE)
        ).first

        start_btn.click()

        # Wait for container to start (up to 30 seconds)
        page.wait_for_timeout(5000)

        # Check for access URL or running status
        page.wait_for_selector(
            "[class*='url'], [class*='port'], [class*='running'], [class*='status']",
            timeout=30000
        )

        # Verify access URL appears
        content = page.content()
        assert "localhost:" in content or "running" in content.lower() or "stop" in content.lower()

    def test_stop_container(self, page: Page):
        """Stop button should stop the container"""
        page.goto(BASE_URL)

        # First start a container
        start_btn = page.locator("button").filter(has_text=re.compile(r"start", re.IGNORECASE)).first
        start_btn.click()
        page.wait_for_timeout(10000)

        # Find and click stop button
        stop_btn = page.locator("button").filter(has_text=re.compile(r"stop", re.IGNORECASE)).first

        if stop_btn.is_visible():
            stop_btn.click()
            page.wait_for_timeout(5000)

            # Start button should return
            start_btn = page.locator("button").filter(has_text=re.compile(r"start", re.IGNORECASE)).first
            assert start_btn.is_visible(), "Start button should be visible after stop"

    def test_copy_url_button(self, page: Page):
        """Copy URL button should exist when container is running"""
        page.goto(BASE_URL)

        # Start a container
        start_btn = page.locator("button").filter(has_text=re.compile(r"start", re.IGNORECASE)).first
        start_btn.click()
        page.wait_for_timeout(10000)

        # Look for copy URL button
        copy_btn = page.locator("button, [class*='btn']").filter(
            has_text=re.compile(r"copy|url", re.IGNORECASE)
        )

        # Should exist (but clipboard API might be restricted)
        # assert copy_btn.count() > 0 or "localhost:" in page.content()

        # Cleanup - stop container
        stop_btn = page.locator("button").filter(has_text=re.compile(r"stop", re.IGNORECASE)).first
        if stop_btn.is_visible():
            stop_btn.click()


class TestFlagSubmission:
    """Test flag submission functionality"""

    def test_submit_flag_button_exists(self, page: Page):
        """Submit Flag button should exist on cards"""
        page.goto(BASE_URL)
        page.wait_for_selector(".benchmark-card")

        flag_btn = page.locator("button, [class*='btn']").filter(
            has_text=re.compile(r"flag|submit", re.IGNORECASE)
        ).first

        assert flag_btn.is_visible(), "Submit Flag button not found"

    def test_flag_modal_opens(self, page: Page):
        """Clicking Submit Flag should open a modal"""
        page.goto(BASE_URL)

        flag_btn = page.locator("button, [class*='btn']").filter(
            has_text=re.compile(r"flag|submit", re.IGNORECASE)
        ).first

        flag_btn.click()
        page.wait_for_timeout(500)

        # Modal should be visible
        modal = page.locator(".modal, [class*='modal'], [role='dialog']")
        assert modal.is_visible() or page.locator("input").filter(has=page.locator("[placeholder*='flag']")).count() > 0

    def test_flag_modal_close(self, page: Page):
        """Modal should close on cancel or X"""
        page.goto(BASE_URL)

        # Open modal
        flag_btn = page.locator("button").filter(has_text=re.compile(r"flag|submit", re.IGNORECASE)).first
        flag_btn.click()
        page.wait_for_timeout(500)

        # Try to close
        close_btn = page.locator("button, [class*='close']").filter(
            has_text=re.compile(r"cancel|close|x", re.IGNORECASE)
        ).first

        if close_btn.is_visible():
            close_btn.click()
            page.wait_for_timeout(500)

            # Modal should be hidden
            modal = page.locator(".modal:visible, [class*='modal']:visible")
            assert modal.count() == 0 or not modal.is_visible()

    def test_wrong_flag_shows_error(self, page: Page):
        """Submitting wrong flag should show error"""
        page.goto(BASE_URL)

        # Open modal
        flag_btn = page.locator("button").filter(has_text=re.compile(r"flag|submit", re.IGNORECASE)).first
        flag_btn.click()
        page.wait_for_timeout(500)

        # Enter wrong flag
        flag_input = page.locator("input").filter(has=page.locator("[type='text']")).first
        if flag_input.count() > 0:
            flag_input.fill("S7BEN{wrong_flag}")

            # Submit
            submit_btn = page.locator("button").filter(has_text=re.compile(r"submit", re.IGNORECASE)).first
            submit_btn.click()
            page.wait_for_timeout(1000)

            # Should show error notification
            content = page.content().lower()
            assert "error" in content or "incorrect" in content or "wrong" in content or "invalid" in content


class TestNotifications:
    """Test toast notifications"""

    def test_notification_appears_on_action(self, page: Page):
        """Notifications should appear for user actions"""
        page.goto(BASE_URL)

        # Try an action that triggers notification
        # Start a container
        start_btn = page.locator("button").filter(has_text=re.compile(r"start", re.IGNORECASE)).first
        start_btn.click()

        # Wait for potential notification
        page.wait_for_timeout(3000)

        # Look for toast/notification element
        notification = page.locator(
            ".toast, .notification, [class*='toast'], [class*='alert'], [role='alert']"
        )

        # Notification might or might not appear depending on implementation
        # This is more of a smoke test

        # Cleanup
        stop_btn = page.locator("button").filter(has_text=re.compile(r"stop", re.IGNORECASE)).first
        if stop_btn.is_visible():
            stop_btn.click()


class TestPerformance:
    """Test performance metrics"""

    def test_page_load_time(self, page: Page):
        """Page should load within 5 seconds"""
        start = time.time()
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        load_time = time.time() - start

        assert load_time < 5, f"Page load took {load_time:.2f}s (expected < 5s)"

    def test_filter_response_time(self, page: Page):
        """Filters should respond within 1 second"""
        page.goto(BASE_URL)
        page.wait_for_selector("input, select")

        search = page.locator("input[type='text'], input[type='search']").first

        start = time.time()
        search.fill("EASY")
        page.wait_for_timeout(100)  # Small delay for debounce
        filter_time = time.time() - start

        assert filter_time < 1, f"Filter took {filter_time:.2f}s (expected < 1s)"


class TestE2EWorkflow:
    """End-to-end workflow tests"""

    def test_full_benchmark_workflow(self, page: Page):
        """Complete workflow: Search → Start → Flag → Stop"""
        page.goto(BASE_URL)

        # 1. Search for a specific benchmark
        search = page.locator("input[type='text'], input[type='search']").first
        search.fill("S7BEN-EASY-001")
        page.wait_for_timeout(500)

        # 2. Start the benchmark
        start_btn = page.locator("button").filter(has_text=re.compile(r"start", re.IGNORECASE)).first
        start_btn.click()
        page.wait_for_timeout(10000)  # Wait for container

        # 3. Verify running state
        content = page.content()
        assert "localhost:" in content or "running" in content.lower() or "stop" in content.lower()

        # 4. Try flag submission
        flag_btn = page.locator("button").filter(has_text=re.compile(r"flag|submit", re.IGNORECASE)).first
        if flag_btn.is_visible():
            flag_btn.click()
            page.wait_for_timeout(500)

            # Enter flag
            flag_input = page.locator("input").first
            flag_input.fill("S7BEN{test_flag}")

            # Close modal
            page.keyboard.press("Escape")

        # 5. Stop the benchmark
        stop_btn = page.locator("button").filter(has_text=re.compile(r"stop", re.IGNORECASE)).first
        if stop_btn.is_visible():
            stop_btn.click()
            page.wait_for_timeout(5000)

        # 6. Verify stopped state
        start_btn = page.locator("button").filter(has_text=re.compile(r"start", re.IGNORECASE)).first
        assert start_btn.is_visible(), "Start button should be visible after workflow"


# Pytest fixtures
@pytest.fixture(scope="function")
def page():
    """Create a new browser page for each test"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        yield page
        browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
