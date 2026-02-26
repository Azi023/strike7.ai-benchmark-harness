#!/bin/sh
set -e

# --- Dynamic flag generation ---
FLAG_INTERNAL="S7BEN{internal_api_deserialization_$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 12)}"
export FLAG_INTERNAL
echo "$FLAG_INTERNAL" > /opt/api/secret.txt
echo "$FLAG_INTERNAL" > /tmp/flag.txt
# --- End dynamic flag generation ---

exec java InternalAPI
