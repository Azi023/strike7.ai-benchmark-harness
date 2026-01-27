#!/bin/bash
set -e

echo "[*] Starting Database Server (dbserver.corp.local)..."

# Start PostgreSQL in background
docker-entrypoint.sh postgres &
PG_PID=$!

# Wait for PostgreSQL to be ready
echo "[*] Waiting for PostgreSQL to be ready..."
until pg_isready -U postgres >/dev/null 2>&1; do
    sleep 1
done
echo "[+] PostgreSQL is ready"

# Start Flask API
echo "[*] Starting Database API on port 5000..."
python3 /opt/database/app.py &
API_PID=$!

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
