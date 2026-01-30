#!/bin/bash
# Quick smoke test - runs only the basic tests to verify setup

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)/venv"

# Activate virtual environment if it exists
if [ -f "$VENV_DIR/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
fi

cd "$SCRIPT_DIR"

echo "=========================================="
echo "Quick Smoke Test - Playwright Setup"
echo "=========================================="
echo ""

echo "Running basic tests to verify installation..."
echo ""

# Run only the TestDashboardLoad class (4 basic tests)
python -m pytest test_e2e_playwright.py::TestDashboardLoad -v --tb=short

echo ""
echo "=========================================="
echo "Quick test complete!"
echo "=========================================="
