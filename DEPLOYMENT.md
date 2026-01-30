# Strike7 Deployment Guide

## Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  Local WSL2     │  git    │  GitHub         │  git    │   VPS (Prod)    │
│  Development    │ ──push─>│  Repository     │ ─auto──>│  139.59.80.137  │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

## Daily Workflow

### Making Changes Locally

1. Edit files in `~/workspace/strike7-benchmarks/`
2. Test locally (optional)
3. Commit and push:
   ```bash
   git add .
   git commit -m "Your change description"
   git push origin main
   ```
4. GitHub Actions automatically deploys to VPS (1-2 minutes)

### Regenerating Dashboard Data

```bash
python3 dashboard/scripts/generate_benchmarks_json.py
git add dashboard/data/benchmarks.json
git commit -m "update: Regenerate benchmarks.json"
git push origin main
```

### Manual VPS Deployment

If GitHub Actions fails, deploy manually:

```bash
ssh root@139.59.80.137 "/opt/strike7-deploy.sh"
```

### Syncing VPS Changes to Local

If you made changes directly on VPS:

```bash
./sync-vps-ports.sh
git add .
git commit -m "sync: Pull VPS changes"
git push origin main
```

## Port Allocation

- **EASY:** 5001-5009 (9 benchmarks)
- **MED:** 5010-5025 (16 benchmarks)
- **HARD:** 5030-5043 (14 benchmarks)
- **VHARD:** 5050-5063 (14 benchmarks)
- **CVE:** 5070-5080 (11 benchmarks)
- **Dashboard API:** 5000

## Monitoring

### Check Deployment Status

```bash
ssh root@139.59.80.137 "tail -f /var/log/strike7-deploy.log"
```

### Check Dashboard Status

```bash
ssh root@139.59.80.137 "systemctl status strike7-dashboard"
```

### View Running Containers

```bash
ssh root@139.59.80.137 "docker ps --format 'table {{.Names}}\t{{.Ports}}'"
```

## Troubleshooting

### GitHub Actions failing?

1. Check workflow logs: https://github.com/Azi023/strike7.ai-benchmark-harness/actions
2. Verify GitHub Secrets are configured correctly
3. Test SSH manually: `ssh root@139.59.80.137 "echo test"`

### Dashboard not updating?

```bash
ssh root@139.59.80.137 "systemctl restart strike7-dashboard"
```

### Port conflicts?

```bash
# Stop all benchmark containers
ssh root@139.59.80.137 "cd /opt/strike7.ai-benchmark-harness/scripts && ./manage-containers.sh stop-all"
```

## Reference Links

- **GitHub Repository:** https://github.com/Azi023/strike7.ai-benchmark-harness
- **GitHub Actions:** https://github.com/Azi023/strike7.ai-benchmark-harness/actions
- **VPS Dashboard:** http://139.59.80.137:5000/
