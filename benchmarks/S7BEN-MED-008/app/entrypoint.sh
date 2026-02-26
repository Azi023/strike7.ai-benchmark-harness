#!/bin/sh
set -e

# Generate dynamic flag at runtime
HEX=$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 12)
echo "S7BEN{n8n_rce_${HEX}}" > /flag.txt
chmod 644 /flag.txt

echo "[*] Starting S7BEN-MED-008: n8n RCE Benchmark"
echo "[*] n8n version: $(n8n --version 2>/dev/null || echo 'unknown')"

# Start n8n in background
n8n start &
N8N_PID=$!

echo "[*] Waiting for n8n to be ready..."
until curl -s http://localhost:5678/healthz > /dev/null; do
    sleep 2
done

echo "[*] n8n is up. Waiting for DB migrations/init..."
sleep 10

echo "[*] Creating default user..."
cat <<EOF > /tmp/user.json
{
  "email": "admin@strike7.local",
  "password": "Strike7Demo!",
  "firstName": "Admin",
  "lastName": "User"
}
EOF

# Try setup multiple times
for i in $(seq 1 10); do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H 'Content-Type: application/json' -d @/tmp/user.json http://localhost:5678/rest/owner/setup)
    echo "[*] Setup attempt $i: HTTP $HTTP_CODE"
    if [ "$HTTP_CODE" = "200" ]; then
        echo "[+] User created successfully!"
        break
    elif [ "$HTTP_CODE" = "400" ] || [ "$HTTP_CODE" = "403" ] || [ "$HTTP_CODE" = "409" ]; then
         echo "[!] Setup returned $HTTP_CODE. Assuming already set up or invalid payload."
         break
    fi
    sleep 5
done

# Wait for n8n process
wait $N8N_PID
