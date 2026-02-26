#!/bin/sh
set -e

# --- Dynamic flag generation ---
FLAG_WEB="S7BEN{java_deserialize_web_rce_$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 12)}"
export FLAG_WEB
echo "$FLAG_WEB" > /app/flag.txt
echo "$FLAG_WEB" > /tmp/flag.txt
# --- End dynamic flag generation ---

exec java -jar /app/webapp.jar
