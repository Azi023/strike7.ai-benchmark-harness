#!/bin/bash
set -e

HEX=$(head -c 6 /dev/urandom | od -An -tx1 | tr -d ' \n')
FLAG="S7BEN{r3d1s_s3ss10n_d3s3r14l1z3_${HEX}}"
echo "$FLAG" > /tmp/flag.txt
chmod 444 /tmp/flag.txt

echo '{"patched":false}' > /tmp/patch_status.json
chmod 666 /tmp/patch_status.json

exec "$@"
