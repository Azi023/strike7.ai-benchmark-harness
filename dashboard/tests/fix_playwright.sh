#!/bin/bash
# Fix Playwright Installation Issues in WSL

set -e

echo "=========================================="
echo "Playwright Installation Fix"
echo "=========================================="
echo ""

# Get directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_DIR="$PROJECT_DIR/venv"

# Activate venv
if [ -f "$VENV_DIR/bin/activate" ]; then
    echo "✓ Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
else
    echo "✗ Virtual environment not found!"
    exit 1
fi

echo ""

# Step 1: Remove lockfile if it exists
LOCKFILE="$HOME/.cache/ms-playwright/__dirlock"
if [ -f "$LOCKFILE" ]; then
    echo "Removing old lockfile..."
    rm -rf "$LOCKFILE"
    echo "✓ Lockfile removed"
else
    echo "✓ No lockfile found"
fi

echo ""

# Step 2: Clean up any partial installations
echo "Cleaning up partial installations..."
rm -rf "$HOME/.cache/ms-playwright/chromium-1200" 2>/dev/null || true
rm -rf "$HOME/.cache/ms-playwright/chromium_headless_shell-1200" 2>/dev/null || true
rm -rf "$HOME/.cache/ms-playwright/ffmpeg-1011" 2>/dev/null || true
echo "✓ Cleanup complete"

echo ""

# Step 3: Install Chromium with --force
echo "Installing Chromium (forced clean install)..."
echo ""
playwright install --force chromium

echo ""
echo "=========================================="
echo "Verification"
echo "=========================================="
echo ""

# Verify installation
if [ -d "$HOME/.cache/ms-playwright/chromium-1200" ]; then
    echo "✅ Chromium browser: Installed"
else
    echo "❌ Chromium browser: Failed"
fi

if [ -d "$HOME/.cache/ms-playwright/chromium_headless_shell-1200" ]; then
    echo "✅ Chromium Headless Shell: Installed"
else
    echo "⚠️  Chromium Headless Shell: Missing (trying to install...)"
    playwright install chromium-headless-shell 2>/dev/null || echo "   Note: May install with main chromium"
fi

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next step: Run the quick test"
echo "  ./quick_test.sh"
echo ""
