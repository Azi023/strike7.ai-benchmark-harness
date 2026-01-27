# Fix Chromium Installation in WSL

## The Problem

You're seeing two issues:

1. **Lockfile error**: `An active lockfile is found at /home/atheeque/.cache/ms-playwright/__dirlock`
2. **Missing browser**: `Executable doesn't exist at .../chromium_headless_shell-1200/...`

## Why This Happens

- Previous installation attempt was interrupted
- Lockfile prevents concurrent installations
- Chromium headless shell didn't fully download

---

## Solution Options

### Option 1: Quick Fix Script (Recommended)

```bash
cd ~/workspace/strike7-benchmarks/dashboard/tests
./fix_playwright.sh
```

This will:
- Remove the lockfile
- Clean partial installations
- Reinstall Chromium completely

### Option 2: Manual Fix

```bash
# 1. Remove lockfile
rm -rf ~/.cache/ms-playwright/__dirlock

# 2. Activate venv
cd ~/workspace/strike7-benchmarks
source venv/bin/activate

# 3. Clean and reinstall
rm -rf ~/.cache/ms-playwright/chromium-1200
rm -rf ~/.cache/ms-playwright/chromium_headless_shell-1200
playwright install --force chromium

# 4. Verify
ls ~/.cache/ms-playwright/
```

### Option 3: Use Fixed Test File (No headless shell needed)

We created a modified test file that works without the headless shell:

```bash
cd ~/workspace/strike7-benchmarks/dashboard/tests
source ../../venv/bin/activate

# Run the fixed version
pytest test_e2e_playwright_fixed.py -v
```

This version uses regular Chromium with WSL-friendly flags instead of the headless shell.

---

## Step-by-Step: Complete Fix

### Step 1: Remove Lockfile

```bash
rm -rf ~/.cache/ms-playwright/__dirlock
```

### Step 2: Clean Playwright Cache

```bash
rm -rf ~/.cache/ms-playwright/*
```

### Step 3: Activate Virtual Environment

```bash
cd ~/workspace/strike7-benchmarks
source venv/bin/activate
```

### Step 4: Install Chromium (with retry)

```bash
# Try 1: Normal install
playwright install chromium

# If that fails, try with --force
playwright install --force chromium

# If still fails, install all browsers
playwright install
```

### Step 5: Verify Installation

```bash
# Check if directories exist
ls -la ~/.cache/ms-playwright/

# You should see:
# chromium-1200/
# chromium_headless_shell-1200/ (or just chromium-1200 is fine)
```

### Step 6: Test

```bash
cd dashboard/tests

# Start dashboard first (in another terminal)
# cd dashboard && python app.py

# Run tests with fixed version
pytest test_e2e_playwright_fixed.py::TestDashboardLoad::test_page_loads_successfully -v
```

---

## If Still Not Working: Alternative Approaches

### Alternative 1: Use Regular Chromium Build

Edit `test_e2e_playwright.py` fixture (line 462):

```python
@pytest.fixture(scope="function")
def page():
    """Create a new browser page for each test"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            channel="chromium",  # Use system chromium
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = browser.new_context()
        page = context.new_page()
        yield page
        browser.close()
```

### Alternative 2: Install System Dependencies

Some WSL systems need additional libraries:

```bash
sudo apt update
sudo apt install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2
```

Then retry:
```bash
playwright install --with-deps chromium
```

### Alternative 3: Use Firefox Instead

```bash
# Install Firefox browser
playwright install firefox

# Run tests with Firefox
pytest test_e2e_playwright.py --browser firefox -v
```

---

## Understanding the Error

### What is `chromium_headless_shell`?

- It's a lightweight version of Chromium for headless testing
- Faster and uses less resources than full Chromium
- Required by Playwright by default

### Why does it fail in WSL?

- WSL file system can be slow
- Downloads can timeout
- Lockfiles don't always clean up properly

### Do I need it?

No! You can use regular Chromium with headless flags (which is what `test_e2e_playwright_fixed.py` does).

---

## Recommended Solution (Simplest)

**Use the fixed test file:**

```bash
cd ~/workspace/strike7-benchmarks/dashboard/tests
source ../../venv/bin/activate

# Run the fix script first
./fix_playwright.sh

# Then use the fixed test file
pytest test_e2e_playwright_fixed.py -v
```

The fixed test file (`test_e2e_playwright_fixed.py`):
- ✅ Uses regular Chromium (not headless shell)
- ✅ Adds WSL-friendly browser arguments
- ✅ Works in WSL without system dependencies
- ✅ Same tests, just different browser configuration

---

## Verification Commands

```bash
# Check if venv is activated
which python
# Should show: /home/atheeque/workspace/strike7-benchmarks/venv/bin/python

# Check playwright version
playwright --version
# Should show: Version 1.57.0

# Check installed browsers
playwright show-browsers
# or
ls ~/.cache/ms-playwright/

# Check for lockfile
ls ~/.cache/ms-playwright/__dirlock
# Should show: No such file or directory
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `rm -rf ~/.cache/ms-playwright/__dirlock` | Remove lockfile |
| `playwright install --force chromium` | Force reinstall |
| `./fix_playwright.sh` | Automated fix |
| `pytest test_e2e_playwright_fixed.py -v` | Run tests with fixed version |

---

## What About GUI Chromium?

You mentioned ChatGPT suggested X server (VcXsrv). **You DON'T need that** for Playwright testing because:

- ✅ Playwright runs headless (no GUI needed)
- ✅ Tests run in background
- ✅ Faster without GUI
- ✅ Better for automation

**X Server is only needed if:**
- You want to manually browse websites from WSL Ubuntu
- You need to debug visually
- You're testing GUI-specific features

**For Strike7 testing: Stay headless!**

---

## Next Steps

1. **Run the fix script:**
   ```bash
   ./fix_playwright.sh
   ```

2. **Test with fixed version:**
   ```bash
   pytest test_e2e_playwright_fixed.py::TestDashboardLoad -v
   ```

3. **If that works, run full suite:**
   ```bash
   pytest test_e2e_playwright_fixed.py -v
   ```

4. **If successful, can switch back to original:**
   ```bash
   pytest test_e2e_playwright.py -v
   ```

---

**Status:** Ready to fix!
**Recommended:** Run `./fix_playwright.sh` then use the fixed test file.
