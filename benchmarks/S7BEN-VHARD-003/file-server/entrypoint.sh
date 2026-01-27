#!/bin/bash
set -e

echo "[*] Starting File Server (fileserver.corp.local)..."

# Wait for domain controller to be ready
echo "[*] Waiting for domain controller..."
until ldapsearch -x -H ldap://dc.corp.local:389 -b "dc=corp,dc=local" >/dev/null 2>&1; do
    echo "    Waiting for LDAP service..."
    sleep 2
done
echo "[+] Domain controller is ready"

# Start Flask application
echo "[*] Starting file server HTTP API on port 8080..."
python3 /opt/fileserver/app.py
