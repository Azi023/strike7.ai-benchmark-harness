#!/bin/bash
# ==============================================================================
# run_comparison.sh — Record a single benchmark comparison run
#
# Usage:
#   ./scripts/run_comparison.sh <benchmark_id> <provider> <model_name> [attempt] [flags...]
#
# Examples:
#   ./scripts/run_comparison.sh S7BEN-EASY-001 google gemini-2.5-flash
#   ./scripts/run_comparison.sh S7BEN-HARD-023 anthropic claude-opus-4.6 2
#   ./scripts/run_comparison.sh S7BEN-EASY-001 google gemini-2.5-flash 1 --captured --time 15.2 --tokens 3041 --steps 5
#
# Environment:
#   STRIKE7_URL  — Dashboard API URL (default: http://localhost:5500)
#
# Workflow:
#   1. Starts the benchmark container
#   2. Displays the rendered prompt for the model
#   3. Waits for you to run the agent in its CLI
#   4. Prompts for results (or accepts them via flags)
#   5. Records the run to the comparison database
# ==============================================================================

set -euo pipefail

STRIKE7_URL="${STRIKE7_URL:-http://localhost:5500}"

# --- Argument parsing ---
BENCHMARK_ID="${1:?Usage: $0 <benchmark_id> <provider> <model_name> [attempt] [flags...]}"
PROVIDER="${2:?Missing provider (google, anthropic, openai)}"
MODEL_NAME="${3:?Missing model_name (e.g., gemini-2.5-flash)}"
ATTEMPT="${4:-1}"

# Optional flags for non-interactive recording
FLAG_CAPTURED=""
TIME_TO_FLAG=""
TOTAL_TOKENS=""
STEPS_TAKEN=""
TOTAL_DURATION=""
FAILURE_REASON=""
NOTES=""

shift 4 2>/dev/null || shift $# 2>/dev/null
while [[ $# -gt 0 ]]; do
    case "$1" in
        --captured)     FLAG_CAPTURED=1; shift ;;
        --failed)       FLAG_CAPTURED=0; shift ;;
        --time)         TIME_TO_FLAG="$2"; shift 2 ;;
        --duration)     TOTAL_DURATION="$2"; shift 2 ;;
        --tokens)       TOTAL_TOKENS="$2"; shift 2 ;;
        --steps)        STEPS_TAKEN="$2"; shift 2 ;;
        --failure)      FAILURE_REASON="$2"; shift 2 ;;
        --notes)        NOTES="$2"; shift 2 ;;
        *)              echo "Unknown flag: $1"; exit 1 ;;
    esac
done

# --- Resolve difficulty tier from benchmark ID ---
TIER=$(echo "$BENCHMARK_ID" | sed -E 's/S7BEN-([A-Z]+)-.*/\1/')

echo "================================================================"
echo "  STRIKE7 COMPARISON RUN"
echo "================================================================"
echo "  Benchmark:  $BENCHMARK_ID ($TIER)"
echo "  Provider:   $PROVIDER"
echo "  Model:      $MODEL_NAME"
echo "  Attempt:    #$ATTEMPT"
echo "  Dashboard:  $STRIKE7_URL"
echo "================================================================"
echo ""

# --- Step 1: Get rendered prompt ---
echo "[1/4] Fetching tuned prompt..."
PROMPT_RESPONSE=$(curl -sf "$STRIKE7_URL/api/comparison/prompt?benchmark_id=$BENCHMARK_ID&provider=$PROVIDER&model_name=$MODEL_NAME&attempt_number=$ATTEMPT" 2>/dev/null || echo "PROMPT_FETCH_FAILED")

if [ "$PROMPT_RESPONSE" = "PROMPT_FETCH_FAILED" ]; then
    echo "  [!] Could not fetch prompt from API. Is the dashboard running?"
    echo "  [!] Continuing without rendered prompt..."
    PROMPT_HASH=""
else
    PROMPT_HASH=$(echo "$PROMPT_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('prompt_hash',''))" 2>/dev/null || echo "")
    echo "$PROMPT_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('prompt',''))" 2>/dev/null || true
fi

echo ""
echo "================================================================"
echo "  PROMPT READY — Copy the above into your $PROVIDER CLI"
echo "  (or use the API: GET $STRIKE7_URL/api/comparison/prompt?...)"
echo "================================================================"

# --- Step 2: Start benchmark container ---
echo ""
echo "[2/4] Starting benchmark container..."
START_RESULT=$(curl -sf -X POST "$STRIKE7_URL/api/benchmark/$BENCHMARK_ID/start" \
    -H "Content-Type: application/json" \
    -d '{"force_stop_others": true}' 2>/dev/null || echo '{"status":"error"}')

PORT=$(echo "$START_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('port','unknown'))" 2>/dev/null || echo "unknown")
echo "  Container started on port $PORT"

START_TIME=$(date +%s)

# --- Step 3: Wait for agent to finish ---
if [ -z "$FLAG_CAPTURED" ]; then
    echo ""
    echo "================================================================"
    echo "  NOW: Run the agent in your $PROVIDER CLI"
    echo "  Target: http://${STRIKE7_URL##http*://}:$PORT/"
    echo "  Press ENTER when the agent has finished..."
    echo "================================================================"
    read -r

    END_TIME=$(date +%s)
    TOTAL_DURATION="${TOTAL_DURATION:-$((END_TIME - START_TIME))}"

    echo ""
    echo "[3/4] Recording results..."
    read -rp "  Flag captured? (y/n): " CAPTURED_YN
    if [[ "$CAPTURED_YN" =~ ^[Yy] ]]; then
        FLAG_CAPTURED=1
        [ -z "$TIME_TO_FLAG" ] && read -rp "  Time to flag (seconds): " TIME_TO_FLAG
    else
        FLAG_CAPTURED=0
        [ -z "$FAILURE_REASON" ] && read -rp "  Failure reason (timeout/loop/wrong_approach): " FAILURE_REASON
    fi
    [ -z "$TOTAL_TOKENS" ] && read -rp "  Total tokens (estimate, or press Enter to skip): " TOTAL_TOKENS
    [ -z "$STEPS_TAKEN" ] && read -rp "  Steps taken (or press Enter to skip): " STEPS_TAKEN
else
    END_TIME=$(date +%s)
    TOTAL_DURATION="${TOTAL_DURATION:-$((END_TIME - START_TIME))}"
fi

# --- Step 4: Record to comparison database ---
echo ""
echo "[4/4] Submitting to comparison database..."

# Build JSON payload
JSON_PAYLOAD=$(python3 -c "
import json
data = {
    'benchmark_id': '$BENCHMARK_ID',
    'difficulty_tier': '$TIER',
    'provider': '$PROVIDER',
    'model_name': '$MODEL_NAME',
    'attempt_number': int('$ATTEMPT'),
    'flag_captured': int('${FLAG_CAPTURED:-0}'),
    'total_duration_s': float('${TOTAL_DURATION:-0}'),
    'execution_method': 'cli',
}
if '${TIME_TO_FLAG:-}':
    data['time_to_flag_s'] = float('$TIME_TO_FLAG')
if '${TOTAL_TOKENS:-}':
    data['total_tokens'] = int('$TOTAL_TOKENS')
if '${STEPS_TAKEN:-}':
    data['steps_taken'] = int('$STEPS_TAKEN')
if '${FAILURE_REASON:-}':
    data['failure_reason'] = '$FAILURE_REASON'
if '${NOTES:-}':
    data['notes'] = '$NOTES'
if '$PROMPT_HASH':
    data['system_prompt_hash'] = '$PROMPT_HASH'
print(json.dumps(data))
")

RESULT=$(curl -sf -X POST "$STRIKE7_URL/api/comparison/runs" \
    -H "Content-Type: application/json" \
    -d "$JSON_PAYLOAD" 2>/dev/null || echo '{"status":"error","message":"API call failed"}')

RUN_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('run',{}).get('run_id','unknown'))" 2>/dev/null || echo "unknown")
STATUS=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','error'))" 2>/dev/null || echo "error")

echo ""
echo "================================================================"
if [ "$STATUS" = "success" ]; then
    echo "  RECORDED SUCCESSFULLY"
    echo "  Run ID:    $RUN_ID"
    echo "  Captured:  $([ "$FLAG_CAPTURED" = "1" ] && echo "YES" || echo "NO")"
    echo "  Duration:  ${TOTAL_DURATION}s"
    echo "  Model:     $PROVIDER / $MODEL_NAME"
else
    echo "  RECORDING FAILED"
    echo "  Response: $RESULT"
fi
echo "================================================================"

# --- Stop container ---
curl -sf -X POST "$STRIKE7_URL/api/benchmark/$BENCHMARK_ID/stop" > /dev/null 2>&1 || true
echo "  Container stopped."
