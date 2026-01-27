# Playwright Installation for WSL/Linux

## Issue Encountered
Playwright was initially installed on Windows but you're running tests from WSL/Linux with a virtual environment.

## Solution: Install in WSL Virtual Environment

### Step 1: Install Python Packages (Already Done ✅)
```bash
cd ~/workspace/strike7-benchmarks
source venv/bin/activate
pip install pytest pytest-playwright
```

### Step 2: Install Chromium Browser
You have two options:

#### Option A: Install without system dependencies (Headless only)
```bash
cd ~/workspace/strike7-benchmarks
source venv/bin/activate
playwright install chromium
```

#### Option B: Install with system dependencies (Requires sudo)
This installs system libraries needed for GUI mode:
```bash
cd ~/workspace/strike7-benchmarks
source venv/bin/activate
sudo playwright install-deps chromium  # This requires sudo password
playwright install chromium
```

**Note:** If you don't have sudo access or don't want to install system deps, use Option A.

### Step 3: Verify Installation
```bash
cd ~/workspace/strike7-benchmarks
source venv/bin/activate
playwright --version
# Should show: Version 1.57.0
```

### Step 4: Run Tests
```bash
cd ~/workspace/strike7-benchmarks/dashboard/tests
source ../../venv/bin/activate

# Run quick test
pytest test_e2e_playwright.py::TestDashboardLoad::test_page_loads_successfully -v

# Run all tests
pytest test_e2e_playwright.py -v
```

## Quick Fix Scripts

We've updated the test scripts to work in WSL:

### Updated: run_tests.sh
```bash
#!/bin/bash
cd ~/workspace/strike7-benchmarks/dashboard/tests
source ../../venv/bin/activate
pytest test_e2e_playwright.py -v --tb=short "$@"
```

### Updated: quick_test.sh
```bash
#!/bin/bash
cd ~/workspace/strike7-benchmarks/dashboard/tests
source ../../venv/bin/activate
pytest test_e2e_playwright.py::TestDashboardLoad -v --tb=short
```

## If Tests Still Fail

### Missing Headless Shell Error?
If you see: `Executable doesn't exist at .../chromium_headless_shell-1200/...`

Run this:
```bash
cd ~/workspace/strike7-benchmarks
source venv/bin/activate
playwright install  # Install all browser components
```

### Dashboard Not Running?
Make sure the dashboard is running on localhost:5500:
```bash
# In another terminal
cd ~/workspace/strike7-benchmarks/dashboard
source ../venv/bin/activate
python app.py
```

### Alternative: Run Without Browser Dependencies
If you can't install system dependencies, use headed mode with a fallback:

Edit `test_e2e_playwright.py` and change the fixture:
```python
@pytest.fixture(scope="function")
def page():
    """Create a new browser page for each test"""
    with sync_playwright() as p:
        # Use chromium-headless-shell instead
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']  # WSL-friendly
        )
        context = browser.new_context()
        page = context.new_page()
        yield page
        browser.close()
```

## Current Status

✅ Python packages installed in WSL venv
✅ Playwright 1.57.0 installed
⏳ Browser installation in progress
⏳ Waiting for system dependencies (optional)

## Next Steps

1. Complete browser installation (run commands above)
2. Test with: `pytest test_e2e_playwright.py::TestDashboardLoad::test_page_loads_successfully -v`
3. If successful, run full suite: `pytest test_e2e_playwright.py -v`
