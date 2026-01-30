#!/bin/bash
# Sync docker-compose.yml files from VPS with port fixes

VPS_HOST="root@139.59.80.137"
VPS_PATH="/opt/strike7.ai-benchmark-harness/benchmarks"
LOCAL_PATH="benchmarks"

echo "🔄 Syncing docker-compose.yml files from VPS..."

# Sync only docker-compose.yml files
rsync -avz --progress \
  --include='*/' \
  --include='docker-compose.yml' \
  --exclude='*' \
  ${VPS_HOST}:${VPS_PATH}/ \
  ${LOCAL_PATH}/

echo "✅ Sync complete! Port mappings now match VPS."
