#!/bin/bash
echo "=== S7BEN-MED-008 Diagnostic ==="

echo -e "\n[1] Container Status:"
docker ps | grep sben-700-25

echo -e "\n[2] n8n Version:"
docker exec sben-700-25-n8n n8n --version

echo -e "\n[3] Flag File:"
docker exec sben-700-25-n8n cat /flag.txt

echo -e "\n[4] Environment Variables:"
docker exec sben-700-25-n8n env | grep -E "(N8N|AUTH|FLAG)" | head -20

echo -e "\n[5] Health Check:"
curl -s http://localhost:5678/healthz && echo " - OK" || echo " - FAILED"

echo -e "\n[6] Login Page Check:"
curl -s http://localhost:5678/ | grep -o "<title>.*</title>"

echo -e "\n[7] API Test (no auth):"
curl -s http://localhost:5678/rest/settings | jq -r '.data.authenticationMethod // "No auth info"' 2>/dev/null || echo "API not accessible"
