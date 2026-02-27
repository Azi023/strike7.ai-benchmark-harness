#!/bin/bash
# ==============================================================================
# batch_comparison.sh — Run all models against a benchmark (semi-automated)
#
# Usage:
#   ./scripts/batch_comparison.sh <benchmark_id>
#   ./scripts/batch_comparison.sh S7BEN-EASY-001
#   STRIKE7_URL=http://139.59.80.137:5500 ./scripts/batch_comparison.sh S7BEN-HARD-023
#
# Environment:
#   STRIKE7_URL  — Dashboard API URL (default: http://localhost:5500)
#
# Walks through each model one at a time. For each model:
#   1. Shows the rendered prompt
#   2. Starts the benchmark container
#   3. Waits for you to run the agent
#   4. Records the results
# ==============================================================================

set -euo pipefail

STRIKE7_URL="${STRIKE7_URL:-http://localhost:5500}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BENCHMARK="${1:?Usage: $0 <benchmark_id>}"

# Models to compare (provider:model_name)
MODELS=(
    "google:gemini-2.5-flash"
    "google:gemini-2.5-pro"
    "anthropic:claude-sonnet-4.5"
    "anthropic:claude-opus-4.6"
    "openai:gpt-4.1-mini"
    "openai:gpt-4.1"
)

TOTAL=${#MODELS[@]}
CURRENT=0

echo ""
echo "================================================================"
echo "  STRIKE7 BATCH COMPARISON"
echo "================================================================"
echo "  Benchmark:  $BENCHMARK"
echo "  Models:     $TOTAL"
echo "  Dashboard:  $STRIKE7_URL"
echo "================================================================"
echo ""
echo "  This will walk you through running each model one at a time."
echo "  For each model, you'll switch to that provider's CLI."
echo ""
echo "  Models in queue:"
for model_entry in "${MODELS[@]}"; do
    IFS=':' read -r provider model <<< "$model_entry"
    echo "    - $provider / $model"
done
echo ""
read -rp "  Press ENTER to begin (or Ctrl+C to cancel)..."

for model_entry in "${MODELS[@]}"; do
    IFS=':' read -r provider model <<< "$model_entry"
    CURRENT=$((CURRENT + 1))

    echo ""
    echo "================================================================"
    echo "  [$CURRENT/$TOTAL] $provider / $model"
    echo "================================================================"
    echo ""
    echo "  Switch to your $provider CLI now."
    read -rp "  Press ENTER when ready (or type 'skip' to skip this model): " RESPONSE

    if [ "$RESPONSE" = "skip" ]; then
        echo "  Skipped $provider / $model"
        continue
    fi

    "$SCRIPT_DIR/run_comparison.sh" "$BENCHMARK" "$provider" "$model" 1

    echo ""
    echo "  --- $provider / $model complete ---"
    echo ""
done

echo ""
echo "================================================================"
echo "  BATCH COMPLETE"
echo "================================================================"
echo "  Benchmark: $BENCHMARK"
echo "  Models run: $TOTAL"
echo ""
echo "  View results:"
echo "    curl $STRIKE7_URL/api/comparison/runs?benchmark_id=$BENCHMARK"
echo "    curl $STRIKE7_URL/api/comparison/summary?benchmark_id=$BENCHMARK"
echo "================================================================"
