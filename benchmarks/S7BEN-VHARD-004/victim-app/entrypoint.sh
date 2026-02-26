#!/bin/sh
set -e

# --- Dynamic flag generation ---
FLAG_VICTIM="S7BEN{victim_app_full_compromise_$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 12)}"
export FLAG_VICTIM
echo "$FLAG_VICTIM" > /data/admin_flag.txt
echo "$FLAG_VICTIM" > /tmp/flag.txt
# --- End dynamic flag generation ---

exec tail -f /dev/null
