#!/bin/bash
set -e
HEX=$(head -c 6 /dev/urandom | od -An -tx1 | tr -d ' \n')
export FLAG="S7BEN{gql_4uth_byp4ss_t34m_l34k_${HEX}}"
echo "$FLAG" > /tmp/flag.txt
exec "$@"
