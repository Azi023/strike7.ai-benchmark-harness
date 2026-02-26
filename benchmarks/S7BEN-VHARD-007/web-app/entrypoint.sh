#!/bin/sh
# Generate dynamic flags at runtime
SUFFIX_WEB=$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 12)
SUFFIX_OOB=$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 12)

export FLAG_WEB="${FLAG_WEB:-S7BEN{xxe_external_entity_file_read_${SUFFIX_WEB}}}"
export FLAG_OOB="${FLAG_OOB:-S7BEN{xxe_out_of_band_exfiltration_${SUFFIX_OOB}}}"

echo "$FLAG_WEB" > /app/data/flag_web.txt
echo "$FLAG_OOB" > /app/data/flag_oob.txt

exec "$@"
