#!/bin/bash
#
# Strike7 Base Docker Images - Build All Script
# Builds all 5 base images for benchmark development
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║  Strike7 Base Docker Images - Build All              ║${NC}"
echo -e "${BOLD}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# Build order: smallest to largest
BASES=(
    "base-db:MySQL 8.0 database with test configuration"
    "base-modsec-waf:ModSecurity + OWASP CRS WAF"
    "base-web-app:Python 3.11 + Node.js 20 web application base"
    "base-exploit-server:Pre-built marshalsec for JNDI exploitation"
    "base-java-vuln:Maven + OpenJDK 11 for Java vulnerabilities"
)

TOTAL=${#BASES[@]}
SUCCESS=0
FAILED=0

for item in "${BASES[@]}"; do
    IFS=':' read -r dir description <<< "$item"

    echo -e "${BLUE}[*]${NC} Building ${BOLD}$dir${NC}"
    echo -e "    Description: $description"

    if [ ! -d "$dir" ]; then
        echo -e "${YELLOW}[!]${NC} Directory not found: $dir - skipping"
        ((FAILED++))
        continue
    fi

    START_TIME=$(date +%s)

    if docker build -t "strike7/$dir:latest" "./$dir" > "/tmp/build-$dir.log" 2>&1; then
        END_TIME=$(date +%s)
        ELAPSED=$((END_TIME - START_TIME))
        echo -e "${GREEN}[✓]${NC} Built ${BOLD}strike7/$dir:latest${NC} in ${ELAPSED}s"
        ((SUCCESS++))
    else
        echo -e "${YELLOW}[✗]${NC} Failed to build $dir"
        echo -e "    See logs: /tmp/build-$dir.log"
        ((FAILED++))
    fi

    echo ""
done

# Summary
echo -e "${BOLD}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║  Build Summary                                        ║${NC}"
echo -e "${BOLD}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}Total Images:${NC}     $TOTAL"
echo -e "  ${GREEN}${BOLD}Successful:${NC}       $SUCCESS"
echo -e "  ${YELLOW}${BOLD}Failed:${NC}           $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}[✓] All base images built successfully!${NC}"
    echo ""
    echo -e "${BOLD}Available Images:${NC}"
    docker images | grep "strike7/base-" || true
    exit 0
else
    echo -e "${YELLOW}[!] Some images failed to build. Check logs in /tmp/build-*.log${NC}"
    exit 1
fi
