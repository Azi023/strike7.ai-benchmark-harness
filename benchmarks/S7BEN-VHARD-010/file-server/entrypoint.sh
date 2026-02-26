#!/bin/sh
# Generate dynamic flag at runtime
SUFFIX=$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 12)

export FLAG_INTERNAL="${FLAG_INTERNAL:-S7BEN{internal_file_server_access_${SUFFIX}}}"

exec "$@"
