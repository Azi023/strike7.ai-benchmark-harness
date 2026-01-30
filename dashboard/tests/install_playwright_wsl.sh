#!/bin/bash
# Install Playwright in WSL Virtual Environment

set -e

echo "=========================================="
echo "Playwright Installation for WSL"
echo "=========================================="
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_DIR="$PROJECT_DIR/venv"

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Virtual environment not found at: $VENV_DIR"
    echo "Please create a virtual environment first:"
    echo "  cd $PROJECT_DIR"
    echo "  python3 -m venv venv"
    exit 1
fi

echo "✓ Found virtual environment at: $VENV_DIR"
echo ""

# Activate venv
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
echo ""

# Install Python packages
echo "Installing Python packages..."
pip install pytest pytest-playwright
echo ""

# Check if playwright is installed
if ! command -v playwright &> /dev/null; then
    echo "❌ Playwright installation failed"
    exit 1
fi

echo "✓ Playwright $(playwright --version) installed"
echo ""

# Install browsers
echo "Installing Chromium browser..."
echo ""

# Try to install chromium
playwright install chromium

echo ""
echo "=========================================="
echo "Installation Status"
echo "=========================================="
echo ""

# Verify installation
if [ -f "$HOME/.cache/ms-playwright/chromium-1200/chrome-linux/chrome" ] || \
   [ -f "$HOME/.cache/ms-playwright/chromium-1200/chrome-linux64/chrome" ]; then
    echo "✅ Chromium browser: Installed"
else
    echo "⚠️  Chromium browser: Partially installed"
    echo "   You may need to run: playwright install chromium"
fi

if command -v pytest &> /dev/null; then
    echo "✅ pytest: Installed"
else
    echo "❌ pytest: Not found"
fi

if command -v playwright &> /dev/null; then
    echo "✅ playwright: Installed ($(playwright --version))"
else
    echo "❌ playwright: Not found"
fi

echo ""
echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo ""
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Ensure dashboard is running:"
echo "   cd dashboard && python app.py"
echo ""
echo "3. Run tests:"
echo "   cd dashboard/tests"
echo "   ./quick_test.sh"
echo ""
echo "=========================================="
