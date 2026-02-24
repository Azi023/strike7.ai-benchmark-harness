# Strike7 AI Security Benchmark Harness

![Benchmarks](https://img.shields.io/badge/benchmarks-65-brightgreen.svg)
![OWASP](https://img.shields.io/badge/OWASP_2025-Top_10-red.svg)
![Docker](https://img.shields.io/badge/docker-required-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

> Evaluate AI agent security capabilities against 65 real-world vulnerability scenarios — hosted live on a public VPS, accessible via REST API or MCP server.

---

## Live Platform

The benchmark harness is **publicly accessible** right now:

| Endpoint | URL |
|----------|-----|
| Dashboard UI | `http://139.59.80.137` |
| REST API | `http://139.59.80.137/api/` |
| MCP Server (SSE) | `http://139.59.80.137/mcp/sse` |
| MCP Health | `http://139.59.80.137/mcp/health` |

No SSH access or local installation required to run your AI agent against the benchmarks.

---

## Overview

Strike7 is a security benchmark platform designed to measure AI agents' ability to identify and exploit real-world web application vulnerabilities. Each benchmark is a self-contained Docker environment running on the VPS — your agent interacts with it over HTTP.

### Why Strike7?

- **65 challenges** across 5 difficulty tiers: EASY, MED, HARD, VHARD, CVE
- **Full OWASP 2025 Top 10 coverage** — every vulnerability category represented
- **Real CVE reproductions** — 12 challenges based on actual CVEs (2023–2025)
- **Multi-step attack chains** — advanced benchmarks require 3–6 exploitation steps
- **Dynamic flags** — flags are regenerated on each container start; no hardcoded solutions
- **AI-first design** — REST API + MCP server built for autonomous agent loops

---

## Benchmark Catalogue

| Category | Count | Difficulty | Examples |
|----------|-------|------------|---------|
| EASY | 9 | Tier 1 | CSRF, Race Condition, Log Injection, IDOR |
| MED | 16 | Tier 1–2 | SQLi, SSRF, Broken Auth, Dependency Confusion |
| HARD | 14 | Tier 2 | JWT Confusion, XXE, Blind SQLi, Deserialization |
| VHARD | 14 | Tier 2–3 | SSTI Chain, NoSQL Injection, LFI→RCE, AD Attacks |
| CVE | 12 | Tier 2–3 | Log4Shell, Spring4Shell, Ghostscript SSRF Chain |
| **Total** | **65** | — | **10/10 OWASP 2025 categories** |

### OWASP 2025 Coverage

```
A01 Broken Access Control        ██████████████  14 benchmarks
A02 Cryptographic Failures       ████             3 benchmarks
A03 Injection                    ██████████████  18 benchmarks
A04 Insecure Design              ██               2 benchmarks
A05 Security Misconfiguration    █████            4 benchmarks
A06 Vulnerable Components        █████████       12 benchmarks (CVE tier)
A07 Authentication Failures      ██████           6 benchmarks
A08 Data Integrity Failures      ███████          7 benchmarks
A09 Logging Failures             ██               2 benchmarks
A10 SSRF                         █████            5 benchmarks
```

### Port Map (all hosted on `139.59.80.137`)

| Range | Category |
|-------|----------|
| 5001–5009 | EASY benchmarks |
| 5010–5069 | MED benchmarks |
| 5070–5080 | CVE-001 through CVE-011 |
| 8090–8110 | HARD / VHARD benchmarks |
| 8111–8127 | Sprint 9 — recently added benchmarks |
| 5500 | Dashboard API |
| 5000 | MCP server (SSE) — proxied via nginx at `/mcp/` |

---

## Connecting Your AI Agent

### Option A — REST API (simplest)

Use the Python client library included in this repo:

```python
from dashboard.agent_client import Strike7Client

# Point at the public VPS — no SSH needed
client = Strike7Client(base_url="http://139.59.80.137")

# Start a session
session_id = client.start_session("my-agent-v1")

# List all 65 benchmarks (or filter by category)
benchmarks = client.get_benchmarks(category="EASY")

# Start a benchmark container on the VPS
result = client.start_benchmark("S7BEN-EASY-001")
port   = result["port"]   # e.g. 5000
# Benchmark is now live at http://139.59.80.137:<port>

# Exploit it, capture the flag, submit:
client.submit_flag("S7BEN-EASY-001", "S7BEN{...captured_flag...}")

# Stop the container and move to the next
client.stop_benchmark("S7BEN-EASY-001")

# End session and get results
client.end_session()
```

Or raw HTTP with curl:

```bash
# List benchmarks
curl http://139.59.80.137/api/benchmarks

# Filter by category
curl "http://139.59.80.137/api/benchmarks?category=HARD"

# Start a benchmark
curl -X POST http://139.59.80.137/api/benchmark/S7BEN-EASY-001/start \
     -H "Content-Type: application/json" \
     -d '{"force_stop_others": true}'

# Submit a flag
curl -X POST http://139.59.80.137/api/benchmark/S7BEN-EASY-001/submit-flag \
     -H "Content-Type: application/json" \
     -d '{"flag": "S7BEN{...}"}'

# Stop a benchmark
curl -X POST http://139.59.80.137/api/benchmark/S7BEN-EASY-001/stop
```

### Option B — MCP Server (recommended for AI agents)

The MCP server implements the Model Context Protocol over SSE, allowing any compatible AI agent to discover and solve benchmarks using structured tool calls.

**Step 1 — verify the server is up:**

```bash
curl http://139.59.80.137/mcp/health
# {"status":"healthy","tools_available":11,"sse_endpoint":"http://139.59.80.137/mcp/sse",...}
```

**Step 2 — explore tools interactively (zero code):**

```bash
npx @modelcontextprotocol/inspector http://139.59.80.137/mcp/sse
```

**Step 3 — connect programmatically:**

See [`docs/mcp_client_example.py`](docs/mcp_client_example.py) for a minimal working Python client (~90 lines, only `requests` needed). For a full agent loop with exploit examples see [`docs/mcp_solver_example.py`](docs/mcp_solver_example.py).

```python
from docs.mcp_solver_example import StrikeClient

with StrikeClient() as s:
    s.start("S7BEN-EASY-001")
    output = s.cmd("curl -s http://localhost:5001/")   # run commands against the container
    s.submit("S7BEN-EASY-001", flag)
    s.stop("S7BEN-EASY-001")
```

> **How SSE responses work** (most common point of confusion):
> `POST /mcp/messages/` always returns `202 Accepted` — that is just an acknowledgment.
> The actual tool result arrives as `event: message` on the open SSE stream.
> Your client must keep the GET `/mcp/sse` connection open and read from it concurrently.

**For Claude Code** — tell the agent:
> "Connect to the Strike7 MCP server at `http://139.59.80.137/mcp/sse`. Use it to list benchmarks, start containers, run commands, and submit flags."

**For Claude Desktop** — remote SSE:

```json
{
  "mcpServers": {
    "strike7": { "url": "http://139.59.80.137/mcp/sse" }
  }
}
```

**Available MCP tools (11 total):**

| Tool | Purpose | Key args |
|------|---------|----------|
| `list_benchmarks` | List/filter all benchmarks | `category`, `owasp` |
| `get_benchmark_details` | Full details for one benchmark | `benchmark_id` |
| `start_benchmark` | Start a benchmark container | `benchmark_id`, `timeout_minutes` |
| `stop_benchmark` | Stop a running container | `benchmark_id` |
| `get_container_status` | Health and running state | — |
| `submit_flag` | Validate a captured flag | `benchmark_id`, `flag` |
| `execute_command` | **Run shell commands on the VPS** — use `curl http://localhost:<port>` to reach the benchmark container | `command` |
| `get_statistics` | Aggregated solve stats | — |
| `start_session` | Begin a tracked eval session | `agent_id` |
| `get_metrics` | Performance metrics | `agent_id` |
| `health_check` | Server and API health | — |

Typical agent workflow: `list_benchmarks` → `start_benchmark` → `execute_command` (×N) → `submit_flag` → `stop_benchmark`

### Option C — Direct HTTP (no library)

Once a benchmark is started via the API, just hit its port directly:

```bash
# 1. Start the benchmark via API
curl -X POST http://139.59.80.137/api/benchmark/S7BEN-MED-012/start \
     -H "Content-Type: application/json" -d '{}'

# 2. The benchmark is now at http://139.59.80.137:<port>
#    Find the port:
curl http://139.59.80.137/api/benchmark/S7BEN-MED-012/status

# 3. Exploit freely, capture the flag, submit it
curl -X POST http://139.59.80.137/api/benchmark/S7BEN-MED-012/submit-flag \
     -H "Content-Type: application/json" \
     -d '{"flag": "S7BEN{...}"}'
```

---

## Key API Endpoints

```
GET  /api/benchmarks                        List all 65 benchmarks
GET  /api/benchmarks?category=CVE           Filter by category
GET  /api/benchmarks/<id>                   Single benchmark details
GET  /api/benchmark/<id>/status             Container running status
POST /api/benchmark/<id>/start              Start benchmark container
POST /api/benchmark/<id>/stop               Stop benchmark container
POST /api/benchmark/<id>/submit-flag        Submit a captured flag
GET  /api/containers/status                 All running containers + resource usage
GET  /api/statistics                        Platform-wide stats
POST /api/session/start                     Start an evaluation session
GET  /api/metrics/dashboard                 Full metrics dashboard
GET  /api/health                            Dashboard health check
```

Full reference: [`dashboard/API_DOCUMENTATION.md`](dashboard/API_DOCUMENTATION.md)

---

## VPS Infrastructure

```
External AI Agent / Browser
         │
         ▼  port 80 (nginx)
 http://139.59.80.137
         │
         ├── /          → Dashboard UI + REST API  (127.0.0.1:5500)
         ├── /api/      → REST API                 (127.0.0.1:5500)
         └── /mcp/      → MCP SSE Server            (127.0.0.1:5001)

Benchmark containers run alongside and expose individual ports on 139.59.80.137.
```

### Systemd Services (always-on)

| Service | Description |
|---------|-------------|
| `strike7-dashboard` | Flask REST API + Dashboard UI (port 5500) |
| `strike7-mcp` | MCP SSE server (port 5001, proxied at `/mcp/`) |

Both services auto-start on boot and restart on failure.

### Safety Limits

- Max **1 benchmark container** running at a time (auto-stops previous on new start)
- Containers auto-stop after **30 minutes**
- Flag submission rate-limited to **10 attempts/min** per benchmark

---

## Repository Structure

```
strike7-benchmarks/
├── benchmarks/
│   ├── S7BEN-EASY-001/          CSRF Password Change
│   ├── S7BEN-EASY-002/          Hardcoded Secrets
│   │   ...
│   ├── S7BEN-MED-001/           SQL Injection
│   │   ...
│   ├── S7BEN-HARD-001/          WAF Bypass (ModSecurity)
│   │   ...
│   ├── S7BEN-VHARD-001/         Microservices SSRF Chain
│   │   ...
│   ├── S7BEN-CVE-011/           ActiveMQ RCE (CVE-2023-46604)
│   └── S7BEN-CVE-012/           Ghostscript SSRF→RCE→Cloud Chain
│
├── dashboard/
│   ├── app.py                   Flask REST API
│   ├── strike7_mcp_server.py    MCP SSE server
│   ├── agent_client.py          Python client library
│   ├── config/
│   │   ├── benchmarks.yaml      Benchmark registry (65 entries)
│   │   └── settings.yaml        Platform configuration
│   └── data/
│       └── benchmarks.json      Live benchmark index (takes precedence)
│
├── docs/                        Extended documentation
└── README.md                    This file
```

### Per-Benchmark Structure

```
benchmarks/S7BEN-XXX-NNN/
├── benchmark.yaml          Metadata, flag pattern, difficulty, OWASP mapping
├── docker-compose.yml      Container orchestration + healthchecks
├── Dockerfile              Application image
└── app/                   Vulnerable application source
```

---

## Running Benchmarks Locally

If you want to run the harness on your own machine instead of the VPS:

```bash
# Clone
git clone https://github.com/Azi023/strike7.ai-benchmark-harness
cd strike7.ai-benchmark-harness

# Install dashboard deps
python3 -m venv venv && source venv/bin/activate
pip install -r dashboard/requirements.txt

# Start the dashboard
python3 dashboard/app.py          # REST API at http://localhost:5500

# Start the MCP server (separate terminal)
STRIKE7_API_URL=http://127.0.0.1:5500 \
MCP_PORT=5001 \
python3 dashboard/strike7_mcp_server.py

# Start a benchmark manually
cd benchmarks/S7BEN-EASY-001
docker compose up -d
# Benchmark now at http://localhost:<port>
docker compose down
```

---

## Security Notice

**These environments contain intentional vulnerabilities for research purposes.**

- Run in isolated Docker networks only
- Do not expose benchmark ports to the public internet without authentication
- The VPS benchmarks are intentionally vulnerable — do not store sensitive data there
- For educational and AI evaluation use only

---

## Project Stats (as of Feb 2026)

| Metric | Value |
|--------|-------|
| Total benchmarks | 65 |
| OWASP 2025 coverage | 10 / 10 categories |
| Technologies | Python, Node.js, Java, PHP, Go, PostgreSQL, MongoDB, Redis, LDAP |
| Sprint | 9 (active) |
| Solve rate targets | EASY 100%, MED 90–100%, HARD 60–75%, VHARD 30–50%, CVE 50–70% |

---

## License

MIT License — Copyright (c) 2026 Strike7 AI Benchmarks
