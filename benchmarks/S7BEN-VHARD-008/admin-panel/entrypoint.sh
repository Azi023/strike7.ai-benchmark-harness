#!/bin/sh
# Generate dynamic flag at runtime
SUFFIX=$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 12)

export FLAG_ADMIN="${FLAG_ADMIN:-S7BEN{nosql_admin_panel_access_${SUFFIX}}}"

exec "$@"
