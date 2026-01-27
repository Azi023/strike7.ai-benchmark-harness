#!/bin/bash
echo "Testing 3 fixed benchmarks..."
for bench in S7BEN-HARD-018 S7BEN-CVE-010 S7BEN-CVE-011; do
    echo ""
    echo "=== Testing  ==="
    cd benchmarks/
    docker-compose up -d > /dev/null 2>&1
    sleep 8
    bash exploit.sh
    docker-compose down > /dev/null 2>&1
    cd ../..
done
