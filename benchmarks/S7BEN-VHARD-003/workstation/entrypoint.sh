#!/bin/bash
set -e

echo "[*] Starting Workstation (ws01.corp.local)..."

# Wait for domain controller to be ready
echo "[*] Waiting for domain controller..."
until ldapsearch -x -H ldap://dc.corp.local:389 -b "dc=corp,dc=local" >/dev/null 2>&1; do
    echo "    Waiting for LDAP service..."
    sleep 2
done
echo "[+] Domain controller is ready"

# Start Flask application
echo "[*] Starting workstation API on port 5000..."
python3 /opt/workstation/app.py
