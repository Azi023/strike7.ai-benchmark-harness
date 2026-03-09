#!/bin/bash
# Push benchmark Docker images from S7-Benchmark to a new worker
# Usage: ./push_images_to_worker.sh <worker_ip> [ssh_key]
set -euo pipefail

WORKER_IP="${1:?Usage: $0 <worker_ip> [ssh_key]}"
SSH_KEY="${2:-/root/.ssh/worker_key}"
EXPORT_DIR="/opt/strike7.ai-benchmark-harness/exports"
ARCHIVE="$EXPORT_DIR/s7ben_images_$(date +%Y%m%d).tar.gz"

if [ ! -f "$ARCHIVE" ]; then
    echo "Archive not found. Creating fresh export..."
    mkdir -p "$EXPORT_DIR"
    docker save $(docker images --format '{{.Repository}}:{{.Tag}}' | grep s7ben) | gzip > "$ARCHIVE"
fi

echo "Transferring $(du -h $ARCHIVE | cut -f1) to $WORKER_IP..."
scp -i "$SSH_KEY" "$ARCHIVE" "root@${WORKER_IP}:/tmp/s7ben_images.tar.gz"

echo "Loading images on worker..."
ssh -i "$SSH_KEY" "root@${WORKER_IP}" "gunzip -c /tmp/s7ben_images.tar.gz | docker load && rm /tmp/s7ben_images.tar.gz"

echo "Verifying..."
REMOTE_COUNT=$(ssh -i "$SSH_KEY" "root@${WORKER_IP}" "docker images | grep s7ben | wc -l")
echo "Worker has $REMOTE_COUNT benchmark images"
echo "Done!"
