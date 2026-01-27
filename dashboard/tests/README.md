# Strike7 Dashboard - E2E Testing with Playwright

## Installation Complete ✓

Playwright has been successfully installed with the following components:
- `pytest` - Testing framework
- `pytest-playwright` - Playwright pytest plugin
- `playwright` - Browser automation library
- Chromium browser (v143.0.7499.4)

---

## Quick Start

### Run All Tests
```bash
cd dashboard/tests
python -m pytest test_e2e_playwright.py -v
```

### Run with Browser Visible (Headed Mode)
```bash
python -m pytest test_e2e_playwright.py -v --headed
```

### Run Specific Test Class
```bash
# Test only page load
python -m pytest test_e2e_playwright.py::TestDashboardLoad -v

# Test only search functionality
python -m pytest test_e2e_playwright.py::TestSearchFunctionality -v

# Test only container management
python -m pytest test_e2e_playwright.py::TestContainerManagement -v

# Test only flag submission
python -m pytest test_e2e_playwright.py::TestFlagSubmission -v

# Test full E2E workflow
python -m pytest test_e2e_playwright.py::TestE2EWorkflow -v
```

### Run Specific Single Test
```bash
python -m pytest test_e2e_playwright.py::TestDashboardLoad::test_page_loads_successfully -v
```

---

## Test Configuration

### Change Base URL
Edit the `BASE_URL` constant at the top of `test_e2e_playwright.py`:

```python
# For local testing
BASE_URL = "http://localhost:5500"

# For VPS testing
BASE_URL = "http://172.19.136.137:5500"
```

### Playwright Options

```bash
# Run in headed mode (see the browser)
pytest test_e2e_playwright.py --headed

# Run with specific browser
pytest test_e2e_playwright.py --browser=firefox
pytest test_e2e_playwright.py --browser=webkit

# Run with slow motion (for debugging)
pytest test_e2e_playwright.py --headed --slowmo=1000

# Run with browser context recording (traces)
pytest test_e2e_playwright.py --tracing=on

# Parallel execution (requires pytest-xdist)
pytest test_e2e_playwright.py -n 4
```

---

## Test Coverage

### Test Classes

| Class | Description | Tests |
|-------|-------------|-------|
| `TestDashboardLoad` | Page loading and initial state | 4 |
| `TestSearchFunctionality` | Search and filtering | 4 |
| `TestCategoryFilter` | Category dropdown filtering | 5 |
| `TestOwaspFilter` | OWASP Top 10 filtering | 2 |
| `TestContainerManagement` | Start/stop containers | 4 |
| `TestFlagSubmission` | Flag modal and submission | 4 |
| `TestNotifications` | Toast notifications | 1 |
| `TestPerformance` | Performance benchmarks | 2 |
| `TestE2EWorkflow` | Full end-to-end workflow | 1 |

**Total: 27 tests**

---

## Test Results Format

### Verbose Output
```bash
pytest test_e2e_playwright.py -v
```
Shows each test name and PASS/FAIL status.

### Detailed Output with Print Statements
```bash
pytest test_e2e_playwright.py -v -s
```
Shows print statements and console logs.

### Short Traceback
```bash
pytest test_e2e_playwright.py --tb=short
```
Shorter error messages for failures.

### Generate HTML Report (requires pytest-html)
```bash
pip install pytest-html
pytest test_e2e_playwright.py --html=report.html --self-contained-html
```

---

## Debugging Tests

### Screenshot on Failure
Playwright automatically captures screenshots on test failures.

### Trace Viewer
```bash
# Record traces
pytest test_e2e_playwright.py --tracing=retain-on-failure

# View traces
playwright show-trace trace.zip
```

### Debug Mode
```bash
# Set breakpoint in test
import pdb; pdb.set_trace()

# Run with debugger
pytest test_e2e_playwright.py -v --pdb
```

### Slow Motion
```bash
# See actions in slow motion
pytest test_e2e_playwright.py --headed --slowmo=2000
```

---

## Common Issues

### Issue: "Chromium not found"
**Solution:**
```bash
python -m playwright install chromium
```

### Issue: "Connection refused to localhost:5500"
**Solution:** Ensure the dashboard is running:
```bash
cd dashboard
python app.py
```

### Issue: Tests timing out
**Solution:** Increase timeout in test:
```python
page.wait_for_selector(".element", timeout=30000)  # 30 seconds
```

### Issue: Element not found
**Solution:** Use more flexible selectors:
```python
# Instead of exact class
page.locator(".benchmark-card")

# Use partial match
page.locator("[class*='benchmark']")

# Use text content
page.locator("text=Start")
```

---

## CI/CD Integration

### GitHub Actions Example
```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install pytest pytest-playwright
          playwright install chromium
      - name: Run tests
        run: |
          cd dashboard/tests
          pytest test_e2e_playwright.py -v
```

---

## Advanced Usage

### Parallel Test Execution
```bash
pip install pytest-xdist
pytest test_e2e_playwright.py -n auto
```

### Custom Markers
```python
# In test file
@pytest.mark.smoke
def test_critical_feature(self, page: Page):
    pass

# Run only smoke tests
pytest test_e2e_playwright.py -m smoke
```

### Parameterized Tests
Already implemented for category filters:
```python
@pytest.mark.parametrize("category,expected_min,expected_max", [
    ("EASY", 8, 10),
    ("MED", 14, 18),
])
def test_category_filter(self, page: Page, category: str, ...):
    pass
```

---

## Next Steps

1. **Run Full Test Suite:**
   ```bash
   cd dashboard/tests
   python -m pytest test_e2e_playwright.py -v
   ```

2. **Check Results:**
   - All tests should pass if dashboard is running
   - Some container tests may take longer (up to 30s)

3. **Add Custom Tests:**
   - Follow existing test patterns
   - Use descriptive test names
   - Add docstrings

4. **Integrate with CI/CD:**
   - Add to GitHub Actions
   - Run on every PR
   - Generate reports

---

## Additional Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-Playwright Plugin](https://github.com/microsoft/playwright-pytest)

---

**Installation Date:** 2026-01-26
**Version:** Playwright 1.57.0, Pytest 9.0.2
**Status:** ✅ Ready to use
