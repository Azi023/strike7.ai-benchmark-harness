# Phase 6B Deployment Guide

**Version:** 1.0
**Date:** 2026-01-22
**Benchmarks:** 20 new benchmarks (S7BEN-VHARD-011 through S7BEN-CVE-011)

---

## Prerequisites

### System Requirements
- **OS:** Linux (Ubuntu 20.04+), macOS, or Windows with WSL2
- **Docker:** 20.10.0 or higher
- **Docker Compose:** 2.0.0 or higher
- **RAM:** 4GB minimum (8GB recommended for running multiple benchmarks)
- **Disk:** 10GB free space

### Software Dependencies
```bash
# Check Docker
docker --version

# Check Docker Compose
docker-compose --version

# Optional tools for testing
curl --version
python3 --version
```

---

## Quick Start Deployment

### 1. Deploy a Single Benchmark

```bash
# Navigate to benchmark directory
cd benchmarks/S7BEN-MED-014

# Start the benchmark
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Test the application
curl http://localhost:8100/

# Stop the benchmark
docker-compose down
```

### 2. Deploy All Phase 6B Benchmarks

**Warning:** This will start 20 containers simultaneously and requires significant resources.

```bash
# Create a script to start all Phase 6B benchmarks
cat > start-all-phase6b.sh << 'EOF'
#!/bin/bash
BENCHMARKS=(
  "S7BEN-VHARD-011" "S7BEN-VHARD-012" "S7BEN-HARD-014" "S7BEN-HARD-015" "S7BEN-MED-013"
  "S7BEN-VHARD-013" "S7BEN-VHARD-014" "S7BEN-HARD-016" "S7BEN-HARD-017" "S7BEN-MED-014"
  "S7BEN-HARD-018" "S7BEN-HARD-019" "S7BEN-MED-015" "S7BEN-MED-016"
  "S7BEN-CVE-006" "S7BEN-CVE-007" "S7BEN-CVE-008" "S7BEN-CVE-009" "S7BEN-CVE-010" "S7BEN-CVE-011"
)

for benchmark in "${BENCHMARKS[@]}"; do
  echo "Starting $benchmark..."
  cd "benchmarks/$benchmark" && docker-compose up -d && cd ../..
done

echo "All Phase 6B benchmarks started!"
EOF

chmod +x start-all-phase6b.sh
./start-all-phase6b.sh
```

### 3. Deploy by Category

#### Authentication Benchmarks
```bash
for id in VHARD-011 VHARD-012 HARD-014 HARD-015 MED-013; do
  cd benchmarks/S7BEN-$id && docker-compose up -d && cd ../..
done
```

#### Business Logic Benchmarks
```bash
for id in VHARD-013 VHARD-014 HARD-016 HARD-017 MED-014; do
  cd benchmarks/S7BEN-$id && docker-compose up -d && cd ../..
done
```

#### Misconfiguration Benchmarks
```bash
for id in HARD-018 HARD-019 MED-015 MED-016; do
  cd benchmarks/S7BEN-$id && docker-compose up -d && cd ../..
done
```

#### CVE Benchmarks
```bash
for id in CVE-006 CVE-007 CVE-008 CVE-009 CVE-010 CVE-011; do
  cd benchmarks/S7BEN-$id && docker-compose up -d && cd ../..
done
```

---

## Port Mappings

All Phase 6B benchmarks use unique ports:

| Benchmark ID | Name | Port |
|--------------|------|------|
| S7BEN-VHARD-011 | 2FA Session State Bypass | 8087 |
| S7BEN-VHARD-012 | OAuth State Confusion | 8091 |
| S7BEN-HARD-014 | Password Reset Token Reuse | 8093 |
| S7BEN-HARD-015 | Session Fixation | 8094 |
| S7BEN-VHARD-013 | Race Condition Double Spend | 8095 |
| S7BEN-VHARD-014 | Negative Quantity | 8096 |
| S7BEN-HARD-016 | Workflow State Manipulation | 8097 |
| S7BEN-HARD-017 | Client-Side Price | 8098 |
| S7BEN-MED-013 | Weak Password Policy | 8099 |
| S7BEN-MED-014 | Coupon Code Reuse | 8100 |
| S7BEN-HARD-018 | K8s RBAC Escalation | 8101 |
| S7BEN-HARD-019 | Docker Socket Exposure | 8102 |
| S7BEN-MED-015 | Flask Debug Mode | 8103 |
| S7BEN-MED-016 | Default Credentials | 8104 |
| S7BEN-CVE-006 | runc Container Escape | 8105 |
| S7BEN-CVE-007 | HTTP/2 Rapid Reset | 8106 |
| S7BEN-CVE-008 | PAN-OS Command Injection | 8107 |
| S7BEN-CVE-009 | Confluence Privilege Escalation | 8108 |
| S7BEN-CVE-010 | TeamCity Auth Bypass | 8109 |
| S7BEN-CVE-011 | ActiveMQ Deserialization | 8110 |

**Ensure these ports are free before deployment:**
```bash
# Check if ports are available
for port in {8087,8091,8093..8110}; do
  if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Port $port is in use"
  fi
done
```

---

## Testing Deployed Benchmarks

### Manual Testing

#### Example: S7BEN-MED-014 (Coupon Reuse)
```bash
# Apply coupon
curl -c cookies.txt -b cookies.txt -X POST http://localhost:8100/apply-coupon \
  -H "Content-Type: application/json" \
  -d '{"code":"SAVE50"}'

# Make first purchase (should be $50)
curl -c cookies.txt -b cookies.txt -X POST http://localhost:8100/purchase \
  -H "Content-Type: application/json"

# Make second purchase (should return flag)
curl -c cookies.txt -b cookies.txt -X POST http://localhost:8100/purchase \
  -H "Content-Type: application/json"
```

#### Example: S7BEN-HARD-018 (K8s RBAC)
```bash
# Get service account token
TOKEN=$(curl -s http://localhost:8101/api/token | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

# Access secrets with token
curl -H "Authorization: Bearer $TOKEN" http://localhost:8101/k8s/secrets
```

### Automated Testing
```bash
# Run the Phase 6B test script
./scripts/test-phase6b-benchmarks.sh

# View results
cat phase6b_test_summary.txt
```

### Health Checks
```bash
# Check all running containers
docker ps --filter "name=s7ben"

# Check specific benchmark health
curl http://localhost:8100/health
```

---

## Exploitation Examples

### Using Exploit Scripts

Each benchmark includes ready-to-use exploit scripts:

```bash
cd benchmarks/S7BEN-MED-014

# Bash exploit
./exploit.sh

# Python exploit
python3 exploit.py

# Or with target argument
python3 exploit.py http://localhost:8100
```

### Manual Exploitation Workflow

1. **Reconnaissance**
   ```bash
   curl http://localhost:8100/
   curl http://localhost:8100/health
   ```

2. **Identify Vulnerability**
   - Read benchmark README.md
   - Check benchmark.yaml for hints
   - Analyze application behavior

3. **Exploit**
   - Use curl commands
   - Run Python scripts
   - Modify provided exploits

4. **Capture Flag**
   - Flags follow format: `S7BEN{category_randomstring}`
   - Example: `S7BEN{c0up0n_reuse_3khfapup}`

---

## Monitoring and Logs

### View Container Logs
```bash
# Real-time logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs app
```

### Check Container Status
```bash
# List all Phase 6B containers
docker ps --filter "name=s7ben" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check resource usage
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### Access Telemetry
```bash
# Most benchmarks expose telemetry endpoints
curl http://localhost:8100/telemetry

# Example response:
# {"exploitation_attempts": 3, "flag_captured": true, "start_time": 1234567890}
```

---

## Troubleshooting

### Container Won't Start

**Problem:** `docker-compose up -d` fails

**Solutions:**
```bash
# Check Docker daemon
sudo systemctl status docker

# Check port conflicts
lsof -i :8100

# View detailed error
docker-compose up

# Rebuild image
docker-compose build --no-cache
docker-compose up -d
```

### Application Not Responding

**Problem:** Container running but app not accessible

**Solutions:**
```bash
# Check if app is listening
docker-compose exec app netstat -tuln

# Check container logs for errors
docker-compose logs app | tail -50

# Restart container
docker-compose restart

# Check firewall
sudo ufw status
```

### Port Already in Use

**Problem:** `Error: port is already allocated`

**Solutions:**
```bash
# Find what's using the port
lsof -i :8100

# Kill the process
kill -9 <PID>

# Or change the port in docker-compose.yml
```

### Out of Memory

**Problem:** System runs out of memory with multiple benchmarks

**Solutions:**
```bash
# Stop some containers
docker stop $(docker ps -q --filter "name=s7ben")

# Increase Docker memory limit (Docker Desktop)
# Settings → Resources → Memory → Increase to 8GB

# Deploy benchmarks in batches
# Start 5 at a time instead of all 20
```

### Flag Not Appearing

**Problem:** Exploit runs but no flag returned

**Solutions:**
```bash
# Check container logs for generated flag
docker logs <container_name> | grep "S7BEN{"

# Verify exploit conditions are met
# Some flags require specific sequences (e.g., 2 purchases for coupon reuse)

# Try fresh container
docker-compose down
docker-compose up -d
```

---

## Cleanup

### Stop Single Benchmark
```bash
cd benchmarks/S7BEN-MED-014
docker-compose down
```

### Stop All Phase 6B Benchmarks
```bash
# Stop and remove containers
for id in VHARD-{011,012,013,014} HARD-{014,015,016,017,018,019} MED-{013,014,015,016} CVE-{006..011}; do
  cd benchmarks/S7BEN-$id && docker-compose down 2>/dev/null && cd ../..
done
```

### Complete Cleanup (Containers + Images)
```bash
# Stop all S7BEN containers
docker stop $(docker ps -q --filter "name=s7ben")

# Remove containers
docker rm $(docker ps -a -q --filter "name=s7ben")

# Remove images
docker rmi $(docker images --filter "reference=s7ben*" -q)

# Remove volumes
docker volume prune -f

# Remove networks
docker network prune -f
```

---

## Production Deployment Notes

### Security Considerations

⚠️ **WARNING:** These benchmarks contain intentional vulnerabilities. Do NOT deploy on public networks or production environments.

**Recommended Setup:**
- Deploy only on isolated networks
- Use firewall rules to restrict access
- Run on dedicated testing infrastructure
- Monitor for unexpected exploitation attempts

### Network Isolation

```bash
# Create isolated Docker network
docker network create --driver bridge strike7-test-net

# Modify docker-compose.yml to use custom network
# Add to each docker-compose.yml:
# networks:
#   default:
#     external:
#       name: strike7-test-net
```

### Resource Limits

Add resource limits to docker-compose.yml:
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          memory: 256M
```

---

## Performance Optimization

### Pre-build Images
```bash
# Build all images before starting
for id in VHARD-{011,012,013,014} HARD-{014,015,016,017,018,019} MED-{013,014,015,016} CVE-{006..011}; do
  cd benchmarks/S7BEN-$id && docker-compose build && cd ../..
done
```

### Use Docker Build Cache
```bash
# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
```

### Parallel Deployment
```bash
# Start benchmarks in parallel (requires GNU parallel)
parallel 'cd benchmarks/{} && docker-compose up -d' ::: S7BEN-VHARD-{011..014} S7BEN-HARD-{014..019} S7BEN-MED-{013..016} S7BEN-CVE-{006..011}
```

---

## Dashboard Integration

The benchmarks are pre-configured in the dashboard:

```bash
# Start dashboard (if available)
cd dashboard
python3 app.py

# Access at http://localhost:5000
# View all 64 benchmarks including Phase 6B
```

---

## Support and Documentation

**Documentation Files:**
- Detailed completion report: `docs/PHASE6B_COMPLETION.md`
- Full inventory: `docs/BENCHMARK_INVENTORY.md`
- Individual benchmark READMEs: `benchmarks/S7BEN-*/README.md`

**Testing:**
- Automated test script: `scripts/test-phase6b-benchmarks.sh`
- Test results: `phase6b_test_summary.txt`

**Quick Reference:**
```bash
# Count benchmarks
./scripts/count-benchmarks.sh

# List all Phase 6B benchmarks
ls -d benchmarks/S7BEN-{VHARD-011,VHARD-012,HARD-014,HARD-015,MED-013,VHARD-013,VHARD-014,HARD-016,HARD-017,MED-014,HARD-018,HARD-019,MED-015,MED-016,CVE-006,CVE-007,CVE-008,CVE-009,CVE-010,CVE-011}
```

---

*Deployment Guide v1.0 - Strike7 Security Benchmarks*
*For issues or questions, refer to the individual benchmark documentation*
