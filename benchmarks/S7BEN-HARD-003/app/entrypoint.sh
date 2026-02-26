#!/bin/bash
set -e
HEX=$(head -c 6 /dev/urandom | od -An -tx1 | tr -d ' \n')
export FLAG="S7BEN{ssrf_internal_acc3ss_dns_rebind_${HEX}}"
echo "$FLAG" > /tmp/flag.txt
exec "$@"
