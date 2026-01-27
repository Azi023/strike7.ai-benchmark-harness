#!/bin/bash

# Quick Phase 6B Test - Tests one benchmark at a time with progress
# Usage: ./quick-test-phase6b.sh [benchmark_id]
# Example: ./quick-test-phase6b.sh S7BEN-MED-014
# Or: ./quick-test-phase6b.sh all

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Phase 6B benchmarks
BENCHMARKS=(
    "S7BEN-VHARD-011"
    "S7BEN-VHARD-012"
    "S7BEN-HARD-014"
    "S7BEN-HARD-015"
    "S7BEN-MED-013"
    "S7BEN-VHARD-013"
    "S7BEN-VHARD-014"
    "S7BEN-HARD-016"
    "S7BEN-HARD-017"
    "S7BEN-MED-014"
    "S7BEN-HARD-018"
    "S7BEN-HARD-019"
    "S7BEN-MED-015"
    "S7BEN-MED-016"
    "S7BEN-CVE-006"
    "S7BEN-CVE-007"
    "S7BEN-CVE-008"
    "S7BEN-CVE-009"
    "S7BEN-CVE-010"
    "S7BEN-CVE-011"
)

test_single_benchmark() {
    local bench_id=$1
    local bench_dir="benchmarks/$bench_id"

    echo -e "\n${YELLOW}Testing $bench_id...${NC}"

    if [[ ! -d "$bench_dir" ]]; then
        echo -e "${RED}❌ Directory not found: $bench_dir${NC}"
        return 1
    fi

    cd "$bench_dir"

    # Check files
    if [[ ! -f "docker-compose.yml" ]] || [[ ! -f "exploit.sh" ]]; then
        echo -e "${RED}❌ Missing required files${NC}"
        cd - > /dev/null
        return 1
    fi

    # Start
    echo "  Starting containers..."
    if ! make up > /dev/null 2>&1; then
        echo -e "${RED}❌ Failed to start${NC}"
        make down > /dev/null 2>&1 || true
        cd - > /dev/null
        return 1
    fi

    sleep 8

    # Run exploit
    echo "  Running exploit..."
    if bash exploit.sh > /tmp/exploit_out.txt 2>&1; then
        if grep -q "S7BEN{" /tmp/exploit_out.txt; then
            local flag=$(grep -oP 'S7BEN\{[^}]+\}' /tmp/exploit_out.txt | head -1)
            echo -e "${GREEN}✅ SUCCESS - Flag: $flag${NC}"
            make down > /dev/null 2>&1 || true
            cd - > /dev/null
            return 0
        fi
    fi

    echo -e "${RED}❌ Exploit failed${NC}"
    echo "Output: $(head -20 /tmp/exploit_out.txt)"
    make down > /dev/null 2>&1 || true
    cd - > /dev/null
    return 1
}

if [[ "$1" == "all" ]] || [[ -z "$1" ]]; then
    echo "Testing all 20 Phase 6B benchmarks..."
    PASSED=0
    FAILED=0

    for bench in "${BENCHMARKS[@]}"; do
        if test_single_benchmark "$bench"; then
            ((PASSED++))
        else
            ((FAILED++))
        fi
    done

    echo ""
    echo "================================"
    echo "Summary: $PASSED passed, $FAILED failed out of 20"
    echo "================================"
else
    test_single_benchmark "$1"
fi
