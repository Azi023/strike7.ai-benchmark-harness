#!/bin/sh
# Generate dynamic flag at runtime
SUFFIX=$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 12)

export FLAG_BYPASS="${FLAG_BYPASS:-S7BEN{nosql_auth_bypass_ne_operator_${SUFFIX}}}"

exec "$@"
