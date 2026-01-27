#!/bin/bash
#
# Strike7 Benchmark Container Management Script
# Centralized control for all benchmarks
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# All benchmarks
BENCHMARKS=(
    "SBEN-HARD-01:benchmarks/SBEN-HARD-01"
    "SBEN-HARD-02:benchmarks/SBEN-HARD-02"
    "SBEN-HARD-03:benchmarks/SBEN-HARD-03"
    "SBEN-HARD-04:benchmarks/SBEN-HARD-04"
    "SBEN-CVE-01:benchmarks/SBEN-CVE-01"
    "SBEN-CVE-02:benchmarks/SBEN-CVE-02"
    "SBEN-CVE-03:benchmarks/SBEN-CVE-03"
    "SBEN-CVE-04:benchmarks/SBEN-CVE-04"
    "SBEN-CVE-05:benchmarks/SBEN-CVE-05"
    "SBEN-DESER-01:benchmarks/SBEN-DESER-01"
    "SBEN-CHAIN-01:benchmarks/SBEN-CHAIN-01"
)

function show_help() {
    echo -e "${BOLD}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}║  Strike7 Benchmark Container Manager                 ║${NC}"
    echo -e "${BOLD}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Usage: ./manage-containers.sh [COMMAND] [BENCHMARK_ID]"
    echo ""
    echo "Commands:"
    echo "  list              List all available benchmarks"
    echo "  status            Show status of all containers"
    echo "  build [ID]        Build specific benchmark (or all if no ID)"
    echo "  up [ID]           Start specific benchmark (or all if no ID)"
    echo "  down [ID]         Stop specific benchmark (or all if no ID)"
    echo "  restart [ID]      Restart specific benchmark"
    echo "  logs [ID]         Show logs for specific benchmark"
    echo "  test [ID]         Run tests for specific benchmark"
    echo "  clean [ID]        Clean specific benchmark (or all if no ID)"
    echo "  exploit [ID]      Run exploit script for specific benchmark"
    echo "  reset [ID]        Reset telemetry for specific benchmark"
    echo "  health [ID]       Check health of specific benchmark"
    echo "  stop-all          Stop all running containers"
    echo "  prune             Clean up all Docker resources"
    echo ""
    echo "Examples:"
    echo "  ./manage-containers.sh list"
    echo "  ./manage-containers.sh build SBEN-CVE-03"
    echo "  ./manage-containers.sh up SBEN-HARD-01"
    echo "  ./manage-containers.sh logs SBEN-CVE-03"
    echo "  ./manage-containers.sh stop-all"
}

function list_benchmarks() {
    echo -e "${BOLD}Available Strike7 Benchmarks:${NC}"
    echo ""
    printf "%-20s %-40s %s\n" "ID" "PATH" "STATUS"
    echo "────────────────────────────────────────────────────────────────────────"

    for item in "${BENCHMARKS[@]}"; do
        IFS=':' read -r id path <<< "$item"
        if [ -d "$path" ]; then
            # Check if containers are running
            if docker compose -f "$path/docker-compose.yml" ps -q 2>/dev/null | grep -q .; then
                status="${GREEN}RUNNING${NC}"
            else
                status="${YELLOW}STOPPED${NC}"
            fi
            printf "%-20s %-40s %b\n" "$id" "$path" "$status"
        else
            printf "%-20s %-40s %b\n" "$id" "$path" "${RED}NOT FOUND${NC}"
        fi
    done
    echo ""
}

function get_benchmark_path() {
    local search_id="$1"
    for item in "${BENCHMARKS[@]}"; do
        IFS=':' read -r id path <<< "$item"
        if [ "$id" == "$search_id" ]; then
            echo "$path"
            return 0
        fi
    done
    return 1
}

function build_benchmark() {
    local benchmark_id="$1"

    if [ -z "$benchmark_id" ]; then
        echo -e "${BLUE}[*]${NC} Building all benchmarks..."
        for item in "${BENCHMARKS[@]}"; do
            IFS=':' read -r id path <<< "$item"
            if [ -d "$path" ]; then
                echo -e "${BLUE}[*]${NC} Building $id..."
                cd "$path" && make build && cd "$SCRIPT_DIR"
            fi
        done
        return
    fi

    local path=$(get_benchmark_path "$benchmark_id")
    if [ -z "$path" ]; then
        echo -e "${RED}[✗]${NC} Benchmark not found: $benchmark_id"
        return 1
    fi

    echo -e "${BLUE}[*]${NC} Building $benchmark_id..."
    cd "$path" && make build && cd "$SCRIPT_DIR"
}

function up_benchmark() {
    local benchmark_id="$1"

    if [ -z "$benchmark_id" ]; then
        echo -e "${YELLOW}[!]${NC} Starting all benchmarks is not recommended (resource intensive)"
        echo -e "${YELLOW}[!]${NC} Specify a benchmark ID or use 'build' first"
        return 1
    fi

    local path=$(get_benchmark_path "$benchmark_id")
    if [ -z "$path" ]; then
        echo -e "${RED}[✗]${NC} Benchmark not found: $benchmark_id"
        return 1
    fi

    echo -e "${BLUE}[*]${NC} Starting $benchmark_id..."
    cd "$path" && make up && cd "$SCRIPT_DIR"
}

function down_benchmark() {
    local benchmark_id="$1"

    if [ -z "$benchmark_id" ]; then
        echo -e "${BLUE}[*]${NC} Stopping all benchmarks..."
        for item in "${BENCHMARKS[@]}"; do
            IFS=':' read -r id path <<< "$item"
            if [ -d "$path" ]; then
                echo -e "${BLUE}[*]${NC} Stopping $id..."
                cd "$path" && make down 2>/dev/null && cd "$SCRIPT_DIR"
            fi
        done
        return
    fi

    local path=$(get_benchmark_path "$benchmark_id")
    if [ -z "$path" ]; then
        echo -e "${RED}[✗]${NC} Benchmark not found: $benchmark_id"
        return 1
    fi

    echo -e "${BLUE}[*]${NC} Stopping $benchmark_id..."
    cd "$path" && make down && cd "$SCRIPT_DIR"
}

function show_status() {
    echo -e "${BOLD}Container Status:${NC}"
    echo ""
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | grep -E "(NAMES|sben-|log4j-|sqli-|xss-|ssrf-)" || echo "No Strike7 containers running"
    echo ""
}

function stop_all() {
    echo -e "${BLUE}[*]${NC} Stopping all Strike7 containers..."
    docker ps -q --filter "name=sben-" --filter "name=log4j-" --filter "name=sqli-" --filter "name=xss-" --filter "name=ssrf-" | xargs -r docker stop
    echo -e "${GREEN}[✓]${NC} All Strike7 containers stopped"
}

function prune_all() {
    echo -e "${YELLOW}[!]${NC} This will remove all unused Docker resources"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker system prune -af --volumes
        echo -e "${GREEN}[✓]${NC} Docker resources pruned"
    fi
}

function run_exploit() {
    local benchmark_id="$1"
    local path=$(get_benchmark_path "$benchmark_id")

    if [ -z "$path" ]; then
        echo -e "${RED}[✗]${NC} Benchmark not found: $benchmark_id"
        return 1
    fi

    cd "$path"
    if [ -f "exploit.py" ]; then
        echo -e "${BLUE}[*]${NC} Running Python exploit..."
        python3 exploit.py
    elif [ -f "exploit.sh" ]; then
        echo -e "${BLUE}[*]${NC} Running shell exploit..."
        bash exploit.sh
    else
        echo -e "${YELLOW}[!]${NC} No exploit script found"
    fi
    cd "$SCRIPT_DIR"
}

function check_health() {
    local benchmark_id="$1"
    local path=$(get_benchmark_path "$benchmark_id")

    if [ -z "$path" ]; then
        echo -e "${RED}[✗]${NC} Benchmark not found: $benchmark_id"
        return 1
    fi

    cd "$path" && make test && cd "$SCRIPT_DIR"
}

# Main command dispatcher
COMMAND="${1:-help}"
BENCHMARK_ID="$2"

case "$COMMAND" in
    list)
        list_benchmarks
        ;;
    status)
        show_status
        ;;
    build)
        build_benchmark "$BENCHMARK_ID"
        ;;
    up)
        up_benchmark "$BENCHMARK_ID"
        ;;
    down)
        down_benchmark "$BENCHMARK_ID"
        ;;
    restart)
        down_benchmark "$BENCHMARK_ID"
        up_benchmark "$BENCHMARK_ID"
        ;;
    logs)
        if [ -n "$BENCHMARK_ID" ]; then
            path=$(get_benchmark_path "$BENCHMARK_ID")
            cd "$path" && make logs && cd "$SCRIPT_DIR"
        else
            echo "Usage: $0 logs [BENCHMARK_ID]"
        fi
        ;;
    test)
        check_health "$BENCHMARK_ID"
        ;;
    clean)
        if [ -n "$BENCHMARK_ID" ]; then
            path=$(get_benchmark_path "$BENCHMARK_ID")
            cd "$path" && make clean && cd "$SCRIPT_DIR"
        else
            echo -e "${YELLOW}[!]${NC} Cleaning all benchmarks..."
            down_benchmark ""
        fi
        ;;
    exploit)
        run_exploit "$BENCHMARK_ID"
        ;;
    reset)
        if [ -n "$BENCHMARK_ID" ]; then
            path=$(get_benchmark_path "$BENCHMARK_ID")
            cd "$path" && make reset && cd "$SCRIPT_DIR"
        else
            echo "Usage: $0 reset [BENCHMARK_ID]"
        fi
        ;;
    health)
        check_health "$BENCHMARK_ID"
        ;;
    stop-all)
        stop_all
        ;;
    prune)
        prune_all
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}[✗]${NC} Unknown command: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac
