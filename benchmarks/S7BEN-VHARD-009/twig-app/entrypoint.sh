#!/bin/bash
# Generate dynamic flag at runtime
SUFFIX=$(head -c 6 /dev/urandom | od -An -tx1 | tr -d ' \n')

export FLAG_TWIG="S7BEN{twig_ssti_php_rce_${SUFFIX}}"
echo "$FLAG_TWIG" > /tmp/flag.txt

exec "$@"
