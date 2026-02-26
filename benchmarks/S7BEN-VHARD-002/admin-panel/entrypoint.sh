#!/bin/sh
set -e
HEX=$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 12)
export FLAG="S7BEN{admin_access_via_ssrf_credentials_${HEX}}"
echo "$FLAG" > /tmp/flag.txt
exec "$@"
