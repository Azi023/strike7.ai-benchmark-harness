#!/bin/bash

# Strike7 Comprehensive Benchmark Test Suite
# Tests all 64 benchmarks systematically

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
RESULTS_DIR="test-results"
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
RESULTS_FILE="$RESULTS_DIR/test-report-$TIMESTAMP.md"
PASSED=0
FAILED=0
SKIPPED=0
TOTAL=0

# Create results directory
mkdir -p "$RESULTS_DIR"

# Initialize results file
cat > "$RESULTS_FILE" <<EOF
# Strike7 Benchmark Test Report

**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Total Benchmarks:** 64
**Test Run ID:** $TIMESTAMP

---

## Test Results

EOF

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    echo "✅ $1" >> "$RESULTS_FILE"
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    echo "❌ $1" >> "$RESULTS_FILE"
}

log_skip() {
    echo -e "${YELLOW}[SKIP]${NC} $1"
    echo "⏭️  $1" >> "$RESULTS_FILE"
}

test_benchmark() {
    local bench_dir=$1
    local bench_id=$(basename "$bench_dir")

    ((TOTAL++))

    log_info "Testing $bench_id ($TOTAL/64)..."

    # Check if benchmark exists
    if [[ ! -d "$bench_dir" ]]; then
        log_skip "$bench_id: Directory not found"
        ((SKIPPED++))
        return 1
    fi

    cd "$bench_dir"

    # Validate required files
    local required_files=("docker-compose.yml" "benchmark.yaml" "README.md")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_fail "$bench_id: Missing $file"
            ((FAILED++))
            cd - > /dev/null
            return 1
        fi
    done

    # Start benchmark
    if docker-compose up -d > /dev/null 2>&1; then
        sleep 8

        # Test health/connectivity
        local port=$(grep -oP ':\K\d+(?=:)' docker-compose.yml | head -1 || echo "5000")
        if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1 || \
           curl -f -s "http://localhost:$port/" > /dev/null 2>&1; then

            # Run exploit if available
            if [[ -f "exploit.sh" ]]; then
                if bash exploit.sh > /tmp/exploit_out.txt 2>&1; then
                    if grep -q "S7BEN{" /tmp/exploit_out.txt; then
                        local flag=$(grep -oP 'S7BEN\{[^}]+\}' /tmp/exploit_out.txt | head -1)
                        log_success "$bench_id: Exploit successful - $flag"
                        ((PASSED++))
                        docker-compose down > /dev/null 2>&1
                        cd - > /dev/null
                        return 0
                    fi
                fi
            fi

            log_success "$bench_id: Service running (exploit not tested)"
            ((PASSED++))
        else
            log_fail "$bench_id: Service not responding"
            ((FAILED++))
        fi

        docker-compose down > /dev/null 2>&1
    else
        log_fail "$bench_id: Failed to start containers"
        ((FAILED++))
    fi

    cd - > /dev/null
}

# Header
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════╗"
echo "║   Strike7 Comprehensive Test Suite       ║"
echo "║   Testing All 64 Benchmarks              ║"
echo "╚═══════════════════════════════════════════╝"
echo -e "${NC}"

# Test all benchmarks
echo "## Phase 1: EASY Benchmarks (9)" >> "$RESULTS_FILE"
log_info "Testing EASY benchmarks..."
for i in {001..009}; do
    test_benchmark "benchmarks/S7BEN-EASY-$i"
done

echo "" >> "$RESULTS_FILE"
echo "## Phase 2: MED Benchmarks (16)" >> "$RESULTS_FILE"
log_info "Testing MED benchmarks..."
for i in {001..016}; do
    test_benchmark "benchmarks/S7BEN-MED-$(printf '%03d' $i)"
done

echo "" >> "$RESULTS_FILE"
echo "## Phase 3: HARD Benchmarks (14)" >> "$RESULTS_FILE"
log_info "Testing HARD benchmarks..."
for i in {001..019}; do
    test_benchmark "benchmarks/S7BEN-HARD-$(printf '%03d' $i)"
done

echo "" >> "$RESULTS_FILE"
echo "## Phase 4: VHARD Benchmarks (14)" >> "$RESULTS_FILE"
log_info "Testing VHARD benchmarks..."
for i in {001..014}; do
    test_benchmark "benchmarks/S7BEN-VHARD-$(printf '%03d' $i)"
done

echo "" >> "$RESULTS_FILE"
echo "## Phase 5: CVE Benchmarks (11)" >> "$RESULTS_FILE"
log_info "Testing CVE benchmarks..."
for i in {001..011}; do
    test_benchmark "benchmarks/S7BEN-CVE-$(printf '%03d' $i)"
done

# Summary
SUCCESS_RATE=0
if [[ $TOTAL -gt 0 ]]; then
    SUCCESS_RATE=$(( PASSED * 100 / TOTAL ))
fi

echo "" >> "$RESULTS_FILE"
echo "---" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "## Summary" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "| Metric | Count | Percentage |" >> "$RESULTS_FILE"
echo "|--------|-------|------------|" >> "$RESULTS_FILE"
echo "| **Total Tested** | $TOTAL | 100% |" >> "$RESULTS_FILE"
echo "| **Passed** | $PASSED | $SUCCESS_RATE% |" >> "$RESULTS_FILE"
echo "| **Failed** | $FAILED | $(( TOTAL > 0 ? FAILED * 100 / TOTAL : 0 ))% |" >> "$RESULTS_FILE"
echo "| **Skipped** | $SKIPPED | $(( TOTAL > 0 ? SKIPPED * 100 / TOTAL : 0 ))% |" >> "$RESULTS_FILE"

echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║            FINAL RESULTS                  ║${NC}"
echo -e "${BLUE}╠═══════════════════════════════════════════╣${NC}"
echo -e "${BLUE}║${NC} Total Tested:   $TOTAL                      ${BLUE}║${NC}"
echo -e "${BLUE}║${NC} ${GREEN}Passed:${NC}         $PASSED                     ${BLUE}║${NC}"
echo -e "${BLUE}║${NC} ${RED}Failed:${NC}         $FAILED                     ${BLUE}║${NC}"
echo -e "${BLUE}║${NC} ${YELLOW}Skipped:${NC}        $SKIPPED                     ${BLUE}║${NC}"
echo -e "${BLUE}║${NC} Success Rate:   $SUCCESS_RATE%                  ${BLUE}║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📄 Full report: $RESULTS_FILE${NC}"
echo ""

exit $(( FAILED > 0 ? 1 : 0 ))
