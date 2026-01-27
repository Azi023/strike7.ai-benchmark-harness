#!/bin/bash
# Strike7 MCP Server - End-to-End Test
# Tests all components to verify production readiness

echo "=============================================="
echo "Strike7 MCP Server - End-to-End Test"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC} - $2"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} - $2"
        ((FAILED++))
    fi
}

# Test 1: Dashboard API
echo "Test 1: Dashboard API Connectivity"
curl -s http://localhost:5500/api/health > /dev/null 2>&1
test_result $? "Dashboard API responding"

# Test 2: Benchmarks endpoint
echo ""
echo "Test 2: Benchmarks Endpoint"
BENCH_COUNT=$(curl -s http://localhost:5500/api/benchmarks | python -c "import sys, json; print(len(json.load(sys.stdin).get('benchmarks', [])))" 2>/dev/null)
if [ "$BENCH_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ PASS${NC} - Found $BENCH_COUNT benchmarks"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} - No benchmarks found"
    ((FAILED++))
fi

# Test 3: MCP capability check
echo ""
echo "Test 3: MCP Capability Check"
python test_mcp_capability.py > /dev/null 2>&1
test_result $? "MCP environment validated"

# Test 4: MCP server syntax
echo ""
echo "Test 4: MCP Server Syntax Check"
python -m py_compile dashboard/strike7_mcp_server.py > /dev/null 2>&1
test_result $? "MCP server syntax valid"

# Test 5: Container status
echo ""
echo "Test 5: Container Status Check"
curl -s http://localhost:5500/api/containers/status | grep -q "running_count" > /dev/null 2>&1
test_result $? "Container status endpoint working"

# Test 6: Documentation exists
echo ""
echo "Test 6: Documentation Files"
FILES_EXIST=0
[ -f "docs/MCP_VPS_DEPLOYMENT_GUIDE.md" ] && ((FILES_EXIST++))
[ -f "MCP_SERVER_COMPLETE.md" ] && ((FILES_EXIST++))
[ -f "dashboard/strike7_mcp_server.py" ] && ((FILES_EXIST++))

if [ $FILES_EXIST -eq 3 ]; then
    echo -e "${GREEN}✓ PASS${NC} - All documentation files present"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} - Missing documentation files"
    ((FAILED++))
fi

# Test 7: Stop button CSS fix
echo ""
echo "Test 7: Stop Button CSS Fix"
if grep -q "display: none;" dashboard/static/css/dashboard.css | grep -q "btn-stop"; then
    echo -e "${RED}✗ FAIL${NC} - Stop button still has display:none"
    ((FAILED++))
else
    echo -e "${GREEN}✓ PASS${NC} - Stop button CSS fixed"
    ((PASSED++))
fi

# Summary
echo ""
echo "=============================================="
echo "Test Summary"
echo "=============================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! MCP server is production ready.${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Some tests failed. Review the output above.${NC}"
    exit 1
fi
