#!/bin/bash
# Quick API Test Runner for Strike7 Dashboard Backend
# Tests core API endpoints to ensure backend is functioning correctly

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    Strike7 Backend API Quick Test                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Activate virtual environment
echo -e "${YELLOW}→${NC} Activating virtual environment..."
cd "$PROJECT_ROOT"
source venv/bin/activate

# Check if dashboard is running
echo -e "${YELLOW}→${NC} Checking if dashboard is running..."
DASHBOARD_URL="http://localhost:5500"

if ! curl -s "${DASHBOARD_URL}/api/health" > /dev/null 2>&1; then
    echo -e "${RED}✗${NC} Dashboard is not running at ${DASHBOARD_URL}"
    echo ""
    echo "Please start the dashboard first:"
    echo "  cd dashboard"
    echo "  python app.py"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓${NC} Dashboard is running"
echo ""

# Test selection
if [ "$1" == "--all" ]; then
    echo -e "${YELLOW}→${NC} Running ALL API tests (this may take a while)..."
    echo ""
    cd "$SCRIPT_DIR"
    pytest test_backend_qa.py -v --tb=short -s
elif [ "$1" == "--benchmarks" ]; then
    echo -e "${YELLOW}→${NC} Running benchmark API tests..."
    echo ""
    cd "$SCRIPT_DIR"
    pytest test_backend_qa.py::TestBenchmarkAPIs -v --tb=short -s
elif [ "$1" == "--stats" ]; then
    echo -e "${YELLOW}→${NC} Running statistics API tests..."
    echo ""
    cd "$SCRIPT_DIR"
    pytest test_backend_qa.py::TestStatisticsAPIs -v --tb=short -s
elif [ "$1" == "--containers" ]; then
    echo -e "${YELLOW}→${NC} Running container API tests..."
    echo ""
    cd "$SCRIPT_DIR"
    pytest test_backend_qa.py::TestContainerAPIs -v --tb=short -s
elif [ "$1" == "--flags" ]; then
    echo -e "${YELLOW}→${NC} Running flag submission API tests..."
    echo ""
    cd "$SCRIPT_DIR"
    pytest test_backend_qa.py::TestFlagSubmissionAPIs -v --tb=short -s
elif [ "$1" == "--sessions" ]; then
    echo -e "${YELLOW}→${NC} Running session API tests..."
    echo ""
    cd "$SCRIPT_DIR"
    pytest test_backend_qa.py::TestSessionAPIs -v --tb=short -s
elif [ "$1" == "--metrics" ]; then
    echo -e "${YELLOW}→${NC} Running metrics API tests..."
    echo ""
    cd "$SCRIPT_DIR"
    pytest test_backend_qa.py::TestMetricsAPIs -v --tb=short -s
elif [ "$1" == "--errors" ]; then
    echo -e "${YELLOW}→${NC} Running error handling tests..."
    echo ""
    cd "$SCRIPT_DIR"
    pytest test_backend_qa.py::TestErrorHandling -v --tb=short -s
elif [ "$1" == "--integration" ]; then
    echo -e "${YELLOW}→${NC} Running integration tests..."
    echo ""
    cd "$SCRIPT_DIR"
    pytest test_backend_qa.py::TestDashboardIntegration -v --tb=short -s
else
    echo -e "${YELLOW}→${NC} Running SMOKE TESTS (quick verification)..."
    echo ""
    cd "$SCRIPT_DIR"

    # Run a few key tests from each category
    pytest test_backend_qa.py::TestBenchmarkAPIs::test_get_all_benchmarks \
           test_backend_qa.py::TestStatisticsAPIs::test_get_statistics \
           test_backend_qa.py::TestContainerAPIs::test_get_containers_status \
           test_backend_qa.py::TestSessionAPIs::test_start_session \
           test_backend_qa.py::TestErrorHandling::test_health_check \
           -v --tb=short -s
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓${NC} API tests completed!"
echo ""
echo "Available test options:"
echo "  ./quick_api_test.sh             # Quick smoke tests (default)"
echo "  ./quick_api_test.sh --all       # Run all API tests"
echo "  ./quick_api_test.sh --benchmarks # Test benchmark endpoints"
echo "  ./quick_api_test.sh --stats      # Test statistics endpoints"
echo "  ./quick_api_test.sh --containers # Test container management"
echo "  ./quick_api_test.sh --flags      # Test flag submission"
echo "  ./quick_api_test.sh --sessions   # Test session tracking"
echo "  ./quick_api_test.sh --metrics    # Test metrics endpoints"
echo "  ./quick_api_test.sh --errors     # Test error handling"
echo "  ./quick_api_test.sh --integration # Test full workflows"
echo ""
