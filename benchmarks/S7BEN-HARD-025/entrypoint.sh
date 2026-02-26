#!/bin/sh
set -e

# Generate a dynamic flag using Python
TOKEN=$(python3 -c "import secrets; print(secrets.token_hex(16))")
export FLAG="S7BEN{prompt_inj3ct10n_${TOKEN}}"

echo "[IntelliAssist] FLAG generated: ${FLAG}"

# Write flag to filesystem so dashboard can capture it via docker exec
echo "${FLAG}" > /flag.txt

exec python3 app.py
