# ✅ FINAL FIX - Missing System Libraries

## The Issue

Chromium is installed but missing system libraries:
```
error while loading shared libraries: libnspr4.so: cannot open shared object file
```

## The Solution (2 Commands)

### Step 1: Install System Dependencies

```bash
cd ~/workspace/strike7-benchmarks/dashboard/tests
./install_dependencies.sh
```

Or manually:
```bash
sudo apt update
sudo apt install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2 libatspi2.0-0 libxshmfence1
```

### Step 2: Run Tests

```bash
cd ~/workspace/strike7-benchmarks/dashboard/tests
source ../../venv/bin/activate
pytest test_e2e_playwright_fixed.py::TestDashboardLoad -v
```

---

## Expected Result

After installing dependencies, you should see:

```
test_e2e_playwright_fixed.py::TestDashboardLoad::test_page_loads_successfully PASSED [ 25%]
test_e2e_playwright_fixed.py::TestDashboardLoad::test_statistics_panel_visible PASSED [ 50%]
test_e2e_playwright_fixed.py::TestDashboardLoad::test_all_benchmarks_load PASSED [ 75%]
test_e2e_playwright_fixed.py::TestDashboardLoad::test_no_javascript_errors PASSED [100%]

============================== 4 passed in 5.2s ==============================
```

---

## What These Libraries Do

| Library | Purpose |
|---------|---------|
| `libnspr4` | Network Security Services (required) |
| `libnss3` | Security certificates |
| `libatk*` | Accessibility toolkit |
| `libcups2` | Printing support |
| `libgbm1` | Graphics buffer manager |
| `libasound2` | Audio support |
| `libpango*` | Text rendering |
| `libcairo2` | 2D graphics |

---

## Why This Happened

Playwright downloads its own Chromium binary, but that binary expects certain system libraries to be installed. WSL Ubuntu minimal doesn't include all browser dependencies by default.

---

## One-Line Fix (if you prefer)

```bash
sudo apt update && sudo apt install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2 libatspi2.0-0 libxshmfence1
```

Then run tests:
```bash
cd ~/workspace/strike7-benchmarks/dashboard/tests
source ../../venv/bin/activate
pytest test_e2e_playwright_fixed.py -v
```

---

## Verification

Check if library is available:
```bash
ldconfig -p | grep libnspr4
# Should show: libnspr4.so
```

If it shows output, the library is installed!

---

**Next:** After installing dependencies, your tests will work!
