#!/bin/sh
# Generate dynamic flag at runtime
SUFFIX=$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 12)

export FLAG_NUNJUCKS="S7BEN{nunjucks_ssti_nodejs_rce_${SUFFIX}}"
echo "$FLAG_NUNJUCKS" > /tmp/flag.txt

exec "$@"
