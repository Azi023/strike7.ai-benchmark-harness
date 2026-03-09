#!/bin/bash
# Add a new worker to the orchestrator
# Usage: ./add_worker.sh <worker_id> <private_ip> <public_ip> [ssh_key]
set -euo pipefail

WORKER_ID="${1:?Usage: $0 <worker_id> <private_ip> <public_ip> [ssh_key]}"
PRIVATE_IP="${2:?Missing private IP}"
PUBLIC_IP="${3:?Missing public IP}"
SSH_KEY="${4:-/root/.ssh/worker_key}"
CONFIG="/opt/strike7.ai-benchmark-harness/orchestrator.yaml"

echo "Adding worker $WORKER_ID ($PRIVATE_IP / $PUBLIC_IP) to orchestrator..."

# Test SSH connectivity
ssh -i "$SSH_KEY" -o ConnectTimeout=5 "root@${PRIVATE_IP}" "echo 'SSH OK'" || {
    echo "Cannot SSH to $PRIVATE_IP — check key and connectivity"
    exit 1
}

# Append worker to config
python3 -c "
import yaml
with open('$CONFIG') as f:
    config = yaml.safe_load(f)
config['workers'].append({
    'id': '$WORKER_ID',
    'mode': 'remote',
    'host': '$PRIVATE_IP',
    'public_host': '$PUBLIC_IP',
    'ssh_user': 'root',
    'ssh_key': '$SSH_KEY',
    'port_range': [5001, 5200],
    'max_containers': 12,
})
with open('$CONFIG', 'w') as f:
    yaml.dump(config, f, default_flow_style=False)
print('Worker added to config')
"

echo "Restart dashboard to pick up new worker:"
echo "  systemctl restart strike7-dashboard"
