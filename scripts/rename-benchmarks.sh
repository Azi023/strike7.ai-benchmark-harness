#!/bin/bash
# rename-benchmarks.sh
# Renames all benchmarks from SBEN-* to S7BEN-* format
# Based on Phase 6 Plan Part B

# Determine the repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT/benchmarks" || {
    echo "Error: Could not change to benchmarks directory"
    exit 1
}

echo "=== Strike7 Benchmark Renaming ==="
echo "Repository: $REPO_ROOT"
echo "Date: $(date +%Y-%m-%d)"
echo ""

# Complete renaming map based on Phase 6 plan
declare -A RENAME_MAP=(
    # Phase 1 - Easy (SBEN-X00-0X → S7BEN-EASY-XXX)
    ["SBEN-100-01"]="S7BEN-EASY-001"   # CSRF
    ["SBEN-200-01"]="S7BEN-EASY-002"   # Hardcoded Secrets
    ["SBEN-400-01"]="S7BEN-EASY-003"   # Race Condition
    ["SBEN-400-02"]="S7BEN-EASY-004"   # Workflow Bypass
    ["SBEN-900-01"]="S7BEN-EASY-005"   # Insufficient Logging
    ["SBEN-900-02"]="S7BEN-EASY-006"   # Log Injection

    # Phase 2 - Medium
    ["SBEN-700-01"]="S7BEN-MED-001"    # Session Fixation
    ["SBEN-400-03"]="S7BEN-MED-002"    # TOCTOU

    # Phase 3 - Tiered (T2=MED, T3=HARD)
    ["SBEN-510-T2"]="S7BEN-MED-003"    # SQLi Evaluation
    ["SBEN-520-T2"]="S7BEN-MED-004"    # XSS Evaluation
    ["SBEN-110-T2"]="S7BEN-MED-005"    # IDOR Evaluation
    ["SBEN-910-T2"]="S7BEN-MED-006"    # Log Chain Evaluation
    ["SBEN-510-T3"]="S7BEN-HARD-010"   # SQLi Adversarial
    ["SBEN-520-T3"]="S7BEN-HARD-011"   # XSS+CSP Adversarial
    ["SBEN-110-T3"]="S7BEN-HARD-012"   # IDOR Adversarial
    ["SBEN-910-T3"]="S7BEN-HARD-013"   # Log Chain Adversarial

    # Phase 4 - Very Hard (Multi-container chains)
    ["SBEN-CHAIN-01"]="S7BEN-VHARD-001"   # Microservices Chain
    ["SBEN-SSRF-01"]="S7BEN-VHARD-002"    # Advanced SSRF
    ["SBEN-AD-01"]="S7BEN-VHARD-003"      # Active Directory
    ["SBEN-DESER-01"]="S7BEN-VHARD-004"   # Java Deserialization
    ["SBEN-DESER-02"]="S7BEN-VHARD-005"   # Python Pickle
    ["SBEN-GQL-01"]="S7BEN-VHARD-006"     # GraphQL SQLi
    ["SBEN-XXE-01"]="S7BEN-VHARD-007"     # XXE Exfiltration
    ["SBEN-NOSQL-01"]="S7BEN-VHARD-008"   # MongoDB Injection
    ["SBEN-SSTI-01"]="S7BEN-VHARD-009"    # Template Injection
    ["SBEN-LFI-01"]="S7BEN-VHARD-010"     # LFI to RCE

    # Phase 5 - Hard + CVE
    ["SBEN-HARD-01"]="S7BEN-HARD-001"     # SQLi + ModSecurity
    ["SBEN-HARD-02"]="S7BEN-HARD-002"     # XSS + DOMPurify
    ["SBEN-HARD-03"]="S7BEN-HARD-003"     # SSRF + Filtering
    ["SBEN-HARD-04"]="S7BEN-HARD-004"     # JWT Auth Bypass
    ["SBEN-CVE-01"]="S7BEN-CVE-001"       # Apache Path Traversal
    ["SBEN-CVE-02"]="S7BEN-CVE-002"       # Text4Shell
    ["SBEN-CVE-03"]="S7BEN-CVE-003"       # Log4Shell
    ["SBEN-CVE-04"]="S7BEN-CVE-004"       # Spring4Shell
    ["SBEN-CVE-05"]="S7BEN-CVE-005"       # GitLab RCE

    # Additional benchmarks found (numbered series)
    ["SBEN-900-03"]="S7BEN-EASY-007"      # Additional logging
    ["SBEN-700-02"]="S7BEN-MED-007"       # Additional session
    ["SBEN-700-25"]="S7BEN-MED-008"       # Additional session variant
    ["SBEN-500-01"]="S7BEN-MED-009"       # Security Misconfiguration
    ["SBEN-1000-01"]="S7BEN-MED-010"      # SSRF basic
    ["SBEN-1010-T1"]="S7BEN-EASY-008"     # Multi-stage auth basic
    ["SBEN-1010-T2"]="S7BEN-MED-011"      # Multi-stage auth eval
    ["SBEN-300-T1"]="S7BEN-EASY-009"      # Supply chain basic
    ["SBEN-300-T2"]="S7BEN-MED-012"       # Supply chain eval
)

# Preview renames
echo "=== Preview of Renames ==="
echo ""
rename_count=0
missing_count=0

for old in "${!RENAME_MAP[@]}"; do
    new="${RENAME_MAP[$old]}"
    if [ -d "$old" ]; then
        echo "  ✓ $old → $new"
        ((rename_count++))
    else
        echo "  ✗ $old → $new (DIRECTORY NOT FOUND)"
        ((missing_count++))
    fi
done | sort

echo ""
echo "Summary:"
echo "  Directories to rename: $rename_count"
echo "  Missing directories: $missing_count"
echo ""

# Check for unmapped benchmarks
echo "=== Checking for Unmapped Benchmarks ==="
unmapped_count=0
for dir in SBEN-*; do
    if [ -d "$dir" ] && [ ! -v "RENAME_MAP[$dir]" ]; then
        echo "  ⚠ UNMAPPED: $dir"
        ((unmapped_count++))
    fi
done

if [ $unmapped_count -eq 0 ]; then
    echo "  ✓ All SBEN-* benchmarks are mapped"
else
    echo ""
    echo "  WARNING: $unmapped_count unmapped benchmarks found!"
    echo "  These will NOT be renamed. Update the script to include them."
fi

echo ""
echo "=========================================="

# Confirmation prompt
read -p "Proceed with renaming $rename_count benchmarks? (y/n): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Renaming cancelled by user."
    exit 1
fi

echo ""
echo "=== Starting Rename Operation ==="
echo ""

# Perform renames
success_count=0
fail_count=0

for old in "${!RENAME_MAP[@]}"; do
    new="${RENAME_MAP[$old]}"

    if [ ! -d "$old" ]; then
        echo "  ✗ SKIP: $old (not found)"
        ((fail_count++))
        continue
    fi

    if [ -d "$new" ]; then
        echo "  ✗ SKIP: $old → $new (target already exists)"
        ((fail_count++))
        continue
    fi

    # Rename directory
    mv "$old" "$new"
    if [ $? -eq 0 ]; then
        echo "  ✓ RENAMED: $old → $new"
        ((success_count++))

        # Update internal references in the renamed directory
        # Target files: *.yaml, *.yml, *.py, *.md, *.sh, *.env, *.json, *.txt
        find "$new" -type f \( \
            -name "*.yaml" -o \
            -name "*.yml" -o \
            -name "*.py" -o \
            -name "*.md" -o \
            -name "*.sh" -o \
            -name "*.env" -o \
            -name "*.json" -o \
            -name "*.txt" \
        \) -exec sed -i "s/$old/$new/g" {} \; 2>/dev/null

    else
        echo "  ✗ FAILED: $old → $new"
        ((fail_count++))
    fi
done | sort

echo ""
echo "=========================================="
echo "=== Rename Operation Complete ==="
echo "  Successful: $success_count"
echo "  Failed: $fail_count"
echo "=========================================="
echo ""

# Final verification
new_count=$(ls -d S7BEN-* 2>/dev/null | wc -l)
old_count=$(ls -d SBEN-* 2>/dev/null | wc -l)

echo "Final Benchmark Count:"
echo "  S7BEN-* (new naming): $new_count"
echo "  SBEN-* (old naming): $old_count"
echo ""

if [ $old_count -eq 0 ]; then
    echo "✓ Migration complete! All benchmarks renamed to S7BEN-* format."
else
    echo "⚠ Warning: $old_count benchmarks still use SBEN-* naming."
    echo "  Run the script again or check for unmapped benchmarks."
fi
