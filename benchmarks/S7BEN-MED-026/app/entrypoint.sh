#!/bin/sh
set -e

# Generate dynamic flag
HEX=$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 12)
FLAG="S7BEN{supply_ch41n_publ1sh_h1jack_${HEX}}"
echo "$FLAG" > /tmp/flag.txt
chmod 444 /tmp/flag.txt

# Initialize patch status
echo '{"patched": false}' > /tmp/patch_status.json

echo "[*] Starting S7BEN-MED-026: PackageForge Registry"
echo "[*] Flag generated and stored"

exec python app.py
