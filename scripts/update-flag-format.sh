#!/bin/bash
# update-flag-format.sh
# Updates all flag formats from SBEN{ to S7BEN{
# Based on Phase 6 Plan Part B3

# Determine the repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Parse arguments
BACKUP=false
if [ "$1" == "--backup" ]; then
    BACKUP=true
fi

cd "$REPO_ROOT" || {
    echo "Error: Could not change to repository root"
    exit 1
}

echo "=== Strike7 Flag Format Update ==="
echo "Repository: $REPO_ROOT"
echo "Date: $(date +%Y-%m-%d)"
echo "Backup: $BACKUP"
echo ""

# Create backup if requested
if [ "$BACKUP" == true ]; then
    backup_file="benchmarks-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    echo "Creating backup: $backup_file"
    tar -czf "$backup_file" benchmarks/
    if [ $? -eq 0 ]; then
        echo "  ✓ Backup created: $backup_file"
    else
        echo "  ✗ Backup failed!"
        exit 1
    fi
    echo ""
fi

# Find all files with SBEN{ references
echo "=== Searching for SBEN{ references ==="
echo ""

file_count=$(grep -r "SBEN{" benchmarks/ \
    --include="*.py" \
    --include="*.yaml" \
    --include="*.yml" \
    --include="*.md" \
    --include="*.sh" \
    --include="*.env" \
    --include="*.json" \
    --include="*.txt" \
    2>/dev/null | wc -l)

if [ $file_count -eq 0 ]; then
    echo "  ✓ No SBEN{ references found. Flag format already updated!"
    exit 0
fi

echo "Found $file_count lines with SBEN{ references"
echo ""

# Show sample matches (first 10)
echo "Sample matches:"
grep -r "SBEN{" benchmarks/ \
    --include="*.py" \
    --include="*.yaml" \
    --include="*.yml" \
    --include="*.md" \
    --include="*.sh" \
    --include="*.env" \
    --include="*.json" \
    --include="*.txt" \
    2>/dev/null | head -10

echo ""
echo "=========================================="

# Confirmation
read -p "Replace all SBEN{ with S7BEN{ in these files? (y/n): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Update cancelled by user."
    exit 1
fi

echo ""
echo "=== Updating Flag Format ==="
echo ""

# Perform replacement
files_modified=0

find benchmarks/ -type f \( \
    -name "*.py" -o \
    -name "*.yaml" -o \
    -name "*.yml" -o \
    -name "*.md" -o \
    -name "*.sh" -o \
    -name "*.env" -o \
    -name "*.json" -o \
    -name "*.txt" \
\) | while read -r file; do
    if grep -q "SBEN{" "$file" 2>/dev/null; then
        sed -i 's/SBEN{/S7BEN{/g' "$file"
        if [ $? -eq 0 ]; then
            echo "  ✓ Updated: $file"
            ((files_modified++))
        else
            echo "  ✗ Failed: $file"
        fi
    fi
done

echo ""
echo "=========================================="

# Verification
remaining=$(grep -r "SBEN{" benchmarks/ \
    --include="*.py" \
    --include="*.yaml" \
    --include="*.yml" \
    --include="*.md" \
    --include="*.sh" \
    --include="*.env" \
    --include="*.json" \
    --include="*.txt" \
    2>/dev/null | wc -l)

new_format=$(grep -r "S7BEN{" benchmarks/ \
    --include="*.py" \
    --include="*.yaml" \
    --include="*.yml" \
    --include="*.md" \
    --include="*.sh" \
    --include="*.env" \
    --include="*.json" \
    --include="*.txt" \
    2>/dev/null | wc -l)

echo ""
echo "=== Update Complete ==="
echo "  S7BEN{ references: $new_format"
echo "  SBEN{ remaining: $remaining"
echo ""

if [ $remaining -eq 0 ]; then
    echo "✓ Flag format successfully updated to S7BEN{...}"
else
    echo "⚠ Warning: $remaining SBEN{ references still found."
    echo "  Run: grep -r \"SBEN{\" benchmarks/ to locate them"
fi

echo ""
echo "Usage: grep -r 'S7BEN{' benchmarks/ | head -5"
