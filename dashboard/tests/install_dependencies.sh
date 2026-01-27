#!/bin/bash
# Install system dependencies for Playwright Chromium in WSL

echo "=========================================="
echo "Installing Chromium System Dependencies"
echo "=========================================="
echo ""
echo "This will install the required libraries for Chromium to run in WSL."
echo "You will be prompted for your sudo password."
echo ""

# Update package list
echo "Updating package list..."
sudo apt update

echo ""
echo "Installing dependencies..."
echo ""

# Install all required libraries
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
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libxshmfence1

echo ""
echo "=========================================="
echo "✅ Dependencies Installed!"
echo "=========================================="
echo ""
echo "Now run the tests:"
echo "  pytest test_e2e_playwright_fixed.py::TestDashboardLoad -v"
echo ""
