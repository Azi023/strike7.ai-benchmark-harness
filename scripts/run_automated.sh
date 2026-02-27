#!/bin/bash
# ==============================================================================
# run_automated.sh — Fully automated benchmark comparison run
#
# Launches a CLI agent in headless mode, captures JSON output, parses metrics,
# and records the run to the comparison database. No manual data entry needed.
#
# Usage:
#   ./scripts/run_automated.sh <benchmark_id> <provider> <model_name> [options]
#
# Examples:
#   ./scripts/run_automated.sh S7BEN-EASY-001 google gemini-2.5-flash
#   ./scripts/run_automated.sh S7BEN-HARD-023 anthropic claude-sonnet-4.5 --attempt 2
#   ./scripts/run_automated.sh S7BEN-MED-020 openai gpt-4.1 --quiet
#   ./scripts/run_automated.sh S7BEN-EASY-001 google gemini-2.5-flash --dry-run
#
# Options:
#   --attempt N     Attempt number for pass@k tracking (default: 1)
#   --quiet         Only output final JSON result (for piping to jq)
#   --dry-run       Show the CLI command without executing
#   --notes "..."   Attach notes to the run record
#
# Environment:
#   STRIKE7_URL  — Dashboard API URL (default: http://localhost:5500)
#
# Configuration:
#   CLI commands & flags: dashboard/utils/provider_config.py
#   Tier timeouts:        dashboard/utils/provider_config.py (TIER_TIMEOUTS)
#   Model pricing:        DB table benchmark_models (via init_comparison_db.py)
#   Prompt templates:     prompts/*.md
# ==============================================================================

set -euo pipefail

# --- Argument parsing ---
BENCHMARK_ID="${1:?Usage: $0 <benchmark_id> <provider> <model_name> [options]}"
PROVIDER="${2:?Missing provider (google, anthropic, openai)}"
MODEL_NAME="${3:?Missing model_name (e.g., gemini-2.5-flash)}"

ATTEMPT=1
QUIET=false
DRY_RUN=false
NOTES=""

shift 3 2>/dev/null || shift $# 2>/dev/null
while [[ $# -gt 0 ]]; do
    case "$1" in
        --attempt)   ATTEMPT="$2"; shift 2 ;;
        --quiet)     QUIET=true; shift ;;
        --dry-run)   DRY_RUN=true; shift ;;
        --notes)     NOTES="$2"; shift 2 ;;
        *)           echo "Unknown option: $1"; exit 1 ;;
    esac
done

STRIKE7_URL="${STRIKE7_URL:-http://localhost:5500}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_DIR="$SCRIPT_DIR/../dashboard"

# --- Build Python command ---
# Arguments are passed via environment variables to avoid shell injection risks.
# Note: --attempt and --notes are accepted for forward compatibility but are not
# yet passed to run_benchmark_automated (the Python function does not support
# them yet). They will be wired in when the function is extended.
PYTHON_CMD=(
    python3 -c "
import sys, json, os
sys.path.insert(0, os.environ['DASHBOARD_DIR'])
from utils.cli_runner import run_benchmark_automated

result = run_benchmark_automated(
    benchmark_id=os.environ['BENCHMARK_ID'],
    provider=os.environ['PROVIDER'],
    model_name=os.environ['MODEL_NAME'],
    base_url=os.environ.get('STRIKE7_URL') or None,
    dry_run=os.environ.get('DRY_RUN') == 'true',
)
print(json.dumps(result, indent=2))
"
)

export DASHBOARD_DIR BENCHMARK_ID PROVIDER MODEL_NAME STRIKE7_URL
export RUN_NOTES="$NOTES"
if [ "$DRY_RUN" = true ]; then
    export DRY_RUN=true
else
    export DRY_RUN=false
fi

# --- Execute and display results ---
if [ "$QUIET" = true ]; then
    "${PYTHON_CMD[@]}"
else
    echo "================================================================"
    echo "  STRIKE7 AUTOMATED COMPARISON RUN"
    echo "================================================================"
    echo "  Benchmark:  $BENCHMARK_ID"
    echo "  Provider:   $PROVIDER"
    echo "  Model:      $MODEL_NAME"
    echo "  Attempt:    #$ATTEMPT"
    echo "  Dashboard:  $STRIKE7_URL"
    if [ -n "$NOTES" ]; then
        echo "  Notes:      $NOTES"
    fi
    if [ "$DRY_RUN" = true ]; then
        echo "  Mode:       DRY RUN (no execution)"
    fi
    echo "================================================================"
    echo ""

    RESULT=$("${PYTHON_CMD[@]}")

    # Parse and display result
    STATUS=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','error'))")
    FLAG=$(echo "$RESULT" | python3 -c "import sys,json; print('YES' if json.load(sys.stdin).get('flag_captured') else 'NO')")
    TOKENS=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_tokens', 0))")
    DURATION=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_duration_s', 0))")
    COST=$(echo "$RESULT" | python3 -c "import sys,json; c=json.load(sys.stdin).get('cost_usd'); print(f'\${c:.4f}' if c else 'N/A')")
    RUN_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('run_id', 'unknown'))")
    FAIL=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('failure_reason') or '-')")

    echo ""
    echo "================================================================"
    if [ "$STATUS" = "success" ]; then
        echo "  RECORDED SUCCESSFULLY"
    elif [ "$STATUS" = "dry_run" ]; then
        echo "  DRY RUN COMPLETE"
        echo ""
        echo "$RESULT"
    else
        echo "  RUN FAILED"
    fi
    echo "----------------------------------------------------------------"
    echo "  Run ID:    $RUN_ID"
    echo "  Captured:  $FLAG"
    echo "  Duration:  ${DURATION}s"
    echo "  Tokens:    $TOKENS"
    echo "  Cost:      $COST"
    echo "  Failure:   $FAIL"
    echo "================================================================"
fi
