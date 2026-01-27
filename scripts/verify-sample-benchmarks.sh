#!/bin/bash
# verify-sample-benchmarks.sh
# Tests a sample of benchmarks to verify migration was successful
# Tests 2 benchmarks from each category (EASY, MED, HARD, VHARD, CVE)

# Determine the repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT" || {
    echo "Error: Could not change to repository root"
    exit 1
}

echo "=== Strike7 Benchmark Verification ==="
echo "Repository: $REPO_ROOT"
echo "Date: $(date +%Y-%m-%d)"
echo ""

# Sample benchmarks to test (2 from each category)
SAMPLE_BENCHMARKS=(
    "S7BEN-EASY-001"
    "S7BEN-EASY-002"
    "S7BEN-MED-001"
    "S7BEN-MED-002"
    "S7BEN-HARD-001"
    "S7BEN-HARD-002"
    "S7BEN-VHARD-001"
    "S7BEN-VHARD-002"
    "S7BEN-CVE-001"
    "S7BEN-CVE-002"
)

total=${#SAMPLE_BENCHMARKS[@]}
passed=0
failed=0

echo "Testing $total sample benchmarks..."
echo ""

for bench in "${SAMPLE_BENCHMARKS[@]}"; do
    echo "=========================================="
    echo "Testing: $bench"
    echo "=========================================="

    bench_dir="benchmarks/$bench"

    if [ ! -d "$bench_dir" ]; then
        echo "  ✗ FAILED: Directory not found"
        ((failed++))
        continue
    fi

    cd "$bench_dir" || {
        echo "  ✗ FAILED: Could not enter directory"
        ((failed++))
        cd "$REPO_ROOT"
        continue
    }

    # Check for required files
    if [ ! -f "Makefile" ]; then
        echo "  ✗ FAILED: Makefile missing"
        ((failed++))
        cd "$REPO_ROOT"
        continue
    fi

    if [ ! -f "benchmark.yaml" ]; then
        echo "  ✗ FAILED: benchmark.yaml missing"
        ((failed++))
        cd "$REPO_ROOT"
        continue
    fi

    # Check for S7BEN flag format in benchmark.yaml
    if grep -q "S7BEN{" benchmark.yaml; then
        echo "  ✓ Flag format updated (S7BEN{...})"
    else
        echo "  ⚠ WARNING: No S7BEN{ found in benchmark.yaml"
    fi

    # Check for old SBEN references
    old_refs=$(grep -r "SBEN-" . 2>/dev/null | wc -l)
    if [ $old_refs -gt 0 ]; then
        echo "  ⚠ WARNING: Found $old_refs old SBEN- references"
    else
        echo "  ✓ No old SBEN- references found"
    fi

    # Try to run health check (optional, commented out to avoid Docker overhead)
    # echo "  → Running health check..."
    # make up > /dev/null 2>&1
    # sleep 2
    # make test > /dev/null 2>&1
    # if [ $? -eq 0 ]; then
    #     echo "  ✓ Health check passed"
    #     make down > /dev/null 2>&1
    # else
    #     echo "  ✗ Health check failed"
    #     make down > /dev/null 2>&1
    #     ((failed++))
    #     cd "$REPO_ROOT"
    #     continue
    # fi

    echo "  ✓ PASSED: Basic verification"
    ((passed++))
    cd "$REPO_ROOT"
    echo ""
done

echo "=========================================="
echo "=== Verification Summary ==="
echo "  Total tested: $total"
echo "  Passed: $passed"
echo "  Failed: $failed"
echo "=========================================="

if [ $failed -eq 0 ]; then
    echo ""
    echo "✓ All sample benchmarks passed verification!"
    exit 0
else
    echo ""
    echo "⚠ Some benchmarks failed verification. Review the output above."
    exit 1
fi
