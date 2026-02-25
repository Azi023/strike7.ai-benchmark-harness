# Strike7 Benchmark Platform - Project Summary

## 🎯 What Strike7 Does

**Strike7 is an AI-powered penetration testing benchmark platform that evaluates autonomous AI agent capabilities in cybersecurity.** It provides 64 isolated Docker container challenges across difficulty levels (EASY, MED, HARD, VHARD, CVE) that test AI agents' ability to discover, exploit, and validate security vulnerabilities without human intervention.

**Success means:**
- All 64 benchmarks can start/stop without port conflicts
- Dashboard correctly displays benchmark status (Not Running → Running → Stopped)
- AI agents can connect via MCP to autonomously test benchmarks
- Flag submission validates correctly (pass@k and pass^k metrics)
- Containers properly isolate and don't interfere with each other

---

## 📊 Current Project Status

### ✅ What's Working (Phase 7 Complete)

1. **All 91 Docker Images Built** (64 benchmarks + 27 service containers)
   - EASY: 9 benchmarks (ports 5001-5009)
   - MED: 16 benchmarks (ports 5010-5025)
   - HARD: 14 benchmarks (ports 5030-5043)
   - VHARD: 14 benchmarks (ports 5050-5063)
   - CVE: 11 benchmarks (ports 5070-5080)

2. **Dashboard Running on VPS**
   - URL: http://139.59.80.137
   - Backend: Flask Python app
   - Frontend: HTML/CSS/JavaScript with real-time status updates
   - Systemd service: `strike7-dashboard.service`

3. **Port Conflict Resolution Complete**
   - All docker-compose.yml files updated with unique ports
   - No more "port already allocated" errors
   - Port allocation scheme documented

4. **Security Tools Installed on VPS**
   - nmap, sqlmap, nikto, gobuster, hydra, john, hashcat
   - All ready for AI agent use

5. **VPS Infrastructure**
   - Ubuntu 24.04.3 LTS
   - IP: 139.59.80.137
   - 4GB RAM, 76% memory usage
   - 4894 processes, low swap usage

### ⚠️ Known Issues (Phase 8 In Progress)

1. **Dashboard/Container Sync Issue**
   - Dashboard shows "8 active containers"
   - Frontend shows "Not Running" but containers may actually be running
   - Root cause: `data/benchmarks.json` missing port updates OR container status polling issues

2. **Stop Button Inconsistent**
   - Sometimes visible, sometimes not
   - May be related to WebSocket/polling disconnects
   - Backend API works, frontend state management needs investigation

3. **Local/VPS Codebase Out of Sync**
   - VPS: `/opt/strike7.ai-benchmark-harness/` (production)
   - Local WSL2: `~/workspace/strike7-benchmarks/` (development)
   - Port fixes applied on VPS but not yet synced to local
   - No Git workflow yet (manual rsync currently)

4. **MCP Server Built But Not Tested**
   - Server code exists at `/opt/strike7-mcp-server/`
   - Not yet configured in Claude Desktop
   - AI agent integration pending

5. **No CI/CD Pipeline Yet**
   - Manual SSH deployment
   - GitHub Actions workflow designed but not implemented
   - Auto-deploy on git push not active

---

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Strike7 Platform                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │  Dashboard   │◄────►│  Flask API   │                    │
│  │  (Frontend)  │      │  (Backend)   │                    │
│  │  Port 80     │      │  Port 5000   │                    │
│  └──────────────┘      └──────┬───────┘                    │
│                               │                             │
│                               ▼                             │
│                    ┌──────────────────┐                     │
│                    │ Docker Engine    │                     │
│                    │ Container Mgmt   │                     │
│                    └──────┬───────────┘                     │
│                           │                                 │
│         ┌─────────────────┼─────────────────┐              │
│         │                 │                 │              │
│         ▼                 ▼                 ▼              │
│  ┌────────────┐    ┌────────────┐   ┌────────────┐       │
│  │ S7BEN-EASY │    │ S7BEN-MED  │   │ S7BEN-HARD │       │
│  │ Containers │    │ Containers │   │ Containers │       │
│  │ 5001-5009  │    │ 5010-5025  │   │ 5030-5063  │       │
│  └────────────┘    └────────────┘   └────────────┘       │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │         MCP Server (AI Agent Interface)          │    │
│  │         Port: stdio (Claude Desktop)             │    │
│  └──────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Key Modules/Services

**Backend (Python/Flask):**
- `dashboard/app.py` - Main Flask application, API routes
- `dashboard/api/` - RESTful API endpoints
- `dashboard/safety_daemon.py` - Container safety monitoring
- `dashboard/agent_client.py` - AI agent interaction handler
- `dashboard/data/benchmarks.json` - Benchmark metadata and config

**Benchmarks:**
- `benchmarks/S7BEN-{CATEGORY}-{NUM}/` - 64 independent challenge directories
- Each contains:
  - `docker-compose.yml` - Container orchestration
  - `Dockerfile` / pre-built image reference
  - `README.md` - Challenge description
  - `FLAG.txt` - Validation flag (not exposed to agents)

**MCP Server (Node.js):**
- `/opt/strike7-mcp-server/index.js` - Model Context Protocol server
- Tools: list_benchmarks, start_benchmark, stop_benchmark, submit_flag, etc.
- Connects Claude AI to Strike7 API

### Data Flow: Benchmark Start → Stop

```
1. User clicks "Start" on Dashboard
   └─► POST /api/benchmark/{id}/start

2. Flask API receives request
   └─► Validates benchmark exists
   └─► Checks no other container running (safety)

3. Docker Compose Up
   └─► cd /opt/strike7.ai-benchmark-harness/benchmarks/{id}
   └─► docker-compose up -d
   └─► Assigns external port (5001-5080 range)

4. Container Health Check
   └─► Docker healthcheck monitors app readiness
   └─► Status changes: starting → healthy → running

5. Dashboard Polls Status
   └─► GET /api/containers/status every 2 seconds
   └─► Frontend updates UI: "Not Running" → "Running"
   └─► Stop button becomes visible

6. User clicks "Stop"
   └─► POST /api/benchmark/{id}/stop
   └─► docker-compose down
   └─► Status returns to "Not Running"
```

### External Dependencies

- **Docker Engine** - Container runtime
- **Docker Compose** - Multi-container orchestration
- **Nginx** (optional) - Reverse proxy for dashboard
- **Systemd** - Service management (`strike7-dashboard.service`)
- **Node.js** - MCP server runtime
- **Python 3.11+** - Backend application

### Environment Variables

**Dashboard (.env or systemd):**
```bash
FLASK_APP=app.py
FLASK_ENV=production
BENCHMARKS_DIR=/opt/strike7.ai-benchmark-harness/benchmarks
DOCKER_SOCKET=/var/run/docker.sock
LOG_LEVEL=INFO
```

**MCP Server:**
```bash
STRIKE7_API_URL=http://localhost:5000
NODE_ENV=production
```

---

## 🚫 What NOT to Touch

### Critical Production Files (DO NOT MODIFY)
- `/etc/systemd/system/strike7-dashboard.service` - Production service config
- `/var/log/strike7-*` - Production logs (read-only)
- `docker-compose.yml.backup` files - Rollback safety copies
- `.env.production` (if exists) - Production secrets

### Docker Infrastructure
- Base images: `base-web-app`, `base-java-vuln`, etc. (already built, don't rebuild)
- Running containers: Don't manually docker stop/rm (use API)
- Docker networks: Auto-managed by compose

### VPS System Config
- `/opt/strike7-deploy.sh` - CI/CD deploy script (once set up)
- SSH keys for deployment
- Firewall rules (ports 80, 5000, 5001-5080)

### Git Workflow (Once Implemented)
- `.github/workflows/deploy.yml` - Auto-deploy config
- Do NOT commit to main without testing locally first
- Do NOT force push to main

---

## 📂 Local Directory Structure (Development)

```
~/workspace/strike7-benchmarks/
├── README.md                          # Project documentation
├── QUICKSTART.md                      # Getting started guide
├── LICENSE                            # License file
├── .gitignore                         # Git ignore patterns
├── .github/
│   └── workflows/
│       └── deploy.yml                 # CI/CD workflow (pending)
│
├── benchmarks/                        # 64 benchmark challenges
│   ├── S7BEN-EASY-001/
│   │   ├── README.md                  # Challenge description
│   │   ├── docker-compose.yml         # ⚠️ Port: 5001
│   │   ├── Dockerfile (optional)      # If needs custom build
│   │   └── app/                       # Challenge application code
│   ├── S7BEN-EASY-002/
│   │   └── docker-compose.yml         # ⚠️ Port: 5002
│   └── ... (62 more)
│
├── dashboard/                         # Flask web dashboard
│   ├── app.py                         # 🔥 Main Flask app (ENTRYPOINT)
│   ├── requirements.txt               # Python dependencies
│   ├── config/
│   │   └── settings.py                # App configuration
│   ├── api/                           # 🔥 REST API routes
│   │   ├── benchmarks.py              # Benchmark CRUD
│   │   ├── containers.py              # Docker container ops
│   │   └── flags.py                   # Flag validation
│   ├── data/
│   │   └── benchmarks.json            # ⚠️ Benchmark metadata
│   ├── static/
│   │   ├── css/                       # Dashboard styles
│   │   └── js/                        # Frontend logic
│   ├── templates/
│   │   └── index.html                 # Dashboard HTML
│   └── tests/                         # Unit tests (pending)
│
├── mcp-server/                        # 🔥 AI Agent MCP Interface
│   ├── index.js                       # MCP server implementation
│   ├── package.json                   # Node.js dependencies
│   └── README.md                      # MCP usage guide
│
├── docker-base-images/                # Reusable Docker base images
│   ├── base-web-app/
│   ├── base-java-vuln/
│   └── base-modsec-waf/
│
├── scripts/                           # Utility scripts
│   ├── build-all-benchmarks.sh        # Build all Docker images
│   ├── sync-from-vps.sh               # Pull VPS changes to local
│   └── test-port-allocation.sh        # Verify no port conflicts
│
└── docs/                              # Documentation
    ├── ARCHITECTURE.md
    ├── API.md
    └── DEPLOYMENT.md
```

---

## 🎯 Critical Files & Why They Matter

### Top 20 Most Important Files

| File | Purpose | Why Critical |
|------|---------|--------------|
| `dashboard/app.py` | Flask app entry point | Defines all API routes, handles requests |
| `dashboard/api/benchmarks.py` | Benchmark CRUD operations | Start/stop container logic |
| `dashboard/api/containers.py` | Docker container management | Interfaces with Docker socket |
| `dashboard/api/flags.py` | Flag validation logic | Scoring/evaluation system |
| `dashboard/data/benchmarks.json` | Benchmark registry | **⚠️ SYNC ISSUE:** Missing port updates |
| `dashboard/config/settings.py` | App configuration | Environment variables, paths |
| `dashboard/static/js/main.js` | Frontend logic | **⚠️ ISSUE:** Stop button state management |
| `dashboard/templates/index.html` | Dashboard UI | User interaction layer |
| `dashboard/safety_daemon.py` | Container safety monitor | Prevents multiple concurrent runs |
| `benchmarks/*/docker-compose.yml` | Container orchestration | **Port allocation: 5001-5080** |
| `mcp-server/index.js` | AI agent interface | Claude → Strike7 integration |
| `scripts/build-all-benchmarks.sh` | Mass Docker build | CI/CD critical |
| `.github/workflows/deploy.yml` | Auto-deploy config | **Pending implementation** |
| `docker-base-images/*/Dockerfile` | Base image definitions | Performance optimization |
| `/opt/strike7-deploy.sh` (VPS) | Production deploy script | **VPS only - do not edit locally** |
| `/etc/systemd/system/strike7-dashboard.service` | Systemd config | **VPS only - production service** |

---

## 🔄 Current Workflow (Manual)

```bash
# Development Flow (Local WSL2)
1. Edit code in ~/workspace/strike7-benchmarks/
2. Test locally (if possible - requires Docker)
3. Commit to Git (when Git workflow is set up)
4. Manual sync: rsync to VPS OR ssh + git pull

# Production Deployment (VPS)
1. SSH into root@139.59.80.137
2. cd /opt/strike7.ai-benchmark-harness/
3. Make changes OR pull from Git
4. systemctl restart strike7-dashboard
5. Verify at http://139.59.80.137
```

---

## 🎯 Success Metrics

### Smoke Test Checklist

**Basic Health:**
- [ ] Dashboard loads at http://139.59.80.137
- [ ] Shows "64 Total Benchmarks"
- [ ] Shows "11/10 OWASP Categories"
- [ ] Active container count is accurate

**Benchmark Lifecycle (EASY category):**
- [ ] Click Start on S7BEN-EASY-001
- [ ] Status changes to "Running"
- [ ] Port shows 5001
- [ ] Stop button becomes visible
- [ ] Click Stop
- [ ] Status returns to "Not Running"

**Multi-Benchmark Test:**
- [ ] Start 3 benchmarks simultaneously (EASY-001, MED-001, HARD-001)
- [ ] All start without port conflicts
- [ ] Dashboard shows "3 Active Containers"
- [ ] All accessible at correct ports (5001, 5010, 5030)
- [ ] Stop all 3
- [ ] All stop cleanly

**API Tests:**
- [ ] GET /api/benchmarks returns 64 items
- [ ] GET /api/containers/status returns current state
- [ ] POST /api/benchmark/S7BEN-EASY-001/start succeeds
- [ ] POST /api/benchmark/S7BEN-EASY-001/stop succeeds
- [ ] POST /api/benchmark/S7BEN-EASY-001/submit-flag validates correctly

**MCP Integration (Phase 8):**
- [ ] Claude Code can call list_benchmarks
- [ ] Claude Code can call start_benchmark
- [ ] Claude Code can call check_container_status
- [ ] Claude Code can call submit_flag
- [ ] Claude Code can autonomously solve S7BEN-EASY-001

---

## 🚀 Next Phase: Phase 8 Goals

1. **Fix Dashboard/Container Sync**
   - Update `data/benchmarks.json` with ports
   - Fix frontend status polling
   - Implement proper WebSocket or SSE for real-time updates

2. **Complete Git Workflow**
   - Initialize local Git repo
   - Push to GitHub
   - Setup GitHub Actions auto-deploy
   - Test local → VPS sync

3. **MCP Integration Testing**
   - Configure Claude Desktop to use MCP server
   - Test all 7 MCP tools
   - Run autonomous benchmark solve attempt
   - Document agent performance metrics

4. **Comprehensive Smoke Testing**
   - Create automated test suite
   - Test all 64 benchmarks (at least start/stop)
   - Verify no port conflicts
   - Document any broken benchmarks

5. **QA Agent Development**
   - Build Strike7QAAgent for automated testing
   - Systematic dashboard feature verification
   - Regression test suite

---

## 📝 Development Guidelines

### Before Making Changes:

1. **Sync local with VPS first:**
   ```bash
   bash scripts/sync-from-vps.sh
   ```

2. **Test locally if possible:**
   ```bash
   cd dashboard
   python app.py
   # Test at http://localhost:5000
   ```

3. **Make small, targeted changes:**
   - One feature/fix per commit
   - Test after each change
   - Don't refactor and add features simultaneously

4. **Commit frequently:**
   ```bash
   git add [specific files]
   git commit -m "Fix: [specific issue]"
   ```

### After Making Changes:

1. **Run smoke tests locally**
2. **Deploy to VPS (manual for now):**
   ```bash
   rsync -avz ~/workspace/strike7-benchmarks/ root@139.59.80.137:/opt/strike7.ai-benchmark-harness/
   ssh root@139.59.80.137 "systemctl restart strike7-dashboard"
   ```
3. **Verify on production:** http://139.59.80.137
4. **Monitor logs:** `ssh root@139.59.80.137 "journalctl -u strike7-dashboard -f"`

---

## 🔍 Debugging Quick Reference

### Dashboard won't start:
```bash
ssh root@139.59.80.137
systemctl status strike7-dashboard
journalctl -u strike7-dashboard -n 100
```

### Container won't start:
```bash
ssh root@139.59.80.137
cd /opt/strike7.ai-benchmark-harness/benchmarks/S7BEN-EASY-001
docker-compose ps
docker-compose logs
```

### Port conflict:
```bash
ssh root@139.59.80.137
docker ps -a
# Find conflicting container
docker stop [container-id]
docker rm [container-id]
```

### Status not updating:
```bash
# Check frontend polling
curl http://139.59.80.137/api/containers/status

# Check Docker socket permissions
ls -la /var/run/docker.sock
```

---

## 📞 Key Information

- **VPS IP:** 139.59.80.137
- **Dashboard URL:** http://139.59.80.137
- **Dashboard Port:** 80 (Nginx) → 5000 (Flask)
- **Benchmark Ports:** 5001-5080
- **VPS Path:** `/opt/strike7.ai-benchmark-harness/`
- **Local Path:** `~/workspace/strike7-benchmarks/`
- **MCP Server:** `/opt/strike7-mcp-server/`
- **Systemd Service:** `strike7-dashboard.service`

---

**Last Updated:** Feb 10, 2026  
**Current Phase:** 8 (CI/CD & QA Testing)  
**Status:** Port conflicts resolved, dashboard running, MCP pending integration
