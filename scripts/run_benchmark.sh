#!/bin/bash
# Usage: ./scripts/run_benchmark.sh <benchmark_id> <provider> <model_name> <attempt>
# Example: ./scripts/run_benchmark.sh S7BEN-EASY-001 google gemini-2.5-flash 1

echo "================================================================"
echo "  [DEPRECATED] This script is superseded by:"
echo "    ./scripts/run_automated.sh  (fully automated)"
echo "    ./scripts/run_comparison.sh (manual with prompts)"
echo "  This script will be removed in a future release."
echo "================================================================"
echo ""

set -e

BENCHMARK_ID=$1
PROVIDER=$2
MODEL_NAME=$3
ATTEMPT=${4:-1}
VPS="139.59.80.137"
API_URL="http://$VPS:5500"

# Get port for this benchmark from the API
PORT=$(curl -s "$API_URL/api/benchmarks" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for b in data:
    if b.get('id') == '$BENCHMARK_ID':
        print(b.get('port', 'unknown'))
        break
" 2>/dev/null || echo "unknown")

echo "══════════════════════════════════════════════════════════"
echo "  BENCHMARK RUN"
echo "  Benchmark:  $BENCHMARK_ID"
echo "  Port:       $PORT"
echo "  Model:      $PROVIDER / $MODEL_NAME"  
echo "  Attempt:    $ATTEMPT"
echo "══════════════════════════════════════════════════════════"

# Start the benchmark container via API
echo "[$(date +%H:%M:%S)] Starting benchmark container..."
START_RESPONSE=$(curl -s -X POST "$API_URL/api/benchmark/$BENCHMARK_ID/start")
echo "  Start response: $START_RESPONSE"

START_TIME=$(date +%s)

echo ""
echo "══════════════════════════════════════════════════════════"
echo "  Container is running. NOW launch your CLI:"
echo ""
echo "  FOR GEMINI:   gemini --yolo"
echo "  FOR CLAUDE:   claude --dangerously-skip-permissions"  
echo "  FOR CODEX:    codex --full-auto"
echo ""
echo "  Then paste the benchmark prompt."
echo "  This script will monitor for flag capture..."
echo "══════════════════════════════════════════════════════════"
echo ""

# Monitor for completion
FLAG_CAPTURED=0
while true; do
    # Check activity history for flag capture
    LATEST=$(curl -s "$API_URL/api/activity-history?limit=1" 2>/dev/null)
    
    if echo "$LATEST" | grep -q "flag_captured.*$BENCHMARK_ID" 2>/dev/null; then
        FLAG_CAPTURED=1
        break
    fi
    
    # Check if container is still running
    CONTAINER_STATUS=$(curl -s "$API_URL/api/benchmark/$BENCHMARK_ID/status" 2>/dev/null)
    if echo "$CONTAINER_STATUS" | grep -q '"running": false' 2>/dev/null; then
        break
    fi
    
    # Timeout after 15 minutes
    ELAPSED=$(( $(date +%s) - START_TIME ))
    if [ $ELAPSED -gt 900 ]; then
        echo "[TIMEOUT] 15 minutes elapsed. Stopping."
        curl -s -X POST "$API_URL/api/benchmark/$BENCHMARK_ID/stop" > /dev/null
        break
    fi
    
    # Show elapsed time
    printf "\r  Elapsed: ${ELAPSED}s  (monitoring...)"
    sleep 5
done

END_TIME=$(date +%s)
DURATION=$(( END_TIME - START_TIME ))

echo ""
echo "══════════════════════════════════════════════════════════"
echo "  RUN COMPLETE"
echo "  Duration:     ${DURATION}s"
echo "  Flag:         $([ $FLAG_CAPTURED -eq 1 ] && echo '✓ CAPTURED' || echo '✗ NOT CAPTURED')"
echo "══════════════════════════════════════════════════════════"

# Prompt for additional data
echo ""
read -p "  Steps taken (from CLI output, or press Enter to skip): " STEPS
read -p "  Token count (from CLI output, or press Enter to skip): " TOKENS
read -p "  Any notes: " NOTES

# Record to comparison API
echo "[$(date +%H:%M:%S)] Recording result..."
curl -s -X POST "$API_URL/api/comparison/runs" \
  -H "Content-Type: application/json" \
  -d "{
    \"benchmark_id\": \"$BENCHMARK_ID\",
    \"difficulty_tier\": \"$(echo $BENCHMARK_ID | grep -oP '(?<=S7BEN-)[A-Z]+' )\",
    \"provider\": \"$PROVIDER\",
    \"model_name\": \"$MODEL_NAME\",
    \"flag_captured\": $FLAG_CAPTURED,
    \"time_to_flag_s\": $([ $FLAG_CAPTURED -eq 1 ] && echo $DURATION || echo 'null'),
    \"total_duration_s\": $DURATION,
    \"attempt_number\": $ATTEMPT,
    \"steps_taken\": ${STEPS:-null},
    \"total_tokens\": ${TOKENS:-null},
    \"execution_method\": \"cli\",
    \"notes\": \"$NOTES\"
  }"

echo ""
echo "✓ Result recorded. View at: http://$VPS:5500/comparison"
