#!/bin/bash
# Run Playwright tests with visible browser (headed mode)
# Useful for debugging and watching tests execute

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)/venv"

# Activate virtual environment if it exists
if [ -f "$VENV_DIR/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
fi

cd "$SCRIPT_DIR"

echo "Running Playwright tests in HEADED mode (browser visible)..."
echo ""

python -m pytest test_e2e_playwright.py -v --headed --tb=short "$@"
