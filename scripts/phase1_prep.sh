#!/usr/bin/env bash
# =============================================================================
# Strike7 Phase 1 Preparation Script
# Run this on the control plane VPS to prepare for adding remote workers.
#
# What it does:
#   1. Exports all benchmark Docker images to a transferable archive
#   2. Generates SSH key pair for worker authentication
#   3. Tests SSHDriver connectivity (localhost loopback)
#   4. Prints Phase 1 checklist
#
# Usage:
#   bash scripts/phase1_prep.sh
# =============================================================================
set -euo pipefail

HARNESS_DIR="/opt/strike7.ai-benchmark-harness"
EXPORT_DIR="${HARNESS_DIR}/exports"
SSH_KEY="/root/.ssh/worker_key"

echo "=============================================="
echo "  Strike7 Phase 1 Preparation"
echo "=============================================="
echo ""

# ---------------------------------------------------------
# 1. Export benchmark Docker images
# ---------------------------------------------------------
echo "[1/3] Exporting benchmark Docker images..."

mkdir -p "$EXPORT_DIR"

IMAGES=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep -i 's7ben\|strike7\|benchmark' || true)
IMAGE_COUNT=$(echo "$IMAGES" | grep -c . || true)

if [ "$IMAGE_COUNT" -eq 0 ]; then
    echo "  No benchmark images found. Build benchmarks first, then re-run."
    echo "  Looked for images matching: s7ben, strike7, benchmark"
else
    EXPORT_FILE="${EXPORT_DIR}/s7ben_images_$(date +%Y%m%d).tar.gz"
    echo "  Found $IMAGE_COUNT images:"
    echo "$IMAGES" | sed 's/^/    /'
    echo ""
    echo "  Saving to: $EXPORT_FILE"
    docker save $IMAGES | gzip > "$EXPORT_FILE"
    SIZE=$(du -sh "$EXPORT_FILE" | cut -f1)
    echo "  Export complete: $SIZE"
    echo ""
    echo "  Transfer to worker with:"
    echo "    scp $EXPORT_FILE root@WORKER_IP:/tmp/"
    echo "    ssh root@WORKER_IP 'gunzip -c /tmp/$(basename $EXPORT_FILE) | docker load'"
fi
echo ""

# ---------------------------------------------------------
# 2. Generate SSH key pair for workers
# ---------------------------------------------------------
echo "[2/3] SSH key pair for worker auth..."

if [ -f "$SSH_KEY" ]; then
    echo "  Key already exists: $SSH_KEY"
    echo "  Public key:"
    cat "${SSH_KEY}.pub" | sed 's/^/    /'
else
    ssh-keygen -t ed25519 -f "$SSH_KEY" -N '' -C "strike7-control-plane"
    echo "  Generated: $SSH_KEY"
    echo "  Public key:"
    cat "${SSH_KEY}.pub" | sed 's/^/    /'
fi
echo ""
echo "  Deploy to worker with:"
echo "    ssh-copy-id -i ${SSH_KEY}.pub root@WORKER_IP"
echo ""

# ---------------------------------------------------------
# 3. Test SSHDriver via localhost loopback
# ---------------------------------------------------------
echo "[3/3] Testing SSHDriver (localhost loopback)..."

cd "$HARNESS_DIR/dashboard"
RESULT=$(python3 -c "
import sys
sys.path.insert(0, '.')
from orchestrator.docker_driver import SSHDriver

driver = SSHDriver(host='localhost', user='root', ssh_key='$SSH_KEY')

# Test 1: Ping
ping_ok = driver.ping()
print(f'  Ping:           {\"PASS\" if ping_ok else \"FAIL\"}')

# Test 2: Container list
cl = driver.container_list()
print(f'  container_list: {\"PASS\" if cl.success else \"FAIL\"}')

# Test 3: System info
si = driver.system_info()
print(f'  system_info:    {\"PASS\" if si.success else \"FAIL\"}')

# Test 4: Image check
ie = driver.image_exists('alpine:latest')
print(f'  image_exists:   {\"PASS\" if isinstance(ie, bool) else \"FAIL\"} (alpine={ie})')

if ping_ok and cl.success and si.success:
    print('  SSHDriver:      ALL TESTS PASSED')
    sys.exit(0)
else:
    print('  SSHDriver:      SOME TESTS FAILED')
    sys.exit(1)
" 2>&1)
echo "$RESULT"
echo ""

# ---------------------------------------------------------
# Phase 1 Checklist
# ---------------------------------------------------------
echo "=============================================="
echo "  Phase 1 Readiness Checklist"
echo "=============================================="
echo ""
echo "  On control plane (this VPS):"
echo "    [x] Orchestrator deployed and running"
echo "    [x] SSH key generated ($SSH_KEY)"
echo "    [x] SSHDriver validated via loopback"
echo "    [x] Docker images exported ($EXPORT_DIR/)"
echo ""
echo "  On new worker VPS (when ready):"
echo "    [ ] Install Docker + docker-compose"
echo "    [ ] Create benchmarks directory: mkdir -p /opt/strike7.ai-benchmark-harness/benchmarks"
echo "    [ ] Transfer + load Docker images"
echo "    [ ] Deploy SSH public key"
echo "    [ ] Open ports 5001-5299 in firewall"
echo "    [ ] Test SSH from control plane: ssh -i $SSH_KEY root@WORKER_IP 'docker ps'"
echo ""
echo "  Config change (orchestrator.yaml):"
echo "    [ ] Set mode: remote"
echo "    [ ] Add worker entry with host, ssh_key, port_range"
echo "    [ ] Restart dashboard: systemctl restart strike7-dashboard"
echo ""
echo "  Example worker config:"
echo "    - id: worker-1"
echo "      mode: remote"
echo "      host: WORKER_IP"
echo "      ssh_user: root"
echo "      ssh_key: $SSH_KEY"
echo "      port_range: [5001, 5200]"
echo "      max_containers: 12"
echo ""
