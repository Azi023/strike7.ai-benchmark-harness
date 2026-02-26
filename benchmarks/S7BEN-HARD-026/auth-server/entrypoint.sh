#!/bin/bash
set -e
HEX=$(head -c 6 /dev/urandom | od -An -tx1 | tr -d ' \n')
export FLAG="S7BEN{oauth_sc0pe_escalat10n_${HEX}}"
echo "$FLAG" > /tmp/flag.txt
exec "$@"
