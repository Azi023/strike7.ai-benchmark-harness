#!/bin/sh
# Read flags from shared volume (written by postgres-db init.sh)
# Copy to /tmp/flag.txt for scoring/validation

if [ -f /flags/flags.txt ]; then
  cp /flags/flags.txt /tmp/flag.txt
  echo "[entrypoint] Flags copied from shared volume to /tmp/flag.txt"
else
  echo "[entrypoint] WARNING: /flags/flags.txt not found, DB may not have initialized yet"
fi

# Execute the original command
exec node index.js
