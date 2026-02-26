#!/bin/bash
# sync-check.sh
echo "=== Strike7 Sync Check ==="
echo "Host: $(hostname) | Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Find benchmarks
for d in /opt/strike7.ai-benchmark-harness/benchmarks $HOME/workspace/strike7-benchmarks/benchmarks; do
    [ -d "$d" ] && BENCH_DIR="$d" && break
done
[ -z "$BENCH_DIR" ] && echo "ERROR: No benchmarks dir found" && exit 1

echo "Dir: $BENCH_DIR"
cd "$BENCH_DIR"

echo ""
echo "DISTRIBUTION:"
for tier in EASY MED HARD VHARD CVE; do
    count=$(ls -d S7BEN-${tier}-* 2>/dev/null | wc -l)
    printf "  %-6s %d\n" "$tier:" "$count"
done
echo "  TOTAL: $(ls -d S7BEN-* 2>/dev/null | wc -l)"

echo ""
echo "IDS:"
ls -d S7BEN-* 2>/dev/null | sort

echo ""
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo ..)"
echo "GIT: $(git branch --show-current 2>/dev/null) | $(git log --oneline -1 2>/dev/null)"
echo "Dirty: $(git status --porcelain 2>/dev/null | wc -l) files"

echo ""
echo "PORTS (from docker-compose):"
cd "$BENCH_DIR"
for dir in S7BEN-*/; do
    id=$(basename "$dir")
    compose=$(find "$dir" -maxdepth 1 -name "docker-compose.*" | head -1)
    if [ -n "$compose" ]; then
        port=$(grep -oP '"\K\d+(?=:\d+")' "$compose" 2>/dev/null | head -1)
        printf "  %-20s → %s\n" "$id" "${port:-NO_PORT}"
    else
        printf "  %-20s → NO_COMPOSE\n" "$id"
    fi
done
