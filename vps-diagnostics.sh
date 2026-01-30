#!/bin/bash
# vps-diagnostics.sh

echo "=== Strike7 VPS Diagnostics ==="
echo ""

echo "1. Checking Strike7 Dashboard Status..."
systemctl status strike7-dashboard --no-pager | head -20

echo ""
echo "2. Checking available benchmark images..."
docker images | grep s7ben | wc -l
echo "   (Should be 64, currently showing above count)"

echo ""
echo "3. Checking installed security tools..."
for tool in nmap sqlmap nikto gobuster hydra john hashcat; do
    if which $tool > /dev/null 2>&1; then
        echo "   ✓ $tool installed"
    else
        echo "   ✗ $tool MISSING"
    fi
done

echo ""
echo "4. Checking MCP server..."
if [ -f "/root/strike7-benchmarks/mcp-server/build/index.js" ]; then
    echo "   ✓ MCP server built"
else
    echo "   ✗ MCP server not found"
fi

echo ""
echo "5. Checking port conflicts..."
docker ps --format "{{.Names}}: {{.Ports}}" | grep "0.0.0.0"
