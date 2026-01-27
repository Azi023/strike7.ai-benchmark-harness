#!/bin/bash
# cleanup-scattered-files.sh
# Deletes redundant documentation and test files from repository root
# Based on Phase 6 Plan Part A

# Determine the repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT" || {
    echo "Error: Could not change to repository root"
    exit 1
}

echo "=== Strike7 Benchmarks - Cleanup Scattered Files ==="
echo "Repository: $REPO_ROOT"
echo "Date: $(date +%Y-%m-%d)"
echo ""

# List of redundant/scattered files to remove
FILES_TO_DELETE=(
    "ALL_FIXES_COMPLETE.md"
    "ALL_ISSUES_RESOLVED.md"
    "BENCHMARKS_COMPLETED.md"
    "BENCHMARK_SCAFFOLDS_SUMMARY.md"
    "FINAL_FIXES_APPLIED.md"
    "FINAL_FIXES_COMPLETE.md"
    "FIXED_AND_READY.md"
    "ISSUES_FIXED_SUMMARY.md"
    "PHASE5_FINAL_STATUS.md"
    "PHASE5_FIXES_FINAL.md"
    "PHASE5_SETUP_COMMANDS.md"
    "REMAINING_ISSUES_SUMMARY.md"
    "SBEN-CVE-01_FIX.md"
    "READY_TO_TEST.md"
    "VERIFY_FIXES.sh"
    "REBUILD_AND_TEST.sh"
    "REBUILD_CVE03.sh"
    "FIX_CVE03_FINAL.sh"
    "FIX_HARD04.sh"
    "TEST_FINAL_TWO.sh"
    "TEST_HARD04_FINAL.sh"
    "TEST_HARD04_MANUAL.sh"
)

echo "=== Files to be deleted ==="
existing_count=0
for file in "${FILES_TO_DELETE[@]}"; do
    if [ -f "$file" ]; then
        echo "  [EXISTS] $file"
        ((existing_count++))
    else
        echo "  [MISSING] $file (already deleted)"
    fi
done

echo ""
echo "Total files to delete: $existing_count"
echo ""

if [ $existing_count -eq 0 ]; then
    echo "No files to delete. Cleanup already complete!"
    exit 0
fi

read -p "Delete these $existing_count files? (y/n): " confirm
if [ "$confirm" == "y" ] || [ "$confirm" == "Y" ]; then
    deleted_count=0
    for file in "${FILES_TO_DELETE[@]}"; do
        if [ -f "$file" ]; then
            rm -f "$file"
            echo "  [DELETED] $file"
            ((deleted_count++))
        fi
    done
    echo ""
    echo "==================================="
    echo "Cleanup complete!"
    echo "Deleted: $deleted_count files"
    echo "==================================="
else
    echo "Cleanup cancelled by user."
    exit 1
fi
