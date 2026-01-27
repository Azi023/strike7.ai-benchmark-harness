#!/bin/bash

# Strike7 Dashboard Deployment Script
# Quick deployment of the dashboard with all dependencies

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════╗"
echo "║  Strike7 Dashboard Deployment            ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# Check Python
echo -e "${BLUE}[1/5]${NC} Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $(python3 --version | cut -d' ' -f2) found${NC}"

# Check pip
echo -e "${BLUE}[2/5]${NC} Checking pip..."
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}pip not found. Installing...${NC}"
    python3 -m ensurepip --upgrade
fi
echo -e "${GREEN}✓ pip found${NC}"

# Install dependencies
echo -e "${BLUE}[3/5]${NC} Installing dependencies..."
cd dashboard
pip3 install -r requirements.txt --quiet
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Verify benchmark registry
echo -e "${BLUE}[4/5]${NC} Verifying benchmark registry..."
if [[ ! -f "config/benchmarks.yaml" ]]; then
    echo -e "${YELLOW}Warning: benchmarks.yaml not found${NC}"
    exit 1
fi

BENCH_COUNT=$(grep -c '  - id: S7BEN' config/benchmarks.yaml || echo "0")
echo -e "${GREEN}✓ Found $BENCH_COUNT benchmarks in registry${NC}"

# Start dashboard
echo -e "${BLUE}[5/5]${NC} Starting dashboard..."
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  Dashboard Starting!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo -e "  📊 Dashboard URL: ${BLUE}http://localhost:5500${NC}"
echo -e "  📚 API Documentation: ${BLUE}http://localhost:5500/api/health${NC}"
echo -e "  🎯 Total Benchmarks: ${GREEN}$BENCH_COUNT${NC}"
echo ""
echo -e "  Press ${YELLOW}Ctrl+C${NC} to stop the dashboard"
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""

python3 app.py
