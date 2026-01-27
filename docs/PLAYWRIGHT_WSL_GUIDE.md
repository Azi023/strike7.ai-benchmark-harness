# Playwright Installation Guide for WSL

**Issue:** Playwright was installed on Windows but you're running tests from WSL with a virtual environment.

**Solution:** Install Playwright in the WSL virtual environment.

---

## Quick Setup (Recommended)

### Option 1: Automated Installation Script

```bash
cd ~/workspace/strike7-benchmarks/dashboard/tests
./install_playwright_wsl.sh
```

This script will:
- Activate your virtual environment
- Install pytest and pytest-playwright
- Install Chromium browser
- Verify the installation

### Option 2: Manual Installation

```bash
# 1. Navigate to project
cd ~/workspace/strike7-benchmarks

# 2. Activate virtual environment
source venv/bin/activate

# 3. Install Python packages
pip install pytest pytest-playwright

# 4. Install Chromium browser
playwright install chromium

# 5. Verify installation
playwright --version
```

---

## Running Tests

### Before Running Tests

Make sure the dashboard is running:
```bash
# In one terminal
cd ~/workspace/strike7-benchmarks/dashboard
source ../venv/bin/activate
python app.py
```

### Quick Test (4 basic tests)

```bash
cd ~/workspace/strike7-benchmarks/dashboard/tests
source ../../venv/bin/activate
./quick_test.sh
```

Or manually:
```bash
cd ~/workspace/strike7-benchmarks/dashboard/tests
source ../../venv/bin/activate
pytest test_e2e_playwright.py::TestDashboardLoad::test_page_loads_successfully -v
```

### Full Test Suite (27 tests)

```bash
cd ~/workspace/strike7-benchmarks/dashboard/tests
source ../../venv/bin/activate
./run_tests.sh
```

Or manually:
```bash
cd ~/workspace/strike7-benchmarks/dashboard/tests
source ../../venv/bin/activate
pytest test_e2e_playwright.py -v
```

---

## Troubleshooting

### Issue: "No module named pytest"

**Cause:** Virtual environment not activated or pytest not installed.

**Solution:**
```bash
cd ~/workspace/strike7-benchmarks
source venv/bin/activate
pip install pytest pytest-playwright
```

### Issue: "Executable doesn't exist at .../chromium..."

**Cause:** Chromium browser not installed.

**Solution:**
```bash
cd ~/workspace/strike7-benchmarks
source venv/bin/activate
playwright install chromium
```

### Issue: "Permission denied" when running scripts

**Cause:** Scripts don't have execute permission.

**Solution:**
```bash
chmod +x ~/workspace/strike7-benchmarks/dashboard/tests/*.sh
```

### Issue: System dependencies missing

If you see errors about missing libraries (libX11, libasound2, etc.):

**Option A:** Install system dependencies (requires sudo):
```bash
cd ~/workspace/strike7-benchmarks
source venv/bin/activate
sudo playwright install-deps chromium
```

**Option B:** Use headless mode with no-sandbox (no sudo needed):

The test scripts already use headless mode by default, which should work without system dependencies.

### Issue: "Connection refused" to localhost:5500

**Cause:** Dashboard not running.

**Solution:**
```bash
# Start dashboard in another terminal
cd ~/workspace/strike7-benchmarks/dashboard
source ../venv/bin/activate
python app.py
```

---

## Verification Checklist

Run these commands to verify your setup:

```bash
cd ~/workspace/strike7-benchmarks
source venv/bin/activate

# Check Python
python --version
# Expected: Python 3.11 or higher

# Check pytest
pytest --version
# Expected: pytest 9.0.2

# Check Playwright
playwright --version
# Expected: Version 1.57.0

# Check if Chromium is installed
ls ~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome 2>/dev/null && echo "✓ Chromium installed" || echo "✗ Chromium missing"

# Check if dashboard is running
curl -s -o /dev/null -w "%{http_code}" http://localhost:5500 | grep -q "200" && echo "✓ Dashboard running" || echo "✗ Dashboard not running"
```

---

## What Was Installed

### In WSL Virtual Environment

✅ **Python Packages:**
- pytest (9.0.2)
- pytest-playwright (0.7.2)
- playwright (1.57.0)
- Dependencies: pyee, greenlet, pytest-base-url, python-slugify

✅ **Browser:**
- Chromium (v143.0.7499.4)
- Location: `~/.cache/ms-playwright/chromium-1200/`

✅ **Test Files:**
- `dashboard/tests/test_e2e_playwright.py` - 27 E2E tests
- `dashboard/tests/quick_test.sh` - Quick smoke test
- `dashboard/tests/run_tests.sh` - Full test runner
- `dashboard/tests/install_playwright_wsl.sh` - Installation script

---

## File Structure

```
strike7-benchmarks/
├── dashboard/
│   ├── tests/
│   │   ├── test_e2e_playwright.py       # Main test file (27 tests)
│   │   ├── quick_test.sh                # Quick test runner
│   │   ├── run_tests.sh                 # Full test runner
│   │   ├── run_tests_headed.sh          # Headed mode runner
│   │   ├── install_playwright_wsl.sh    # Installation script
│   │   ├── pytest.ini                   # Pytest configuration
│   │   ├── README.md                    # Detailed documentation
│   │   └── INSTALL_WSL.md               # WSL-specific guide
│   └── app.py                           # Dashboard server
└── venv/                                # Virtual environment
    ├── bin/
    │   ├── python
    │   ├── pytest
    │   └── playwright
    └── lib/
        └── python3.12/
            └── site-packages/
                ├── playwright/
                └── pytest/
```

---

## Common Commands Reference

```bash
# Activate venv (always do this first!)
cd ~/workspace/strike7-benchmarks
source venv/bin/activate

# Install Playwright
pip install pytest pytest-playwright
playwright install chromium

# Start dashboard
cd dashboard
python app.py

# Run quick test
cd dashboard/tests
./quick_test.sh

# Run all tests
./run_tests.sh

# Run specific test
pytest test_e2e_playwright.py::TestSearchFunctionality -v

# Run with output
pytest test_e2e_playwright.py -v -s

# Generate HTML report
pip install pytest-html
pytest test_e2e_playwright.py --html=report.html --self-contained-html
```

---

## Next Steps

1. **Run the installation script:**
   ```bash
   cd ~/workspace/strike7-benchmarks/dashboard/tests
   ./install_playwright_wsl.sh
   ```

2. **Verify everything works:**
   ```bash
   source ../../venv/bin/activate
   ./quick_test.sh
   ```

3. **If successful, run full test suite:**
   ```bash
   ./run_tests.sh
   ```

4. **Review test results and proceed with QA phase**

---

## Support

- **Test Documentation:** `dashboard/tests/README.md`
- **WSL-Specific Guide:** `dashboard/tests/INSTALL_WSL.md`
- **Playwright Docs:** https://playwright.dev/python/
- **Pytest Docs:** https://docs.pytest.org/

---

**Status:** Setup guide created
**Next Action:** Run `./install_playwright_wsl.sh` in WSL
