#!/bin/sh
set -e

# --- Dynamic flag generation ---
FLAG_KERBEROAST="S7BEN{kerberoast_service_account_$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 12)}"
export FLAG_KERBEROAST
echo "$FLAG_KERBEROAST" > /tmp/flag.txt
# --- End dynamic flag generation ---

exec node index.js
