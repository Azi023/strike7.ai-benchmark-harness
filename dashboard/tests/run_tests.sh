#!/bin/bash
# Strike7 Dashboard - E2E Test Runner
# Quick script to run Playwright tests

set -e

echo "=========================================="
echo "Strike7 Dashboard - E2E Test Suite"
echo "=========================================="
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)/venv"

# Activate virtual environment if it exists
if [ -f "$VENV_DIR/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
fi

# Check if dashboard is running
echo "Checking if dashboard is running..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5500 2>/dev/null | grep -q "200"; then
    echo "✓ Dashboard is running on http://localhost:5500"
else
    echo "✗ Dashboard is not running!"
    echo "  Please start the dashboard first:"
    echo "  cd dashboard && python app.py"
    exit 1
fi

echo ""
echo "Running Playwright E2E tests..."
echo ""

# Run tests
cd "$SCRIPT_DIR"
python -m pytest test_e2e_playwright.py -v --tb=short "$@"

echo ""
echo "=========================================="
echo "Test run complete!"
echo "=========================================="
