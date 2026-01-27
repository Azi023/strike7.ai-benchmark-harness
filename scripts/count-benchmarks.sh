#!/bin/bash
# count-benchmarks.sh
# Counts all benchmarks in the repository and categorizes them
# Run from ~/workspace/strike7-benchmarks/

# Determine the repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT/benchmarks" 2>/dev/null || {
    echo "Error: benchmarks directory not found at $REPO_ROOT/benchmarks"
    exit 1
}

echo "=== Strike7 Benchmark Inventory ==="
echo "Date: $(date +%Y-%m-%d)"
echo ""

# Count old naming (SBEN-*)
old_sben=$(ls -d SBEN-* 2>/dev/null | wc -l)

# Count new naming (S7BEN-*)
easy=$(ls -d S7BEN-EASY-* 2>/dev/null | wc -l)
med=$(ls -d S7BEN-MED-* 2>/dev/null | wc -l)
hard=$(ls -d S7BEN-HARD-* 2>/dev/null | wc -l)
vhard=$(ls -d S7BEN-VHARD-* 2>/dev/null | wc -l)
cve=$(ls -d S7BEN-CVE-* 2>/dev/null | wc -l)

new_total=$((easy + med + hard + vhard + cve))

echo "Current Naming (SBEN-*):"
echo "  Total SBEN benchmarks: $old_sben"
echo ""

if [ $new_total -gt 0 ]; then
    echo "New Naming (S7BEN-*):"
    echo "  EASY:  $easy"
    echo "  MED:   $med"
    echo "  HARD:  $hard"
    echo "  VHARD: $vhard"
    echo "  CVE:   $cve"
    echo "  ---------------"
    echo "  Total: $new_total"
    echo ""
fi

grand_total=$((old_sben + new_total))
echo "Grand Total: $grand_total benchmarks"
echo ""

# Category breakdown for SBEN-* naming
if [ $old_sben -gt 0 ]; then
    echo "SBEN-* Category Breakdown:"
    cve_count=$(ls -d SBEN-CVE-* 2>/dev/null | wc -l)
    hard_count=$(ls -d SBEN-HARD-* 2>/dev/null | wc -l)
    numbered_count=$(ls -d SBEN-[0-9]* 2>/dev/null | wc -l)
    chain_count=$(ls -d SBEN-CHAIN-01 2>/dev/null | wc -l)
    ssrf_count=$(ls -d SBEN-SSRF-01 2>/dev/null | wc -l)
    ad_count=$(ls -d SBEN-AD-01 2>/dev/null | wc -l)
    deser_count=$(ls -d SBEN-DESER-* 2>/dev/null | wc -l)
    gql_count=$(ls -d SBEN-GQL-01 2>/dev/null | wc -l)
    xxe_count=$(ls -d SBEN-XXE-01 2>/dev/null | wc -l)
    nosql_count=$(ls -d SBEN-NOSQL-01 2>/dev/null | wc -l)
    ssti_count=$(ls -d SBEN-SSTI-01 2>/dev/null | wc -l)
    lfi_count=$(ls -d SBEN-LFI-01 2>/dev/null | wc -l)
    named_total=$((chain_count + ssrf_count + ad_count + deser_count + gql_count + xxe_count + nosql_count + ssti_count + lfi_count))

    echo "  CVE series:         $cve_count"
    echo "  HARD series:        $hard_count"
    echo "  Numbered (100-999): $numbered_count"
    echo "  Named chains:       $named_total"
    echo ""
fi

# Target gap calculation
target=108
gap=$((target - grand_total))
echo "Target: $target benchmarks (XBOW match)"
echo "Gap: $gap more benchmarks needed"
echo ""

# List all benchmarks
echo "=== Complete Benchmark List ==="
ls -d SBEN-* S7BEN-* 2>/dev/null | sort | nl
