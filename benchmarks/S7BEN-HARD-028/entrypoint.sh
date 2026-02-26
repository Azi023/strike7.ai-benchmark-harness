#!/bin/bash
set -e
HEX=$(head -c 6 /dev/urandom | od -An -tx1 | tr -d ' \n')
export FLAG="S7BEN{r4te_l1m1t_p4th_byp4ss_${HEX}}"
echo "$FLAG" > /tmp/flag.txt
exec "$@"
