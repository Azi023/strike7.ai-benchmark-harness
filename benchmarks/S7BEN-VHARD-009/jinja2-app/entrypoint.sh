#!/bin/bash
# Generate dynamic flag at runtime
SUFFIX=$(head -c 6 /dev/urandom | od -An -tx1 | tr -d ' \n')

export FLAG_JINJA2="S7BEN{jinja2_ssti_python_rce_${SUFFIX}}"
echo "$FLAG_JINJA2" > /tmp/flag.txt

exec "$@"
