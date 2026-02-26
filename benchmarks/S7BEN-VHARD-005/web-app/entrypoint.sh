#!/bin/sh
set -e

# --- Dynamic flag generation ---
FLAG_WEB="S7BEN{pickle_session_cookie_rce_$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 12)}"
export FLAG_WEB
mkdir -p /app
echo "$FLAG_WEB" > /app/flag.txt
echo "$FLAG_WEB" > /tmp/flag.txt
# --- End dynamic flag generation ---

# Start Flask application
exec python app.py
