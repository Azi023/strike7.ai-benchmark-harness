#!/bin/sh
set -e

# --- Dynamic flag generation ---
FLAG_WORKER="S7BEN{celery_worker_task_deserialization_$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 12)}"
export FLAG_WORKER
mkdir -p /worker
echo "$FLAG_WORKER" > /worker/secret_flag.txt
echo "$FLAG_WORKER" > /tmp/flag.txt
# --- End dynamic flag generation ---

# Start Celery worker
exec celery -A tasks worker --loglevel=info --concurrency=2
