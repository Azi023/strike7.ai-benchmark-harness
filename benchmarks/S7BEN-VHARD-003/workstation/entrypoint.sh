#!/bin/bash
set -e

# --- Dynamic flag generation ---
FLAG_ASREP="S7BEN{asrep_roast_no_preauth_$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 12)}"
export FLAG_ASREP
echo "$FLAG_ASREP" > /tmp/flag.txt
# --- End dynamic flag generation ---

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
