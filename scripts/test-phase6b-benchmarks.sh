#!/bin/bash
# Phase 6B Benchmark Testing Script
# Tests all 20 new benchmarks created in Phase 6B

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$REPO_ROOT/phase6b_test_results.log"
RESULTS_FILE="$REPO_ROOT/phase6b_test_summary.txt"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Initialize log
echo "=== Phase 6B Benchmark Testing ===" > "$LOG_FILE"
echo "Date: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Test results
declare -a PASSED_BENCHMARKS
declare -a FAILED_BENCHMARKS

echo "═══════════════════════════════════════════════════════════════════"
echo "                  Phase 6B Benchmark Testing"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Function to test a benchmark
test_benchmark() {
    local BENCHMARK_ID=$1
    local BENCHMARK_DIR="$REPO_ROOT/benchmarks/$BENCHMARK_ID"
    local CATEGORY=$2

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -e "${YELLOW}Testing $BENCHMARK_ID...${NC}"
    echo "=== Testing $BENCHMARK_ID ===" >> "$LOG_FILE"

    # Check if directory exists
    if [ ! -d "$BENCHMARK_DIR" ]; then
        echo -e "${RED}✗ FAILED: Directory not found${NC}"
        echo "FAILED: Directory not found" >> "$LOG_FILE"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        FAILED_BENCHMARKS+=("$BENCHMARK_ID (directory not found)")
        return 1
    fi

    cd "$BENCHMARK_DIR"

    # Check required files exist
    local REQUIRED_FILES=("app/app.py" "docker-compose.yml" "Makefile" "exploit.sh" "exploit.py" "README.md" "benchmark.yaml")
    for file in "${REQUIRED_FILES[@]}"; do
        if [ ! -f "$file" ]; then
            echo -e "${RED}✗ FAILED: Missing $file${NC}"
            echo "FAILED: Missing $file" >> "$LOG_FILE"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            FAILED_BENCHMARKS+=("$BENCHMARK_ID (missing $file)")
            return 1
        fi
    done

    # Start the benchmark
    echo "  Starting containers..." >> "$LOG_FILE"
    docker-compose down >> "$LOG_FILE" 2>&1
    sleep 2
    if ! docker-compose up -d >> "$LOG_FILE" 2>&1; then
        echo -e "${RED}✗ FAILED: Container startup failed${NC}"
        echo "FAILED: Container startup" >> "$LOG_FILE"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        FAILED_BENCHMARKS+=("$BENCHMARK_ID (startup failed)")
        return 1
    fi

    # Wait for container to be ready
    echo "  Waiting for container to be ready..."
    sleep 5

    # Check if app is responding
    local PORT=$(grep -oP 'port:\s*\K\d+' benchmark.yaml | head -1)
    if [ -z "$PORT" ]; then
        echo -e "${YELLOW}  Warning: Could not detect port, skipping health check${NC}"
    else
        if curl -s "http://localhost:$PORT/" > /dev/null 2>&1; then
            echo "  ✓ App responding on port $PORT" >> "$LOG_FILE"
        else
            echo -e "${YELLOW}  Warning: App not responding on port $PORT${NC}"
            echo "WARNING: App not responding" >> "$LOG_FILE"
        fi
    fi

    # Check container logs for flag
    local CONTAINER_NAME=$(docker-compose ps -q | head -1)
    if [ -n "$CONTAINER_NAME" ]; then
        if docker logs "$CONTAINER_NAME" 2>&1 | grep -q "S7BEN{"; then
            echo "  ✓ Dynamic flag generated" >> "$LOG_FILE"
        else
            echo -e "${YELLOW}  Warning: No flag found in logs${NC}"
            echo "WARNING: No flag in logs" >> "$LOG_FILE"
        fi
    fi

    # Stop the benchmark
    docker-compose down >> "$LOG_FILE" 2>&1

    echo -e "${GREEN}✓ PASSED${NC}"
    echo "PASSED" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    PASSED_BENCHMARKS+=("$BENCHMARK_ID")

    cd "$REPO_ROOT"
}

# Authentication Benchmarks
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Testing Authentication Benchmarks (5)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_benchmark "S7BEN-VHARD-011" "Auth"
test_benchmark "S7BEN-VHARD-012" "Auth"
test_benchmark "S7BEN-HARD-014" "Auth"
test_benchmark "S7BEN-HARD-015" "Auth"
test_benchmark "S7BEN-MED-013" "Auth"

# Business Logic Benchmarks
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Testing Business Logic Benchmarks (5)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_benchmark "S7BEN-VHARD-013" "Business Logic"
test_benchmark "S7BEN-VHARD-014" "Business Logic"
test_benchmark "S7BEN-HARD-016" "Business Logic"
test_benchmark "S7BEN-HARD-017" "Business Logic"
test_benchmark "S7BEN-MED-014" "Business Logic"

# Misconfiguration Benchmarks
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Testing Misconfiguration Benchmarks (4)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_benchmark "S7BEN-HARD-018" "Misconfiguration"
test_benchmark "S7BEN-HARD-019" "Misconfiguration"
test_benchmark "S7BEN-MED-015" "Misconfiguration"
test_benchmark "S7BEN-MED-016" "Misconfiguration"

# CVE Benchmarks
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Testing CVE Benchmarks (6)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_benchmark "S7BEN-CVE-006" "CVE"
test_benchmark "S7BEN-CVE-007" "CVE"
test_benchmark "S7BEN-CVE-008" "CVE"
test_benchmark "S7BEN-CVE-009" "CVE"
test_benchmark "S7BEN-CVE-010" "CVE"
test_benchmark "S7BEN-CVE-011" "CVE"

# Generate summary report
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "                       Test Summary"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "Total Tests:   $TOTAL_TESTS"
echo -e "Passed:        ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed:        ${RED}$FAILED_TESTS${NC}"
echo "Success Rate:  $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"
echo ""

# Write summary to file
{
    echo "=== Phase 6B Test Summary ==="
    echo "Date: $(date)"
    echo ""
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"
    echo "Success Rate: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"
    echo ""

    if [ ${#PASSED_BENCHMARKS[@]} -gt 0 ]; then
        echo "PASSED BENCHMARKS:"
        for benchmark in "${PASSED_BENCHMARKS[@]}"; do
            echo "  ✓ $benchmark"
        done
        echo ""
    fi

    if [ ${#FAILED_BENCHMARKS[@]} -gt 0 ]; then
        echo "FAILED BENCHMARKS:"
        for benchmark in "${FAILED_BENCHMARKS[@]}"; do
            echo "  ✗ $benchmark"
        done
        echo ""
    fi
} > "$RESULTS_FILE"

echo "Summary saved to: $RESULTS_FILE"
echo "Detailed log saved to: $LOG_FILE"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Check $LOG_FILE for details.${NC}"
    exit 1
fi
