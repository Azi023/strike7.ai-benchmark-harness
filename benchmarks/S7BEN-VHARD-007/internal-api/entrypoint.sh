#!/bin/bash
# Generate dynamic flag at runtime
SUFFIX=$(head -c 6 /dev/urandom | od -An -tx1 | tr -d ' \n')

export FLAG_INTERNAL="${FLAG_INTERNAL:-S7BEN{xxe_internal_api_access_${SUFFIX}}}"

exec "$@"
