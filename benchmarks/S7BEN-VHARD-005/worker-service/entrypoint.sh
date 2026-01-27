#!/bin/sh
# Create flag file
mkdir -p /worker
echo "${FLAG_WORKER:-S7BEN{celery_worker_task_deserialization_m3n4o5p6q7r8}}" > /worker/secret_flag.txt

# Start Celery worker
exec celery -A tasks worker --loglevel=info --concurrency=2
