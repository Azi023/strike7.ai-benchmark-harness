#!/bin/bash

# Comprehensive Phase 6B Test - Works without make/jq

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Results
RESULTS_FILE="phase6b-test-results.md"
PASSED=0
FAILED=0
TOTAL=0

# Phase 6B benchmarks organized by category
declare -A BENCHMARKS
BENCHMARKS[AUTH]="S7BEN-VHARD-011 S7BEN-VHARD-012 S7BEN-HARD-014 S7BEN-HARD-015 S7BEN-MED-013"
BENCHMARKS[LOGIC]="S7BEN-VHARD-013 S7BEN-VHARD-014 S7BEN-HARD-016 S7BEN-HARD-017 S7BEN-MED-014"
BENCHMARKS[MISCONFIG]="S7BEN-HARD-018 S7BEN-HARD-019 S7BEN-MED-015 S7BEN-MED-016"
BENCHMARKS[CVE]="S7BEN-CVE-006 S7BEN-CVE-007 S7BEN-CVE-008 S7BEN-CVE-009 S7BEN-CVE-010 S7BEN-CVE-011"

# Initialize results
cat > "$RESULTS_FILE" <<EOF
# Phase 6B Benchmark Test Results

**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Environment:** Strike7 Benchmarks v6B
**Total Benchmarks:** 20

---

EOF

log_test() {
    echo -e "$1"
    echo "$2" >> "$RESULTS_FILE"
}

test_benchmark() {
    local bench_id=$1
    local category=$2

    ((TOTAL++))

    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}[$TOTAL/20] Testing: $bench_id${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    local bench_dir="benchmarks/$bench_id"

    if [[ ! -d "$bench_dir" ]]; then
        log_test "${RED}❌ FAIL${NC}: Directory not found" "❌ **$bench_id** - Directory not found"
        ((FAILED++))
        return 1
    fi

    cd "$bench_dir"

    # Validate structure
    echo "  📋 Checking files..."
    local missing=""
    [[ ! -f "docker-compose.yml" ]] && missing="$missing docker-compose.yml"
    [[ ! -f "exploit.sh" ]] && missing="$missing exploit.sh"
    [[ ! -f "benchmark.yaml" ]] && missing="$missing benchmark.yaml"
    [[ ! -f "README.md" ]] && missing="$missing README.md"

    if [[ -n "$missing" ]]; then
        log_test "${RED}❌ FAIL${NC}: Missing files:$missing" "❌ **$bench_id** - Missing:$missing"
        ((FAILED++))
        cd - > /dev/null
        return 1
    fi

    # Start containers
    echo "  🚀 Starting containers..."
    if ! docker-compose up -d > /tmp/docker_start.log 2>&1; then
        log_test "${RED}❌ FAIL${NC}: Container start failed" "❌ **$bench_id** - Container start failed"
        cat /tmp/docker_start.log
        ((FAILED++))
        docker-compose down > /dev/null 2>&1 || true
        cd - > /dev/null
        return 1
    fi

    echo "  ⏳ Waiting for services (10s)..."
    sleep 10

    # Check if containers are running
    if ! docker-compose ps | grep -q "Up"; then
        echo "  ⚠️  Containers may not be healthy"
        docker-compose ps
    fi

    # Run exploit
    echo "  🔓 Running exploit..."
    if bash exploit.sh > /tmp/exploit_output.txt 2>&1; then
        # Look for flag
        if grep -q "S7BEN{" /tmp/exploit_output.txt; then
            local flag=$(grep -oP 'S7BEN\{[^}]+\}' /tmp/exploit_output.txt | head -1)
            log_test "${GREEN}✅ SUCCESS${NC}: Flag captured: $flag" "✅ **$bench_id** - Success! Flag: \`$flag\`"
            ((PASSED++))

            # Cleanup
            echo "  🧹 Cleaning up..."
            docker-compose down > /dev/null 2>&1 || true
            cd - > /dev/null
            return 0
        else
            echo "  ⚠️  Exploit ran but no flag found"
            echo "  Output preview:"
            head -10 /tmp/exploit_output.txt | sed 's/^/    /'
        fi
    else
        echo "  ⚠️  Exploit script failed"
        echo "  Error preview:"
        head -10 /tmp/exploit_output.txt | sed 's/^/    /'
    fi

    log_test "${RED}❌ FAIL${NC}: No flag captured" "❌ **$bench_id** - Exploit failed (see logs)"
    ((FAILED++))

    # Cleanup
    echo "  🧹 Cleaning up..."
    docker-compose down > /dev/null 2>&1 || true
    cd - > /dev/null
    return 1
}

# Header
echo -e "${BLUE}"
echo "╔════════════════════════════════════════╗"
echo "║  Strike7 Phase 6B Test Suite          ║"
echo "║  Testing 20 Benchmarks                 ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"

# Test each category
for category in AUTH LOGIC MISCONFIG CVE; do
    case $category in
        AUTH) cat_name="Authentication" ;;
        LOGIC) cat_name="Business Logic" ;;
        MISCONFIG) cat_name="Misconfiguration" ;;
        CVE) cat_name="CVE Reproductions" ;;
    esac

    echo "" >> "$RESULTS_FILE"
    echo "## $cat_name" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"

    echo ""
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${YELLOW}  Category: $cat_name${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"

    for bench in ${BENCHMARKS[$category]}; do
        test_benchmark "$bench" "$category"
        sleep 2  # Brief pause between tests
    done
done

# Summary
echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           FINAL RESULTS                ║${NC}"
echo -e "${BLUE}╠════════════════════════════════════════╣${NC}"
echo -e "${BLUE}║${NC} Total Tests:    $TOTAL/20                  ${BLUE}║${NC}"
echo -e "${BLUE}║${NC} ${GREEN}Passed:${NC}         $PASSED                    ${BLUE}║${NC}"
echo -e "${BLUE}║${NC} ${RED}Failed:${NC}         $FAILED                    ${BLUE}║${NC}"
echo -e "${BLUE}║${NC} Success Rate:   $(( TOTAL > 0 ? PASSED * 100 / TOTAL : 0 ))%                  ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

# Add summary to report
cat >> "$RESULTS_FILE" <<EOF

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Benchmarks** | $TOTAL |
| **Passed** | $PASSED ✅ |
| **Failed** | $FAILED ❌ |
| **Success Rate** | $(( TOTAL > 0 ? PASSED * 100 / TOTAL : 0 ))% |

**Test Completed:** $(date '+%Y-%m-%d %H:%M:%S')

---

## Next Steps

EOF

if [[ $FAILED -gt 0 ]]; then
    echo "⚠️  Some benchmarks failed. Check the logs above for details." >> "$RESULTS_FILE"
    echo ""
    echo -e "${YELLOW}⚠️  Some tests failed. See $RESULTS_FILE for details.${NC}"
else
    echo "🎉 All Phase 6B benchmarks passed successfully!" >> "$RESULTS_FILE"
    echo ""
    echo -e "${GREEN}🎉 All tests passed!${NC}"
fi

echo ""
echo -e "📄 Full results saved to: ${BLUE}$RESULTS_FILE${NC}"
echo ""

exit $(( FAILED > 0 ? 1 : 0 ))
