#!/bin/bash
# Generate dynamic flags at runtime
SUFFIX_LFI=$(head -c 6 /dev/urandom | od -An -tx1 | tr -d ' \n')
SUFFIX_SESSION=$(head -c 6 /dev/urandom | od -An -tx1 | tr -d ' \n')

export FLAG_LFI="${FLAG_LFI:-S7BEN{lfi_path_traversal_file_read_${SUFFIX_LFI}}}"
export FLAG_SESSION="${FLAG_SESSION:-S7BEN{php_session_poisoning_rce_${SUFFIX_SESSION}}}"

echo "$FLAG_LFI" > /var/www/html/flag.txt
echo "$FLAG_SESSION" > /var/www/html/session_flag.txt

exec "$@"
