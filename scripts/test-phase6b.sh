#!/bin/bash

# Strike7 Phase 6B - Comprehensive Test Suite
# Tests all 20 benchmarks created in Phase 6B

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
RESULTS_FILE="test-results-phase6b.md"

# Initialize results file
cat > "$RESULTS_FILE" <<EOF
# Phase 6B Test Results
**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Total Benchmarks:** 20

---

## Test Results

EOF

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
    echo "✅ $1" >> "$RESULTS_FILE"
    ((PASSED_TESTS++))
}

log_fail() {
    echo -e "${RED}❌ $1${NC}"
    echo "❌ $1" >> "$RESULTS_FILE"
    ((FAILED_TESTS++))
}

log_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

test_benchmark() {
    local bench_dir=$1
    local bench_name=$(basename "$bench_dir")

    ((TOTAL_TESTS++))

    echo ""
    log_info "Testing $bench_name..."
    echo "### $bench_name" >> "$RESULTS_FILE"

    cd "$bench_dir"

    # Check required files exist
    if [[ ! -f "docker-compose.yml" ]]; then
        log_fail "$bench_name: Missing docker-compose.yml"
        cd - > /dev/null
        return 1
    fi

    if [[ ! -f "Makefile" ]]; then
        log_fail "$bench_name: Missing Makefile"
        cd - > /dev/null
        return 1
    fi

    if [[ ! -f "exploit.sh" ]]; then
        log_fail "$bench_name: Missing exploit.sh"
        cd - > /dev/null
        return 1
    fi

    # Start the benchmark
    log_info "$bench_name: Starting containers..."
    if ! make up > /dev/null 2>&1; then
        log_fail "$bench_name: Failed to start containers"
        make down > /dev/null 2>&1 || true
        cd - > /dev/null
        return 1
    fi

    # Wait for services to be ready
    sleep 10

    # Test health endpoint if available
    local port=$(grep -oP ':\K\d+(?=:)' docker-compose.yml | head -1 || echo "")
    if [[ -n "$port" ]]; then
        log_info "$bench_name: Testing health endpoint on port $port..."
        if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1 || \
           curl -f -s "http://localhost:$port/" > /dev/null 2>&1; then
            log_info "$bench_name: Health check passed"
        else
            log_info "$bench_name: Health check failed (may be expected)"
        fi
    fi

    # Run exploit script
    log_info "$bench_name: Running exploit..."
    if bash exploit.sh > exploit_output.txt 2>&1; then
        if grep -q "S7BEN{" exploit_output.txt; then
            local flag=$(grep -oP 'S7BEN\{[^}]+\}' exploit_output.txt | head -1)
            log_success "$bench_name: Exploit successful! Flag: $flag"
        else
            log_fail "$bench_name: Exploit ran but no flag captured"
            echo "Output: $(cat exploit_output.txt)" >> "$RESULTS_FILE"
        fi
    else
        log_fail "$bench_name: Exploit script failed"
        echo "Error output: $(cat exploit_output.txt)" >> "$RESULTS_FILE"
    fi

    # Cleanup
    log_info "$bench_name: Cleaning up..."
    make down > /dev/null 2>&1 || true
    rm -f exploit_output.txt

    cd - > /dev/null
    echo "" >> "$RESULTS_FILE"
}

# Phase 6B Benchmarks by category
echo "========================================"
echo "  Strike7 Phase 6B Test Suite"
echo "========================================"
echo ""

# Authentication (5 benchmarks)
echo "## Authentication Benchmarks (5)" >> "$RESULTS_FILE"
echo ""
log_info "Category: Authentication (5 benchmarks)"
test_benchmark "benchmarks/S7BEN-VHARD-011"
test_benchmark "benchmarks/S7BEN-VHARD-012"
test_benchmark "benchmarks/S7BEN-HARD-014"
test_benchmark "benchmarks/S7BEN-HARD-015"
test_benchmark "benchmarks/S7BEN-MED-013"

# Business Logic (5 benchmarks)
echo "## Business Logic Benchmarks (5)" >> "$RESULTS_FILE"
echo ""
log_info "Category: Business Logic (5 benchmarks)"
test_benchmark "benchmarks/S7BEN-VHARD-013"
test_benchmark "benchmarks/S7BEN-VHARD-014"
test_benchmark "benchmarks/S7BEN-HARD-016"
test_benchmark "benchmarks/S7BEN-HARD-017"
test_benchmark "benchmarks/S7BEN-MED-014"

# Misconfiguration (4 benchmarks)
echo "## Misconfiguration Benchmarks (4)" >> "$RESULTS_FILE"
echo ""
log_info "Category: Misconfiguration (4 benchmarks)"
test_benchmark "benchmarks/S7BEN-HARD-018"
test_benchmark "benchmarks/S7BEN-HARD-019"
test_benchmark "benchmarks/S7BEN-MED-015"
test_benchmark "benchmarks/S7BEN-MED-016"

# CVE Reproductions (6 benchmarks)
echo "## CVE Reproduction Benchmarks (6)" >> "$RESULTS_FILE"
echo ""
log_info "Category: CVE Reproductions (6 benchmarks)"
test_benchmark "benchmarks/S7BEN-CVE-006"
test_benchmark "benchmarks/S7BEN-CVE-007"
test_benchmark "benchmarks/S7BEN-CVE-008"
test_benchmark "benchmarks/S7BEN-CVE-009"
test_benchmark "benchmarks/S7BEN-CVE-010"
test_benchmark "benchmarks/S7BEN-CVE-011"

# Summary
echo ""
echo "========================================"
echo "  Test Summary"
echo "========================================"
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"
echo "Success Rate: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"
echo ""
echo "Full results saved to: $RESULTS_FILE"

# Add summary to results file
cat >> "$RESULTS_FILE" <<EOF

---

## Summary

- **Total Tests:** $TOTAL_TESTS
- **Passed:** $PASSED_TESTS
- **Failed:** $FAILED_TESTS
- **Success Rate:** $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%

**Test completed:** $(date '+%Y-%m-%d %H:%M:%S')
EOF

exit 0
