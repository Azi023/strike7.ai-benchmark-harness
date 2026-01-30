#!/bin/bash
# Test Strike7 MCP Server
# Verifies the MCP server responds correctly to basic requests

set -e

MCP_SERVER="dashboard/mcp_server_minimal.py"

echo "============================================================"
echo "Strike7 MCP Server - Test Suite"
echo "============================================================"
echo ""

# Test 1: Initialize
echo "[1/5] Testing initialize..."
RESPONSE=$(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"0.1.0","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | python "$MCP_SERVER" 2>/dev/null | head -1)
if echo "$RESPONSE" | grep -q '"protocolVersion"'; then
    echo "✓ Initialize successful"
else
    echo "✗ Initialize failed"
    echo "Response: $RESPONSE"
    exit 1
fi
echo ""

# Test 2: List Tools
echo "[2/5] Testing tools/list..."
RESPONSE=$(echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python "$MCP_SERVER" 2>/dev/null | head -1)
if echo "$RESPONSE" | grep -q 'strike7_start_benchmark'; then
    echo "✓ Tools list successful"
    TOOL_COUNT=$(echo "$RESPONSE" | grep -o 'strike7_' | wc -l)
    echo "  Found $TOOL_COUNT tools"
else
    echo "✗ Tools list failed"
    exit 1
fi
echo ""

# Test 3: List Resources
echo "[3/5] Testing resources/list..."
RESPONSE=$(echo '{"jsonrpc":"2.0","id":3,"method":"resources/list","params":{}}' | python "$MCP_SERVER" 2>/dev/null | head -1)
if echo "$RESPONSE" | grep -q 'strike7://benchmarks'; then
    echo "✓ Resources list successful"
else
    echo "✗ Resources list failed"
    exit 1
fi
echo ""

# Test 4: Read Resource
echo "[4/5] Testing resources/read..."
RESPONSE=$(echo '{"jsonrpc":"2.0","id":4,"method":"resources/read","params":{"uri":"strike7://benchmarks"}}' | python "$MCP_SERVER" 2>/dev/null | head -1)
if echo "$RESPONSE" | grep -q 'S7BEN'; then
    echo "✓ Resource read successful"
    BENCHMARK_COUNT=$(echo "$RESPONSE" | grep -o 'S7BEN-' | wc -l)
    echo "  Found $BENCHMARK_COUNT benchmarks"
else
    echo "✗ Resource read failed"
    exit 1
fi
echo ""

# Test 5: Tool Call (get status - safe operation)
echo "[5/5] Testing tools/call (get_status)..."
RESPONSE=$(echo '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"strike7_get_status","arguments":{}}}' | python "$MCP_SERVER" 2>/dev/null | head -1)
if echo "$RESPONSE" | grep -q 'running_count'; then
    echo "✓ Tool call successful"
    RUNNING=$(echo "$RESPONSE" | grep -o '"running_count":[0-9]*' | grep -o '[0-9]*')
    echo "  Running containers: $RUNNING"
else
    echo "✗ Tool call failed"
    echo "Response: $RESPONSE"
    exit 1
fi
echo ""

echo "============================================================"
echo "All MCP Server Tests Passed! ✓"
echo "============================================================"
echo ""
echo "The MCP server is working correctly."
echo ""
echo "Next steps:"
echo "1. Configure Claude Desktop (see MCP_QUICKSTART.md)"
echo "2. Test with a real AI agent"
echo "3. Try exploiting a benchmark through MCP"
