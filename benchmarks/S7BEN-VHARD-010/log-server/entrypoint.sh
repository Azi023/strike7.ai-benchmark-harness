#!/bin/bash
# Generate dynamic flag at runtime
SUFFIX=$(head -c 6 /dev/urandom | od -An -tx1 | tr -d ' \n')

export FLAG_LOG="${FLAG_LOG:-S7BEN{apache_log_poisoning_rce_${SUFFIX}}}"

exec "$@"
